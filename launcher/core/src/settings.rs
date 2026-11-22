//! Where the launcher keeps the game and its own settings, and the command-line test hooks.

use crate::feed::{Channel, API_URL};
use crate::host;
use crate::log;
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};

const SETTINGS_FILE: &str = "launcher.json";
const GAME_FOLDER: &str = "Fenlight";

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(default)]
pub struct Settings {
    pub channel: Channel,
    /// Host a server: UDP port and player limit.
    pub port: u16,
    pub max_players: u8,
    /// Close the launcher when the game starts (it stays open while hosting a server).
    pub close_on_play: bool,
    /// Folder the player picked for the game; `None` means `<data folder>/game`.
    pub install_dir: Option<PathBuf>,
}

impl Default for Settings {
    fn default() -> Self {
        Self {
            channel: Channel::Stable,
            port: host::DEFAULT_PORT,
            max_players: host::MAX_PLAYERS,
            close_on_play: true,
            install_dir: None,
        }
    }
}

impl Settings {
    /// Saved settings, or the defaults when the file is missing or broken (logged).
    pub fn load(data_dir: &Path) -> Self {
        let Ok(text) = std::fs::read_to_string(data_dir.join(SETTINGS_FILE)) else {
            return Self::default();
        };
        serde_json::from_str(&text).unwrap_or_else(|error| {
            log::write(data_dir, "warn", "settings_reset", &error.to_string());
            Self::default()
        })
    }

    /// The game folder: the picked one, else `<data folder>/game` (where installs from before
    /// the folder picker live).
    pub fn game_dir(&self, data_dir: &Path) -> PathBuf {
        self.install_dir.clone().unwrap_or_else(|| data_dir.join("game"))
    }

    pub fn save(&self, data_dir: &Path) -> Result<(), String> {
        std::fs::create_dir_all(data_dir).map_err(|error| error.to_string())?;
        let text = serde_json::to_string_pretty(self).map_err(|error| error.to_string())?;
        // Written next to the file, then swapped in: a crash mid-save keeps the old settings.
        let temp = data_dir.join(format!("{SETTINGS_FILE}.tmp"));
        std::fs::write(&temp, text).map_err(|error| error.to_string())?;
        std::fs::rename(&temp, data_dir.join(SETTINGS_FILE)).map_err(|error| error.to_string())
    }
}

/// `--name=value` from the command line.
pub fn arg_value(args: &[String], name: &str) -> Option<String> {
    let prefix = format!("--{name}=");
    args.iter()
        .find_map(|arg| arg.strip_prefix(&prefix).map(str::to_string))
}

/// The launcher's data folder: `--game-dir=` (tests), else `Experiment Undead` inside the
/// launcher's local app data folder (`%LOCALAPPDATA%\com.experimentundead.launcher`).
/// The folder keeps the game's old name so installs from before the rename to Fenlight carry over.
pub fn data_dir(args: &[String], local_data: PathBuf) -> PathBuf {
    arg_value(args, "game-dir")
        .map(PathBuf::from)
        .unwrap_or_else(|| local_data.join("Experiment Undead"))
}

pub fn versions_dir(game_dir: &Path) -> PathBuf {
    game_dir.join("versions")
}

/// The game folder for a folder the player picked: its own `Fenlight` folder inside it, so
/// picking a drive like `D:\` never fills the drive's top folder.
pub fn install_folder(picked: &Path) -> PathBuf {
    let named = picked
        .file_name()
        .is_some_and(|name| name.to_string_lossy().eq_ignore_ascii_case(GAME_FOLDER));
    if named {
        picked.to_path_buf()
    } else {
        picked.join(GAME_FOLDER)
    }
}

/// The releases API: `--releases-api=` (tests), else GitHub.
pub fn releases_api(args: &[String]) -> String {
    arg_value(args, "releases-api").unwrap_or_else(|| API_URL.to_string())
}
