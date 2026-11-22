//! Fenlight launcher: installs the newest game on the player's channel, keeps it
//! updated and starts it (docs/plans/separate-launcher.md). The window is `ui/`.

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod host;
mod pages;

use launcher_core::feed::{self, Channel, Release};
use launcher_core::host::Host;
use launcher_core::install::Installer;
use launcher_core::log;
use launcher_core::settings::{self, Settings};
use serde::Serialize;
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Arc, Mutex};
use tauri::{AppHandle, Emitter, Manager, State, WindowEvent};
use tauri_plugin_updater::UpdaterExt;

struct Launcher {
    data_dir: PathBuf,
    api_url: String,
    settings: Mutex<Settings>,
    releases: Mutex<Option<Vec<serde_json::Value>>>,
    cancel: Arc<AtomicBool>,
    busy: AtomicBool,
    host: Mutex<Host>,
}

impl Launcher {
    /// The installer, told which version a hosted server runs so it is never deleted.
    fn installer(&self) -> Installer {
        let mut installer = Installer::new(settings::versions_dir(&self.game_dir()));
        if let Some(version) = self.hosting() {
            installer.in_use.push(version);
        }
        installer
    }

    /// The game folder. Locks the settings only for this line, so callers never hold it.
    fn game_dir(&self) -> PathBuf {
        let saved = self.settings.lock().map(|saved| saved.clone()).unwrap_or_default();
        saved.game_dir(&self.data_dir)
    }

    fn hosting(&self) -> Option<String> {
        self.host.lock().ok()?.running()
    }

    fn newest(&self) -> Option<Release> {
        let channel = self.settings.lock().ok()?.channel;
        let releases = self.releases.lock().ok()?;
        feed::newest(releases.as_deref()?, channel, feed::platform_suffix())
    }
}

#[derive(Serialize)]
struct Status {
    version: String,
    channel: Channel,
    online: bool,
    installed: Vec<String>,
    newest: Option<Release>,
    /// Newest version on each channel, for the Game version dropdown.
    stable: Option<String>,
    test: Option<String>,
    update_ready: bool,
    /// A newer version installs on its own: only once the game is installed.
    auto_update: bool,
    close_on_play: bool,
    hosting: bool,
    busy: bool,
    game_dir: String,
}

#[derive(Clone, Serialize)]
struct Progress {
    done: u64,
    total: u64,
}

#[derive(Clone, Serialize)]
struct Finished {
    ok: bool,
    message: String,
}

#[tauri::command]
fn status(launcher: State<'_, Launcher>) -> Status {
    let installed = launcher.installer().installed();
    let newest = launcher.newest();
    let update_ready = newest
        .as_ref()
        .is_some_and(|release| feed::is_newer(&release.version, &installed));
    let auto_update = newest
        .as_ref()
        .is_some_and(|release| feed::auto_update(&release.version, &installed));
    let saved = launcher.settings.lock().map(|saved| saved.clone()).unwrap_or_default();
    let on_channel = |channel: Channel| {
        let releases = launcher.releases.lock().ok()?;
        feed::newest(releases.as_deref()?, channel, feed::platform_suffix()).map(|release| release.version)
    };
    Status {
        version: env!("CARGO_PKG_VERSION").to_string(),
        channel: saved.channel,
        online: launcher.releases.lock().map(|list| list.is_some()).unwrap_or(false),
        installed,
        newest,
        stable: on_channel(Channel::Stable),
        test: on_channel(Channel::Test),
        auto_update,
        update_ready,
        close_on_play: saved.close_on_play,
        hosting: launcher.hosting().is_some(),
        busy: launcher.busy.load(Ordering::Relaxed),
        game_dir: launcher.game_dir().display().to_string(),
    }
}

/// Asks GitHub for the releases list. Offline keeps the last list (none at start).
#[tauri::command]
async fn refresh(launcher: State<'_, Launcher>) -> Result<(), String> {
    let api_url = launcher.api_url.clone();
    let fetched = tauri::async_runtime::spawn_blocking(move || feed::fetch(&api_url))
        .await
        .map_err(|error| error.to_string())?;
    match fetched {
        Ok(list) => {
            *launcher.releases.lock().map_err(|error| error.to_string())? = Some(list);
            Ok(())
        }
        Err(problem) => {
            log::write(&launcher.data_dir, "warn", "check_failed", &problem);
            Err(problem)
        }
    }
}

#[tauri::command]
fn set_channel(launcher: State<'_, Launcher>, channel: Channel) -> Result<(), String> {
    let mut saved = launcher.settings.lock().map_err(|error| error.to_string())?;
    saved.channel = channel;
    saved.save(&launcher.data_dir)
}

/// Installs the newest release on the channel in the background: `progress` events while
/// downloading, then one `finished` event.
#[tauri::command]
fn install(app: AppHandle, launcher: State<'_, Launcher>) -> Result<(), String> {
    let release = launcher.newest().ok_or("No release to install.")?;
    start_download(app, &launcher, release, false)
}

/// Repair game files: checks the newest installed version against its release zip and
/// replaces only the files that are missing or damaged. Same events as `install`.
#[tauri::command]
fn repair(app: AppHandle, launcher: State<'_, Launcher>) -> Result<(), String> {
    if launcher.hosting().is_some() {
        return Err("Stop your server first.".into());
    }
    let version = launcher
        .installer()
        .installed()
        .into_iter()
        .next()
        .ok_or("The game is not installed.")?;
    let release = {
        let releases = launcher.releases.lock().map_err(|error| error.to_string())?;
        let list = releases
            .as_deref()
            .ok_or("Connect to the internet to repair the game.")?;
        feed::find(list, &version, feed::platform_suffix())
    }
    .ok_or(format!(
        "v{version} can no longer be downloaded, so it cannot be repaired."
    ))?;
    start_download(app, &launcher, release, true)
}

fn start_download(app: AppHandle, launcher: &Launcher, release: Release, repair: bool) -> Result<(), String> {
    if launcher.busy.swap(true, Ordering::Relaxed) {
        return Err("Wait for the download to finish.".into());
    }
    launcher.cancel.store(false, Ordering::Relaxed);
    let installer = launcher.installer();
    let cancel = launcher.cancel.clone();
    let data_dir = launcher.data_dir.clone();
    std::thread::spawn(move || {
        let mut last_percent = u64::MAX;
        let mut report = |done: u64, total: u64| {
            let percent = (done * 100).checked_div(total).unwrap_or(0);
            if percent != last_percent {
                last_percent = percent;
                let _ = app.emit("progress", Progress { done, total });
            }
        };
        let version = &release.version;
        let result = if repair {
            installer
                .repair(&release, &cancel, &mut report)
                .map(|replaced| match replaced {
                    0 => format!("All game files of v{version} are fine."),
                    1 => format!("Repaired v{version}: replaced 1 file."),
                    count => format!("Repaired v{version}: replaced {count} files."),
                })
        } else {
            installer
                .install(&release, &cancel, &mut report)
                .map(|_| format!("Installed v{version}."))
        };
        let (event, failed) = if repair {
            ("repaired", "repair_failed")
        } else {
            ("installed", "install_failed")
        };
        let finished = match result {
            Ok(message) => {
                log::write(&data_dir, "info", event, &message);
                Finished { ok: true, message }
            }
            Err(message) => {
                log::write(&data_dir, "warn", failed, &message);
                Finished { ok: false, message }
            }
        };
        app.state::<Launcher>().busy.store(false, Ordering::Relaxed);
        let _ = app.emit("finished", finished);
    });
    Ok(())
}

#[tauri::command]
fn cancel(launcher: State<'_, Launcher>) {
    launcher.cancel.store(true, Ordering::Relaxed);
}

/// Updates the launcher itself when the newest release on the channel has a newer one: the
/// signed setup exe installs quietly and the launcher restarts. Ok(false) means up to date,
/// or a hosted server is running (a restart would leave it without its launcher).
#[tauri::command]
async fn self_update(app: AppHandle, launcher: State<'_, Launcher>) -> Result<bool, String> {
    if launcher.hosting().is_some() {
        return Ok(false);
    }
    let url = {
        let channel = launcher.settings.lock().map_err(|error| error.to_string())?.channel;
        let releases = launcher.releases.lock().map_err(|error| error.to_string())?;
        releases
            .as_deref()
            .and_then(|list| feed::launcher_manifest_url(list, channel))
    };
    let Some(url) = url else {
        return Ok(false);
    };
    let result = check_and_install(&app, &url).await;
    match &result {
        Ok(true) => log::write(&launcher.data_dir, "info", "self_updated", &url),
        Ok(false) => {}
        Err(problem) => log::write(&launcher.data_dir, "warn", "self_update_failed", problem),
    }
    if result == Ok(true) {
        app.restart();
    }
    result
}

async fn check_and_install(app: &AppHandle, manifest: &str) -> Result<bool, String> {
    let endpoint = manifest.parse().map_err(|error: url::ParseError| error.to_string())?;
    let updater = app
        .updater_builder()
        .endpoints(vec![endpoint])
        .map_err(|error| error.to_string())?
        .build()
        .map_err(|error| error.to_string())?;
    let Some(update) = updater.check().await.map_err(|error| error.to_string())? else {
        return Ok(false);
    };
    update
        .download_and_install(|_, _| {}, || {})
        .await
        .map_err(|error| error.to_string())?;
    Ok(true)
}

/// Starts the newest installed game and closes the launcher when the player wants that and
/// it hosts no server.
#[tauri::command]
fn play(app: AppHandle, launcher: State<'_, Launcher>) -> Result<(), String> {
    let installer = launcher.installer();
    let version = installer
        .installed()
        .into_iter()
        .next()
        .ok_or("The game is not installed yet.")?;
    let exe = installer.exe_path(&version);
    let me = std::env::current_exe().map_err(|error| error.to_string())?;
    std::process::Command::new(&exe)
        .current_dir(exe.parent().unwrap_or(&launcher.data_dir))
        .arg("--from-launcher")
        .arg(format!("--launcher-exe={}", me.display()))
        .spawn()
        .map_err(|error| format!("Could not start the game: {error}"))?;
    let close = launcher
        .settings
        .lock()
        .map(|saved| saved.close_on_play)
        .unwrap_or(true);
    if close && launcher.hosting().is_none() {
        app.exit(0);
    }
    Ok(())
}

/// The window has one fixed size; on a smaller screen (or high display scaling) it shrinks
/// once to fit, so Play is never under the taskbar.
fn fit_to_screen(window: &tauri::WebviewWindow) {
    let (Ok(Some(monitor)), Ok(size)) = (window.current_monitor(), window.outer_size()) else {
        return;
    };
    let area = monitor.work_area().size;
    if size.width > area.width || size.height > area.height {
        let fitted = tauri::PhysicalSize::new(size.width.min(area.width), size.height.min(area.height));
        let _ = window.set_size(fitted);
        let _ = window.center();
    }
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    tauri::Builder::default()
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_dialog::init())
        .setup(move |app| {
            let app_data = app.path().app_local_data_dir()?;
            let data_dir = settings::data_dir(&args, app_data);
            app.manage(Launcher {
                settings: Mutex::new(Settings::load(&data_dir)),
                api_url: settings::releases_api(&args),
                data_dir: data_dir.clone(),
                releases: Mutex::new(None),
                cancel: Arc::new(AtomicBool::new(false)),
                busy: AtomicBool::new(false),
                host: Mutex::new(Host::new(data_dir.join("server"))),
            });
            if let Some(window) = app.get_webview_window("main") {
                fit_to_screen(&window);
            }
            let handle = app.handle().clone();
            std::thread::spawn(move || host::watch(handle));
            Ok(())
        })
        .on_window_event(|window, event| {
            // Closing while hosting asks first (ui/host.js), then `quit` stops the server.
            if let WindowEvent::CloseRequested { api, .. } = event {
                if window.state::<Launcher>().hosting().is_some() {
                    api.prevent_close();
                    let _ = window.emit("close_requested", ());
                }
            }
        })
        .invoke_handler(tauri::generate_handler![
            status,
            refresh,
            self_update,
            set_channel,
            install,
            repair,
            cancel,
            play,
            host::host_status,
            host::host_start,
            host::host_stop,
            host::open_logs,
            host::quit,
            pages::news,
            pages::patches,
            pages::disk,
            pages::install_place,
            pages::browse_install,
            pages::uninstall,
            pages::set_close_on_play,
            pages::open_place
        ])
        .run(tauri::generate_context!())
        .expect("the launcher window could not start");
}
