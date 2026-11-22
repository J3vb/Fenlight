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
    /// Windows ends the server when the launcher ends, even when it crashes or is killed.
    #[cfg(windows)]
    job: Option<job::KillOnClose>,
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
            #[cfg(windows)]
            job: job::KillOnClose::new(),
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
        #[cfg(windows)]
        if let Some(job) = &self.job {
            job.add(&child);
        }
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

/// A launcher that closes without `quit` (crash, Task Manager, an update restart) must not
/// leave a hidden server holding the port.
impl Drop for Host {
    fn drop(&mut self) {
        if let Some(child) = self.child.as_mut() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
}

#[cfg(windows)]
mod job {
    use std::os::windows::io::AsRawHandle;
    use windows_sys::Win32::Foundation::{CloseHandle, HANDLE};
    use windows_sys::Win32::System::JobObjects::{
        AssignProcessToJobObject, CreateJobObjectW, JobObjectExtendedLimitInformation, SetInformationJobObject,
        JOBOBJECT_EXTENDED_LIMIT_INFORMATION, JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
    };

    /// A Windows job object that ends every process in it when its last handle closes, which
    /// Windows does for the launcher however it ends.
    pub struct KillOnClose(HANDLE);

    // The handle is only used through `&self`/`Drop`, and job handles work from any thread.
    unsafe impl Send for KillOnClose {}

    impl KillOnClose {
        pub fn new() -> Option<Self> {
            // SAFETY: plain Win32 calls; the handle is checked and closed on every path.
            unsafe {
                let handle = CreateJobObjectW(std::ptr::null(), std::ptr::null());
                if handle.is_null() {
                    return None;
                }
                let mut info: JOBOBJECT_EXTENDED_LIMIT_INFORMATION = std::mem::zeroed();
                info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
                let set = SetInformationJobObject(
                    handle,
                    JobObjectExtendedLimitInformation,
                    std::ptr::from_ref(&info).cast(),
                    std::mem::size_of::<JOBOBJECT_EXTENDED_LIMIT_INFORMATION>() as u32,
                );
                if set == 0 {
                    CloseHandle(handle);
                    return None;
                }
                Some(Self(handle))
            }
        }

        pub fn add(&self, child: &std::process::Child) -> bool {
            // SAFETY: both handles are valid while `self` and `child` live.
            unsafe { AssignProcessToJobObject(self.0, child.as_raw_handle() as HANDLE) != 0 }
        }
    }

    impl Drop for KillOnClose {
        fn drop(&mut self) {
            // SAFETY: the handle came from CreateJobObjectW and is closed once.
            unsafe {
                CloseHandle(self.0);
            }
        }
    }

    #[cfg(test)]
    mod tests {
        use super::KillOnClose;
        use std::time::Duration;

        /// The crash case: only the job handle closes (as Windows does for a dead launcher),
        /// nobody calls kill, and the server still ends.
        #[test]
        fn closing_the_job_ends_the_server() {
            let deps = std::env::current_exe().unwrap();
            let exe = deps
                .parent()
                .unwrap()
                .parent()
                .unwrap()
                .join("examples")
                .join("fake_server.exe");
            let dir = std::env::temp_dir().join(format!("eu-launcher-job-{}", std::process::id()));
            std::fs::create_dir_all(&dir).unwrap();
            let mut child = std::process::Command::new(exe)
                .arg(format!("--stop-file={}", dir.join("stop").display()))
                .arg(format!("--drain-file={}", dir.join("drain").display()))
                .spawn()
                .expect("fake server");
            let job = KillOnClose::new().expect("job object");
            assert!(job.add(&child));
            std::thread::sleep(Duration::from_millis(200));
            assert!(matches!(child.try_wait(), Ok(None)), "running before the job closes");
            drop(job);
            std::thread::sleep(Duration::from_millis(500));
            assert!(
                matches!(child.try_wait(), Ok(Some(_))),
                "the job did not end the server"
            );
        }
    }
}
