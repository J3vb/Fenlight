//! The News, Patches, Settings and Support pages and the Installation panel
//! (docs/plans/separate-launcher.md, step 5).

use crate::Launcher;
use launcher_core::feed::{self, Patch};
use launcher_core::install;
use launcher_core::log;
use launcher_core::news::{self, NewsItem};
use launcher_core::settings;
use serde::Serialize;
use std::path::Path;
use std::sync::atomic::Ordering;
use tauri::{AppHandle, Manager, State};
use tauri_plugin_dialog::DialogExt;

const ISSUES_URL: &str = "https://github.com/J3vb/Fenlight/issues";

#[derive(Serialize)]
pub struct Disk {
    installed: u64,
    free: u64,
}

/// News from the repo, or the built-in copy when offline. Pictures come from `ui/news/`.
#[tauri::command]
pub async fn news(app: AppHandle) -> Vec<NewsItem> {
    let fetched = tauri::async_runtime::spawn_blocking(|| news::fetch(news::NEWS_URL))
        .await
        .unwrap_or_else(|error| Err(error.to_string()));
    news::pick(fetched, |name| {
        app.asset_resolver().get(format!("news/{name}")).is_some()
    })
}

#[tauri::command]
pub fn patches(launcher: State<'_, Launcher>) -> Result<Vec<Patch>, String> {
    let channel = launcher.settings.lock().map_err(|error| error.to_string())?.channel;
    let releases = launcher.releases.lock().map_err(|error| error.to_string())?;
    Ok(releases
        .as_deref()
        .map(|list| feed::patches(list, channel))
        .unwrap_or_default())
}

#[tauri::command]
pub fn disk(launcher: State<'_, Launcher>) -> Disk {
    let installer = launcher.installer();
    Disk {
        installed: installer.size(),
        free: installer.free_space(),
    }
}

/// The Install dialog: where the game goes, the free space there and the space it needs.
#[derive(Serialize)]
pub struct InstallPlace {
    dir: String,
    free: u64,
    need: u64,
}

#[tauri::command]
pub fn install_place(launcher: State<'_, Launcher>) -> InstallPlace {
    let installer = launcher.installer();
    InstallPlace {
        dir: launcher.game_dir().display().to_string(),
        free: installer.free_space(),
        need: launcher
            .newest()
            .map(|release| install::space_needed(release.size))
            .unwrap_or(0),
    }
}

/// Browse in the Install dialog: the system folder picker, then the game goes into a
/// `Fenlight` folder inside the pick. Only before the first install, so installed versions
/// are never left behind in the old folder. The window never passes a path.
#[tauri::command]
pub async fn browse_install(app: AppHandle) -> Result<InstallPlace, String> {
    let start = {
        let launcher = app.state::<Launcher>();
        if !launcher.installer().installed().is_empty() || launcher.busy.load(Ordering::Relaxed) {
            return Err("Uninstall the game first to install it somewhere else.".into());
        }
        launcher.game_dir()
    };
    let start = start.ancestors().find(|dir| dir.is_dir()).map(Path::to_path_buf);
    let picker = app.clone();
    let picked = tauri::async_runtime::spawn_blocking(move || {
        let dialog = picker.dialog().file().set_title("Install Fenlight in");
        match start {
            Some(dir) => dialog.set_directory(dir),
            None => dialog,
        }
        .blocking_pick_folder()
    })
    .await
    .map_err(|error| error.to_string())?;
    let launcher = app.state::<Launcher>();
    if let Some(picked) = picked {
        let picked = picked.into_path().map_err(|error| error.to_string())?;
        let mut saved = launcher.settings.lock().map_err(|error| error.to_string())?;
        saved.install_dir = Some(settings::install_folder(&picked));
        saved.save(&launcher.data_dir)?;
        log::write(
            &launcher.data_dir,
            "info",
            "install_dir_picked",
            &picked.display().to_string(),
        );
    }
    Ok(install_place(launcher))
}

#[tauri::command]
pub fn uninstall(launcher: State<'_, Launcher>) -> Result<(), String> {
    idle_installer(&launcher)?.remove_all()?;
    log::write(&launcher.data_dir, "info", "uninstalled", "");
    Ok(())
}

fn idle_installer(launcher: &Launcher) -> Result<launcher_core::install::Installer, String> {
    if launcher.busy.load(Ordering::Relaxed) {
        return Err("Wait for the download to finish.".into());
    }
    if launcher.hosting().is_some() {
        return Err("Stop your server first.".into());
    }
    Ok(launcher.installer())
}

#[tauri::command]
pub fn set_close_on_play(launcher: State<'_, Launcher>, close: bool) -> Result<(), String> {
    let mut saved = launcher.settings.lock().map_err(|error| error.to_string())?;
    saved.close_on_play = close;
    saved.save(&launcher.data_dir)
}

/// Opens one of the launcher's fixed places: the game folder, the logs folder or the
/// GitHub issues page. The window never passes a path or address of its own.
#[tauri::command]
pub fn open_place(launcher: State<'_, Launcher>, place: String) -> Result<(), String> {
    let target = match place.as_str() {
        "game" => launcher.game_dir(),
        "logs" => launcher.data_dir.clone(),
        "issues" => return open(ISSUES_URL),
        _ => return Err(format!("Unknown place {place}.")),
    };
    std::fs::create_dir_all(&target).map_err(|error| error.to_string())?;
    open(&target.display().to_string())
}

/// Opens a folder or web address with the system's default program.
pub fn open(target: &str) -> Result<(), String> {
    let opener = if cfg!(windows) {
        "explorer"
    } else if cfg!(target_os = "macos") {
        "open"
    } else {
        "xdg-open"
    };
    std::process::Command::new(opener)
        .arg(target)
        .spawn()
        .map(|_| ())
        .map_err(|error| format!("Could not open {}: {error}", Path::new(target).display()))
}
