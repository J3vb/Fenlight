use launcher_core::feed::{auto_update, find, is_newer, newest, patches, Channel, LINUX_SUFFIX, WINDOWS_SUFFIX};
use serde_json::Value;

mod common;

fn releases() -> Vec<Value> {
    let text = std::fs::read_to_string(common::fixture("releases.json")).expect("releases fixture");
    serde_json::from_str(&text).expect("releases json")
}

#[test]
fn stable_skips_pre_releases_and_drafts() {
    let release = newest(&releases(), Channel::Stable, WINDOWS_SUFFIX).expect("a stable release");
    assert_eq!(release.version, "0.1.1");
    assert_eq!(release.digest, "ccc");
    assert_eq!(release.notes, "Stable notes");
}

#[test]
fn test_channel_takes_pre_releases() {
    let release = newest(&releases(), Channel::Test, WINDOWS_SUFFIX).expect("a test release");
    assert_eq!(release.version, "0.2.0-test.1");
}

#[test]
fn release_without_digest_for_this_platform_is_skipped() {
    let release = newest(&releases(), Channel::Stable, LINUX_SUFFIX).expect("a linux release");
    assert_eq!(release.version, "0.1.0");
}

#[test]
fn nothing_newer_than_installed() {
    let installed = vec!["0.1.1".to_string(), "0.1.0".to_string()];
    assert!(!is_newer("0.1.1", &installed));
    assert!(is_newer("0.2.0-test.1", &installed));
    assert!(is_newer("0.1.0", &[]));
}

#[test]
fn first_install_waits_for_the_player_and_updates_do_not() {
    assert!(
        !auto_update("0.1.1", &[]),
        "nothing installed: wait for the Install button"
    );
    assert!(auto_update("0.1.1", &["0.1.0".to_string()]));
    assert!(!auto_update("0.1.1", &["0.1.1".to_string()]));
}

#[test]
fn find_gets_one_version_on_any_channel() {
    assert_eq!(
        find(&releases(), "0.1.0", WINDOWS_SUFFIX).expect("0.1.0").version,
        "0.1.0"
    );
    assert_eq!(
        find(&releases(), "0.2.0-test.1", WINDOWS_SUFFIX)
            .expect("test build")
            .version,
        "0.2.0-test.1"
    );
    assert!(find(&releases(), "9.9.9", WINDOWS_SUFFIX).is_none());
}

#[test]
fn garbage_entries_are_ignored() {
    let list: Vec<Value> = serde_json::from_str(r#"[1, "x", {"tag_name": 5}, {"tag_name": "v1.0.0"}]"#).unwrap();
    assert!(newest(&list, Channel::Test, WINDOWS_SUFFIX).is_none());
}

#[test]
fn launcher_manifest_follows_the_channel() {
    use launcher_core::feed::launcher_manifest_url;
    assert_eq!(
        launcher_manifest_url(&releases(), Channel::Stable).as_deref(),
        Some("https://example.invalid/latest-0.1.1.json")
    );
    assert_eq!(
        launcher_manifest_url(&releases(), Channel::Test).as_deref(),
        Some("https://example.invalid/latest-0.2.0-test.1.json")
    );
    assert!(launcher_manifest_url(&releases()[2..], Channel::Test).is_none());
}

#[test]
fn patches_list_the_channel_newest_first() {
    let stable = patches(&releases(), Channel::Stable);
    let versions: Vec<&str> = stable.iter().map(|patch| patch.version.as_str()).collect();
    assert_eq!(versions, ["0.1.1", "0.1.0"]);
    assert_eq!(stable[0].date, "2026-11-19");
    assert_eq!(stable[0].notes, "Stable notes");
    assert_eq!(stable[1].date, "");
    assert_eq!(patches(&releases(), Channel::Test)[0].version, "0.2.0-test.1");
}
