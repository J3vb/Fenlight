//! The Host a server page: start, stop and watch a dedicated server run by the newest
//! installed game, and keep it updated between matches (docs/plans/separate-launcher.md,
//! step 4).

use crate::{Finished, Launcher, Progress};
use launcher_core::feed;
use launcher_core::host::Tick;
use launcher_core::log;
use serde::Serialize;
use std::sync::atomic::Ordering;
use std::time::Duration;
use tauri::{AppHandle, Emitter, Manager, State};

/// How often a hosting launcher looks for a newer release (F-65 step 9).
const UPDATE_CHECK: Duration = Duration::from_secs(15 * 60);

#[derive(Serialize)]
pub struct HostStatus {
    /// Version of the running server, or None.
    running: Option<String>,
    port: u16,
    max_players: u8,
    /// What Start would run.
    installed: Option<String>,
}

#[tauri::command]
pub fn host_status(launcher: State<'_, Launcher>) -> Result<HostStatus, String> {
    host_state(&launcher)
}

/// Takes one lock at a time: `Launcher::installer` locks the host too, and locking it twice
/// on the window's thread froze the launcher on start (v0.1.0).
fn host_state(launcher: &Launcher) -> Result<HostStatus, String> {
    let installed = launcher.installer().installed().into_iter().next();
    let running = launcher.hosting();
    let saved = launcher.settings.lock().map_err(|error| error.to_string())?.clone();
    Ok(HostStatus {
        running,
        port: saved.port,
        max_players: saved.max_players,
        installed,
    })
}

/// Saves the port and player limit, then starts the newest installed game as a server.
#[tauri::command]
pub fn host_start(launcher: State<'_, Launcher>, port: u16, max_players: u8) -> Result<(), String> {
    {
        let mut saved = launcher.settings.lock().map_err(|error| error.to_string())?;
        saved.port = port.max(1);
        saved.max_players = max_players.clamp(1, launcher_core::host::MAX_PLAYERS);
        saved.save(&launcher.data_dir)?;
    }
    let installer = launcher.installer();
    let version = installer
        .installed()
        .into_iter()
        .next()
        .ok_or("Install the game before hosting a server.")?;
    let mut host = launcher.host.lock().map_err(|error| error.to_string())?;
    let result = host.start(&installer.exe_path(&version), &version, port, max_players);
    match &result {
        Ok(()) => log::write(
            &launcher.data_dir,
            "info",
            "server_started",
            &format!("{version} port {port}"),
        ),
        Err(problem) => log::write(&launcher.data_dir, "warn", "server_start_failed", problem),
    }
    result
}

#[tauri::command]
pub fn host_stop(launcher: State<'_, Launcher>) -> Result<(), String> {
    launcher.host.lock().map_err(|error| error.to_string())?.stop();
    log::write(&launcher.data_dir, "info", "server_stop_requested", "");
    Ok(())
}

/// Opens the folder with `server.log` in the file manager.
#[tauri::command]
pub fn open_logs(launcher: State<'_, Launcher>) -> Result<(), String> {
    let dir = launcher.host.lock().map_err(|error| error.to_string())?.dir.clone();
    std::fs::create_dir_all(&dir).map_err(|error| error.to_string())?;
    crate::pages::open(&dir.display().to_string())
}

/// Closes the launcher, stopping a running server first (it gets 10 seconds to save). The
/// wait runs off the window's thread, so the window keeps painting "Stopping the server".
#[tauri::command]
pub fn quit(app: AppHandle) {
    std::thread::spawn(move || {
        stop_server(&app.state::<Launcher>());
        app.exit(0);
    });
}

fn stop_server(launcher: &Launcher) {
    let Ok(mut host) = launcher.host.lock() else {
        return;
    };
    if host.running().is_some() {
        host.stop_and_wait(Duration::from_secs(10));
        log::write(&launcher.data_dir, "info", "server_exited", "launcher closed");
    }
}

/// Runs for the launcher's lifetime: every second it lets the host drain or restart the
/// server (`Host::tick`), and while hosting it installs a newer release every 15 minutes.
pub fn watch(app: AppHandle) {
    let mut since_check = Duration::ZERO;
    loop {
        std::thread::sleep(Duration::from_secs(1));
        let launcher = app.state::<Launcher>();
        let installer = launcher.installer();
        let newest = installer.installed().into_iter().next();
        let exe = newest.as_deref().map(|version| installer.exe_path(version));
        let tick = match launcher.host.lock() {
            Ok(mut host) => host.tick(exe.as_deref().zip(newest.as_deref())),
            Err(_) => return,
        };
        let (event, message) = match &tick {
            Tick::Idle => {
                since_check = Duration::ZERO;
                continue;
            }
            Tick::Running => ("", String::new()),
            Tick::Draining(version) => ("server_draining", version.clone()),
            Tick::Restarted(version) => ("server_update_restarted", version.clone()),
            Tick::Exited(code) => ("server_exited", code.to_string()),
        };
        if !event.is_empty() {
            log::write(&launcher.data_dir, "info", event, &message);
            let _ = app.emit("host_changed", ());
        }
        since_check += Duration::from_secs(1);
        if since_check >= UPDATE_CHECK {
            since_check = Duration::ZERO;
            let app = app.clone();
            std::thread::spawn(move || install_newer(&app));
        }
    }
}

/// Fetches the release list and installs a newer game on the player's channel next to the
/// running server. The next tick then drains the server onto it. Sends the same `progress`
/// and `finished` events as a Play install, so the bottom bar and Cancel follow it.
fn install_newer(app: &AppHandle) {
    let launcher = app.state::<Launcher>();
    let list = match feed::fetch(&launcher.api_url) {
        Ok(list) => list,
        Err(problem) => {
            log::write(&launcher.data_dir, "warn", "check_failed", &problem);
            return;
        }
    };
    if let Ok(mut releases) = launcher.releases.lock() {
        *releases = Some(list);
    }
    let installer = launcher.installer();
    let Some(release) = launcher.newest() else {
        return;
    };
    if !feed::is_newer(&release.version, &installer.installed()) || launcher.busy.swap(true, Ordering::Relaxed) {
        return;
    }
    launcher.cancel.store(false, Ordering::Relaxed);
    let mut last_percent = u64::MAX;
    let mut report = |done: u64, total: u64| {
        let percent = (done * 100).checked_div(total).unwrap_or(0);
        if percent != last_percent {
            last_percent = percent;
            let _ = app.emit("progress", Progress { done, total });
        }
    };
    let finished = match installer.install(&release, &launcher.cancel, &mut report) {
        Ok(_) => {
            log::write(&launcher.data_dir, "info", "installed", &release.version);
            Finished {
                ok: true,
                message: format!("Installed v{} for the server.", release.version),
            }
        }
        Err(message) => {
            log::write(&launcher.data_dir, "warn", "install_failed", &message);
            Finished { ok: false, message }
        }
    };
    launcher.busy.store(false, Ordering::Relaxed);
    let _ = app.emit("finished", finished);
}

#[cfg(test)]
mod tests {
    use super::*;
    use launcher_core::host::{Host, DEFAULT_PORT};
    use launcher_core::settings::Settings;
    use std::sync::atomic::AtomicBool;
    use std::sync::{mpsc, Arc, Mutex};

    fn launcher() -> Launcher {
        let data_dir = std::env::temp_dir().join(format!("fenlight-host-state-{}", std::process::id()));
        Launcher {
            settings: Mutex::new(Settings::default()),
            api_url: String::new(),
            releases: Mutex::new(None),
            cancel: Arc::new(AtomicBool::new(false)),
            busy: AtomicBool::new(false),
            host: Mutex::new(Host::new(data_dir.join("server"))),
            data_dir,
        }
    }

    /// The Host panel asks for this every second from the window's thread: if it hangs, the
    /// whole window goes "Not responding".
    #[test]
    fn host_status_answers_without_hanging() {
        let launcher = launcher();
        let (sender, receiver) = mpsc::channel();
        std::thread::spawn(move || {
            let _ = sender.send(host_state(&launcher).map(|state| (state.running, state.port, state.installed)));
        });
        let answer = receiver
            .recv_timeout(Duration::from_secs(5))
            .expect("host_status hung: it locks a mutex it already holds");
        assert_eq!(answer, Ok((None, DEFAULT_PORT, None)));
    }
}
