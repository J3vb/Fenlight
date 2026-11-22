use launcher_core::feed::Release;
use launcher_core::install::{game_exe_name, sha256_file, space_needed, Installer, KEEP};
use std::sync::atomic::AtomicBool;

mod common;

fn release(url: String, digest: String, version: &str) -> Release {
    Release {
        version: version.into(),
        notes: String::new(),
        url,
        digest,
        size: 0,
        page: String::new(),
    }
}

fn digest_of(bytes: &[u8], dir: &std::path::Path) -> String {
    let path = dir.join("digest.bin");
    std::fs::write(&path, bytes).unwrap();
    let digest = sha256_file(&path).unwrap();
    std::fs::remove_file(path).unwrap();
    digest
}

#[test]
fn good_zip_lands_in_its_version_folder() {
    let dir = common::temp_dir("good");
    let zip = common::game_zip(game_exe_name());
    let digest = digest_of(&zip, &dir);
    let installer = Installer::new(dir.join("versions"));
    let mut calls = 0;
    let folder = installer
        .install(
            &release(common::serve(zip, None), digest, "0.1.1"),
            &AtomicBool::new(false),
            &mut |_, _| calls += 1,
        )
        .expect("installed");
    assert!(folder.join(game_exe_name()).is_file());
    assert!(folder.join("ExperimentUndead.pck").is_file());
    assert_eq!(installer.installed(), vec!["0.1.1".to_string()]);
    assert!(calls > 0);
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let mode = std::fs::metadata(folder.join(game_exe_name()))
            .unwrap()
            .permissions()
            .mode();
        assert_eq!(mode & 0o111, 0o111);
    }
}

#[test]
fn wrong_digest_leaves_nothing_behind() {
    let dir = common::temp_dir("digest");
    let installer = Installer::new(dir.join("versions"));
    let zip = common::game_zip(game_exe_name());
    let result = installer.install(
        &release(common::serve(zip, None), "00".into(), "0.1.1"),
        &AtomicBool::new(false),
        &mut |_, _| {},
    );
    assert!(result.is_err());
    assert!(installer.installed().is_empty());
    assert!(!dir.join("versions/0.1.1.tmp").exists());
}

#[test]
fn cut_off_download_leaves_nothing_behind() {
    let dir = common::temp_dir("cut");
    let zip = common::game_zip(game_exe_name());
    let digest = digest_of(&zip, &dir);
    let installer = Installer::new(dir.join("versions"));
    let cut = zip.len() / 2;
    let result = installer.install(
        &release(common::serve(zip, Some(cut)), digest, "0.1.1"),
        &AtomicBool::new(false),
        &mut |_, _| {},
    );
    assert!(result.is_err());
    assert!(installer.installed().is_empty());
}

#[test]
fn cancel_stops_the_download() {
    let dir = common::temp_dir("cancel");
    let zip = common::game_zip(game_exe_name());
    let installer = Installer::new(dir.join("versions"));
    let result = installer.install(
        &release(common::serve(zip, None), "x".into(), "0.1.1"),
        &AtomicBool::new(true),
        &mut |_, _| {},
    );
    assert_eq!(result.unwrap_err(), "Download cancelled.");
}

#[test]
fn only_the_newest_folders_stay() {
    let dir = common::temp_dir("prune");
    let versions = dir.join("versions");
    for name in ["0.1.0", "0.1.1", "0.2.0-test.1", "0.1.2.tmp", "notes"] {
        std::fs::create_dir_all(versions.join(name)).unwrap();
    }
    let installer = Installer::new(versions.clone());
    installer.prune(&["0.1.0".to_string()]);
    assert_eq!(
        installer.installed(),
        vec!["0.2.0-test.1".to_string(), "0.1.1".to_string(), "0.1.0".to_string()]
    );
    installer.prune(&[]);
    assert_eq!(installer.installed().len(), KEEP);
    assert!(versions.join("notes").exists());
}

#[test]
fn installing_keeps_the_version_a_server_runs() {
    let dir = common::temp_dir("in-use");
    let mut installer = Installer::new(dir.join("versions"));
    for version in ["0.1.0", "0.1.1"] {
        std::fs::create_dir_all(installer.versions_dir.join(version)).unwrap();
    }
    installer.in_use = vec!["0.1.0".to_string()];
    let zip_path = dir.join("game.zip");
    std::fs::write(&zip_path, common::game_zip(game_exe_name())).unwrap();
    let digest = sha256_file(&zip_path).unwrap();
    installer.install_zip(&zip_path, &digest, "0.1.2").expect("installed");
    assert_eq!(installer.installed(), vec!["0.1.2", "0.1.1", "0.1.0"]);
}

#[test]
fn size_counts_every_version_and_free_space_is_known() {
    let dir = common::temp_dir("size");
    let installer = Installer::new(dir.join("versions"));
    assert_eq!(installer.size(), 0);
    assert!(
        installer.free_space() > 0,
        "free space comes from the nearest existing folder"
    );
    std::fs::create_dir_all(dir.join("versions/0.1.0/data")).unwrap();
    std::fs::write(dir.join("versions/0.1.0").join(game_exe_name()), [0u8; 300]).unwrap();
    std::fs::write(dir.join("versions/0.1.0/data/game.pck"), [0u8; 700]).unwrap();
    std::fs::create_dir_all(dir.join("versions/0.2.0")).unwrap();
    std::fs::write(dir.join("versions/0.2.0").join(game_exe_name()), [0u8; 24]).unwrap();
    assert_eq!(installer.size(), 1024);
}

#[test]
fn remove_and_remove_all_skip_versions_in_use() {
    let dir = common::temp_dir("remove");
    let mut installer = Installer::new(dir.join("versions"));
    for version in ["0.1.0", "0.2.0", "0.3.0"] {
        std::fs::create_dir_all(dir.join("versions").join(version)).unwrap();
    }
    installer.remove("0.3.0").unwrap();
    assert_eq!(installer.installed(), vec!["0.2.0", "0.1.0"]);
    assert!(installer.remove("../escape").is_err());
    installer.in_use.push("0.1.0".into());
    assert!(installer.remove_all().is_err(), "a hosted server's version stays");
    assert_eq!(installer.installed(), vec!["0.1.0"]);
    installer.in_use.clear();
    installer.remove_all().unwrap();
    assert!(installer.installed().is_empty());
}

#[test]
fn repair_replaces_only_missing_or_damaged_files() {
    let dir = common::temp_dir("repair");
    let zip = common::game_zip(game_exe_name());
    let digest = digest_of(&zip, &dir);
    let installer = Installer::new(dir.join("versions"));
    let folder = installer
        .install(
            &release(common::serve(zip.clone(), None), digest.clone(), "0.1.1"),
            &AtomicBool::new(false),
            &mut |_, _| {},
        )
        .expect("installed");
    let good = release(common::serve(zip, None), digest, "0.1.1");
    let fine = installer
        .repair(&good, &AtomicBool::new(false), &mut |_, _| {})
        .expect("checked");
    assert_eq!(fine, 0, "nothing to replace in a good install");

    std::fs::write(folder.join("ExperimentUndead.pck"), b"game pacK").unwrap();
    std::fs::remove_file(folder.join(game_exe_name())).unwrap();
    std::fs::write(folder.join("settings.cfg"), b"player file").unwrap();
    let replaced = installer
        .repair(&good, &AtomicBool::new(false), &mut |_, _| {})
        .expect("repaired");
    assert_eq!(replaced, 2);
    assert_eq!(
        std::fs::read(folder.join("ExperimentUndead.pck")).unwrap(),
        b"game pack"
    );
    assert_eq!(std::fs::read(folder.join(game_exe_name())).unwrap(), b"game exe");
    assert_eq!(std::fs::read(folder.join("settings.cfg")).unwrap(), b"player file");
    assert_eq!(installer.installed(), vec!["0.1.1".to_string()]);
}

#[test]
fn repair_with_a_bad_download_touches_nothing() {
    let dir = common::temp_dir("repair-bad");
    let zip = common::game_zip(game_exe_name());
    let installer = Installer::new(dir.join("versions"));
    let folder = dir.join("versions").join("0.1.1");
    std::fs::create_dir_all(&folder).unwrap();
    std::fs::write(folder.join("ExperimentUndead.pck"), b"old").unwrap();
    let result = installer.repair(
        &release(common::serve(zip, None), "0".repeat(64), "0.1.1"),
        &AtomicBool::new(false),
        &mut |_, _| {},
    );
    assert_eq!(result, Err("The download was damaged. Try again.".to_string()));
    assert_eq!(std::fs::read(folder.join("ExperimentUndead.pck")).unwrap(), b"old");
    assert!(!dir.join("versions").join(".downloads").exists());
}

#[test]
fn install_needs_room_for_the_zip_and_the_game() {
    assert_eq!(space_needed(1_000_000_000), 2_500_000_000);
    assert_eq!(space_needed(0), 0);
}
