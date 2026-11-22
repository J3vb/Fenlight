//! Reads the GitHub Releases list: the newest release a channel may install, and
//! whether it is newer than what is already installed. Same rules as the game's old
//! `ReleaseFeed`.

use crate::version;
use serde::Serialize;
use serde_json::Value;
use std::time::Duration;

pub const API_URL: &str = "https://api.github.com/repos/J3vb/Fenlight/releases";
pub const WINDOWS_SUFFIX: &str = "-windows.zip";
pub const LINUX_SUFFIX: &str = "-linux.zip";
const DIGEST_PREFIX: &str = "sha256:";
pub const USER_AGENT: &str = "Fenlight-launcher";
/// The launcher's update manifest, attached to each release next to the setup exe.
pub const LAUNCHER_MANIFEST: &str = "latest.json";

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, serde::Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Channel {
    Stable,
    Test,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, serde::Deserialize)]
pub struct Release {
    pub version: String,
    pub notes: String,
    pub url: String,
    pub digest: String,
    pub size: u64,
    pub page: String,
}

/// One release's notes for the Patches page.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct Patch {
    pub version: String,
    /// `YYYY-MM-DD`, empty when GitHub gave none.
    pub date: String,
    pub notes: String,
}

/// Notes of every release the channel may see, newest first.
pub fn patches(releases: &[Value], channel: Channel) -> Vec<Patch> {
    let mut found: Vec<Patch> = releases
        .iter()
        .filter_map(|entry| {
            Some(Patch {
                version: release_version(entry, channel)?,
                date: entry["published_at"].as_str().unwrap_or("").chars().take(10).collect(),
                notes: entry["body"].as_str().unwrap_or("").to_string(),
            })
        })
        .collect();
    found.sort_by(|a, b| version::compare(&b.version, &a.version));
    found
}

/// The zip name ending for this platform's game build.
pub fn platform_suffix() -> &'static str {
    if cfg!(windows) {
        WINDOWS_SUFFIX
    } else {
        LINUX_SUFFIX
    }
}

/// Downloads the releases list. Errors are plain text for the status line and the log.
/// GitHub sends 30 releases unless asked for more; 100 is its most per page and keeps the
/// newest stable release in the list even after many test builds.
pub fn fetch(api_url: &str) -> Result<Vec<Value>, String> {
    let client = reqwest::blocking::Client::builder()
        .user_agent(USER_AGENT)
        .connect_timeout(Duration::from_secs(8))
        .timeout(Duration::from_secs(20))
        .build()
        .map_err(|error| error.to_string())?;
    let response = client
        .get(api_url)
        .query(&[("per_page", "100")])
        .send()
        .map_err(|error| error.to_string())?;
    if !response.status().is_success() {
        return Err(format!("GitHub answered {}", response.status()));
    }
    response.json::<Vec<Value>>().map_err(|error| error.to_string())
}

/// Newest release on the channel with this platform's zip and a SHA-256 digest.
/// Stable sees only full releases; test sees pre-releases too.
pub fn newest(releases: &[Value], channel: Channel, suffix: &str) -> Option<Release> {
    releases
        .iter()
        .filter_map(|entry| installable(entry, channel, suffix))
        .max_by(|a, b| version::compare(&a.version, &b.version))
}

/// The release of one version, whatever its channel: Repair fetches what is installed.
pub fn find(releases: &[Value], version: &str, suffix: &str) -> Option<Release> {
    releases
        .iter()
        .filter_map(|entry| installable(entry, Channel::Test, suffix))
        .find(|release| release.version == version)
}

/// The installed versions a channel plays: stable plays only stable builds, so switching from
/// Test back to Stable does not keep running a test build (or its test saves).
pub fn installed_on(installed: &[String], channel: Channel) -> Vec<String> {
    installed
        .iter()
        .filter(|version| channel == Channel::Test || !version.contains('-'))
        .cloned()
        .collect()
}

/// True when version is newer than every installed one.
pub fn is_newer(version: &str, installed: &[String]) -> bool {
    installed.iter().all(|other| version::compare(version, other).is_gt())
}

/// Updates install on their own once the game is installed. The first install waits for the
/// player to pick a folder and press Install.
pub fn auto_update(newest: &str, installed: &[String]) -> bool {
    !installed.is_empty() && is_newer(newest, installed)
}

/// Download address of the launcher update manifest in the newest release on the channel that
/// has one. Releases from before the separate launcher have none and are skipped.
pub fn launcher_manifest_url(releases: &[Value], channel: Channel) -> Option<String> {
    releases
        .iter()
        .filter_map(|entry| {
            let version = release_version(entry, channel)?;
            let asset = entry["assets"]
                .as_array()?
                .iter()
                .find(|asset| asset["name"] == LAUNCHER_MANIFEST)?;
            Some((version, asset["browser_download_url"].as_str()?.to_string()))
        })
        .max_by(|a, b| version::compare(&a.0, &b.0))
        .map(|(_, url)| url)
}

/// The release's version when the channel may use it: no drafts, stable sees no pre-releases.
fn release_version(entry: &Value, channel: Channel) -> Option<String> {
    let prerelease = entry["prerelease"].as_bool().unwrap_or(false);
    if entry["draft"].as_bool().unwrap_or(false) || (channel == Channel::Stable && prerelease) {
        return None;
    }
    let version = entry["tag_name"].as_str()?.trim_start_matches('v').to_string();
    if !version::is_release_version(&version) || (channel == Channel::Stable && version.contains('-')) {
        return None;
    }
    Some(version)
}

fn installable(entry: &Value, channel: Channel, suffix: &str) -> Option<Release> {
    let version = release_version(entry, channel)?;
    let asset = entry["assets"].as_array()?.iter().find(|asset| {
        let name = asset["name"].as_str().unwrap_or("");
        let digest = asset["digest"].as_str().unwrap_or("");
        name.ends_with(suffix) && digest.starts_with(DIGEST_PREFIX)
    })?;
    Some(Release {
        version,
        notes: entry["body"].as_str().unwrap_or("").to_string(),
        url: asset["browser_download_url"].as_str().unwrap_or("").to_string(),
        digest: asset["digest"].as_str()?.trim_start_matches(DIGEST_PREFIX).to_string(),
        size: asset["size"].as_u64().unwrap_or(0),
        page: entry["html_url"].as_str().unwrap_or("").to_string(),
    })
}
