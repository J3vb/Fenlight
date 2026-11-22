use launcher_core::feed::{Channel, API_URL};
use launcher_core::settings::{data_dir, install_folder, releases_api, versions_dir, Settings};
use std::path::PathBuf;

mod common;

fn args(list: &[&str]) -> Vec<String> {
    list.iter().map(|arg| arg.to_string()).collect()
}

#[test]
fn channel_is_saved_and_loaded() {
    let dir = common::temp_dir("settings");
    assert_eq!(Settings::load(&dir).channel, Channel::Stable);
    Settings {
        channel: Channel::Test,
        port: 7790,
        max_players: 4,
        close_on_play: false,
        install_dir: Some(PathBuf::from("/games/Fenlight")),
    }
    .save(&dir)
    .unwrap();
    let loaded = Settings::load(&dir);
    assert_eq!(loaded.channel, Channel::Test);
    assert_eq!((loaded.port, loaded.max_players), (7790, 4));
    assert!(!loaded.close_on_play);
    assert_eq!(loaded.game_dir(&dir), PathBuf::from("/games/Fenlight"));
}

#[test]
fn old_settings_files_get_the_default_server_port() {
    let dir = common::temp_dir("settings-old");
    std::fs::write(dir.join("launcher.json"), r#"{"channel":"test"}"#).unwrap();
    let loaded = Settings::load(&dir);
    assert_eq!(loaded.channel, Channel::Test);
    assert_eq!((loaded.port, loaded.max_players), (7777, 8));
    assert!(loaded.close_on_play);
    assert_eq!(loaded.install_dir, None);
    assert_eq!(
        loaded.game_dir(&dir),
        dir.join("game"),
        "old installs stay where they are"
    );
}

#[test]
fn a_picked_folder_gets_its_own_fenlight_folder() {
    assert_eq!(
        install_folder(&PathBuf::from("/mnt/d")),
        PathBuf::from("/mnt/d/Fenlight")
    );
    assert_eq!(
        install_folder(&PathBuf::from("/games/Fenlight")),
        PathBuf::from("/games/Fenlight")
    );
    assert_eq!(
        install_folder(&PathBuf::from("/games/fenlight")),
        PathBuf::from("/games/fenlight")
    );
}

#[test]
fn broken_settings_fall_back_to_stable() {
    let dir = common::temp_dir("settings-broken");
    std::fs::write(dir.join("launcher.json"), "{not json").unwrap();
    assert_eq!(Settings::load(&dir).channel, Channel::Stable);
}

#[test]
fn command_line_test_hooks() {
    let local = PathBuf::from("/local");
    assert_eq!(
        data_dir(&args(&["launcher"]), local.clone()),
        local.join("Experiment Undead")
    );
    assert_eq!(
        data_dir(&args(&["launcher", "--game-dir=/tmp/x"]), local),
        PathBuf::from("/tmp/x")
    );
    assert_eq!(
        versions_dir(&PathBuf::from("/d/game")),
        PathBuf::from("/d/game/versions")
    );
    assert_eq!(releases_api(&args(&[])), API_URL);
    assert_eq!(API_URL, "https://api.github.com/repos/J3vb/Fenlight/releases");
    assert_eq!(
        releases_api(&args(&["--releases-api=http://127.0.0.1:9/r"])),
        "http://127.0.0.1:9/r"
    );
}

#[test]
fn saving_leaves_no_temp_file_and_a_reset_is_logged() {
    let dir = common::temp_dir("settings-save");
    Settings::default().save(&dir).unwrap();
    assert!(dir.join("launcher.json").is_file());
    assert!(!dir.join("launcher.json.tmp").exists());
    std::fs::write(dir.join("launcher.json"), r#"{"channel": "dev"}"#).unwrap();
    let _ = Settings::load(&dir);
    let log = std::fs::read_to_string(dir.join("launcher.log")).unwrap_or_default();
    assert!(log.contains("settings_reset"), "{log}");
}
