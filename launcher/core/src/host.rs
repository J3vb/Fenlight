//! Host a server: runs an installed game build as a headless dedicated server, stops it
//! through its stop file and moves it to a newer installed version between matches through
//! its drain file and exit code 3 (docs/RELEASING.md).

use crate::version;
use std::cmp::Ordering;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::time::{Duration, Instant};

/// Same as `Net.DEFAULT_PORT` and `Net.MAX_PLAYERS` in the game.
pub const DEFAULT_PORT: u16 = 7777;
pub const MAX_PLAYERS: u8 = 8;
pub const LOG_FILE: &str = "server.log";
/// The game quits with this after draining: restart it on the newer version.
pub const EXIT_UPDATE: i32 = 3;
const STOP_FILE: &str = "server.stop";
const DRAIN_FILE: &str = "server.drain";

/// The game's command line for a headless server on `port` for at most `max_players`
/// (clamped to 1-8), quitting when `stop_file` appears and draining when `drain_file` does.
pub fn server_args(port: u16, max_players: u8, stop_file: &Path, drain_file: &Path) -> Vec<String> {
    vec![
        "--headless".into(),
        "--".into(),
        "--server".into(),
        format!("--port={}", port.max(1)),
        format!("--max-players={}", max_players.clamp(1, MAX_PLAYERS)),
        format!("--stop-file={}", stop_file.display()),
        format!("--drain-file={}", drain_file.display()),
    ]
}

/// What one `Host::tick` saw.
#[derive(Debug, PartialEq)]
pub enum Tick {
    Idle,
    Running,
    /// A newer version is installed; the drain file asks the server to finish its match.
    Draining(String),
    /// The server drained and was started again on this version.
    Restarted(String),
    /// The server quit with this code and was not restarted (stopped, crashed, or a
    /// restart failed).
    Exited(i32),
}

pub struct Host {
    /// Holds the stop and drain files and the server log.
    pub dir: PathBuf,
    child: Option<Child>,
    version: String,
    port: u16,
    max_players: u8,
    draining: bool,
    exit: Option<i32>,
}

impl Host {
    pub fn new(dir: PathBuf) -> Self {
        Self {
            dir,
            child: None,
            version: String::new(),
            port: DEFAULT_PORT,
            max_players: MAX_PLAYERS,
            draining: false,
            exit: None,
        }
    }

    pub fn drain_file(&self) -> PathBuf {
        self.dir.join(DRAIN_FILE)
    }

    pub fn stop_file(&self) -> PathBuf {
        self.dir.join(STOP_FILE)
    }

    /// Starts `exe` (the game of `version`) as a server, its output added to `server.log`
    /// so the log of the run before an update restart is kept.
    pub fn start(&mut self, exe: &Path, version: &str, port: u16, max_players: u8) -> Result<(), String> {
        if self.running().is_some() {
            return Err("A server is already running.".into());
        }
        fs::create_dir_all(&self.dir).map_err(|error| error.to_string())?;
        let _ = fs::remove_file(self.stop_file());
        let _ = fs::remove_file(self.drain_file());
        let mut log = OpenOptions::new()
            .create(true)
            .append(true)
            .open(self.dir.join(LOG_FILE))
            .map_err(|error| error.to_string())?;
        let _ = writeln!(log, "--- Server v{version} on port {port} ---");
        let mut command = Command::new(exe);
        command
            .args(server_args(port, max_players, &self.stop_file(), &self.drain_file()))
            .current_dir(exe.parent().unwrap_or(&self.dir))
            .stdin(Stdio::null())
            .stdout(log.try_clone().map_err(|error| error.to_string())?)
            .stderr(log);
        #[cfg(windows)]
        {
            use std::os::windows::process::CommandExt;
            const CREATE_NO_WINDOW: u32 = 0x0800_0000;
            command.creation_flags(CREATE_NO_WINDOW);
        }
        let child = command
            .spawn()
            .map_err(|error| format!("Could not start the server: {error}"))?;
        self.child = Some(child);
        self.version = version.to_string();
        self.port = port;
        self.max_players = max_players;
        self.draining = false;
        self.exit = None;
        Ok(())
    }

    /// The running server's version, or None once it has exited. Keeps the exit code for
    /// `poll`.
    pub fn running(&mut self) -> Option<String> {
        self.reap();
        self.child.as_ref().map(|_| self.version.clone())
    }

    /// Exit code of a server that has exited since the last call (-1 when it was killed or
    /// crashed hard). None while it runs or when none was started.
    pub fn poll(&mut self) -> Option<i32> {
        self.reap();
        self.exit.take()
    }

    fn reap(&mut self) {
        let Some(child) = self.child.as_mut() else {
            return;
        };
        if let Ok(Some(status)) = child.try_wait() {
            self.child = None;
            self.version.clear();
            self.exit = Some(status.code().unwrap_or(-1));
        }
    }

    /// Asks the server to quit through its stop file.
    pub fn stop(&self) {
        if self.child.is_some() {
            let _ = fs::write(self.stop_file(), "stop");
        }
    }

    /// Stops the server and waits up to `timeout` for it, then kills it.
    pub fn stop_and_wait(&mut self, timeout: Duration) {
        self.stop();
        let start = Instant::now();
        while self.running().is_some() && start.elapsed() < timeout {
            std::thread::sleep(Duration::from_millis(100));
        }
        if let Some(mut child) = self.child.take() {
            let _ = child.kill();
            let _ = child.wait();
            self.version.clear();
        }
    }
}

impl Host {
    /// Called every second with the newest installed game. A running server older than it
    /// gets the drain file once (tried again next tick if it could not be written); a server
    /// that then quits with `EXIT_UPDATE` starts again on it with the same port and player
    /// limit. Any other exit is left alone.
    pub fn tick(&mut self, newest: Option<(&Path, &str)>) -> Tick {
        if let Some(code) = self.poll() {
            return match newest {
                Some((exe, version)) if code == EXIT_UPDATE => {
                    match self.start(exe, version, self.port, self.max_players) {
                        Ok(()) => Tick::Restarted(version.to_string()),
                        Err(_) => Tick::Exited(code),
                    }
                }
                _ => Tick::Exited(code),
            };
        }
        if self.child.is_none() {
            return Tick::Idle;
        }
        match newest {
            Some((_, version)) if !self.draining && version::compare(version, &self.version) == Ordering::Greater => {
                if fs::write(self.drain_file(), version).is_err() {
                    return Tick::Running;
                }
                self.draining = true;
                Tick::Draining(version.to_string())
            }
            _ => Tick::Running,
        }
    }
}
