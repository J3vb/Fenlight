//! Downloads a release zip, checks its SHA-256 and unpacks it into `versions/<version>/`,
//! complete or not at all. Keeps the newest few version folders. Same rules as the game's
//! old `VersionInstaller`.

use crate::feed::{Release, USER_AGENT};
use crate::version;
use sha2::{Digest, Sha256};
use std::fs::{self, File};
use std::io::{self, Read, Write};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};
use std::time::Duration;

/// Version folders kept after an install.
pub const KEEP: usize = 2;
/// A download that receives nothing for this long fails, so Cancel never waits on a dead line.
pub const STALL_TIMEOUT: Duration = Duration::from_secs(30);
const DOWNLOADS: &str = ".downloads";
const CHUNK: usize = 64 * 1024;

/// The game exe inside each version folder.
pub fn game_exe_name() -> &'static str {
    if cfg!(windows) {
        "ExperimentUndead.exe"
    } else {
        "ExperimentUndead.x86_64"
    }
}

/// Free bytes an install needs: the zip download plus the unpacked game, which is about one
/// and a half times the zip.
pub fn space_needed(zip_size: u64) -> u64 {
    zip_size.saturating_mul(5) / 2
}

pub struct Installer {
    /// Folder that holds one folder per installed version.
    pub versions_dir: PathBuf,
    /// Versions that are running (a hosted server) and must not be pruned.
    pub in_use: Vec<String>,
    /// How long a download may receive nothing before it fails (`STALL_TIMEOUT`).
    pub stall_timeout: Duration,
}

impl Installer {
    pub fn new(versions_dir: PathBuf) -> Self {
        Self {
            versions_dir,
            in_use: Vec::new(),
            stall_timeout: STALL_TIMEOUT,
        }
    }

    /// Deletes what an install cut short by closing the launcher left: the `.downloads`
    /// folder and `<version>.tmp` folders. Only one launcher runs, so none is in progress.
    pub fn clean_leftovers(&self) {
        let _ = fs::remove_dir_all(self.versions_dir.join(DOWNLOADS));
        let Ok(entries) = fs::read_dir(&self.versions_dir) else {
            return;
        };
        for entry in entries.filter_map(Result::ok) {
            if entry.file_name().to_string_lossy().ends_with(".tmp") && entry.path().is_dir() {
                let _ = fs::remove_dir_all(entry.path());
            }
        }
    }

    /// Complete version folders (a `.tmp` folder is a failed install), newest first.
    pub fn installed(&self) -> Vec<String> {
        let Ok(entries) = fs::read_dir(&self.versions_dir) else {
            return Vec::new();
        };
        let mut found: Vec<String> = entries
            .filter_map(Result::ok)
            .filter(|entry| entry.path().is_dir())
            .filter_map(|entry| entry.file_name().into_string().ok())
            .filter(|name| version::is_release_version(name))
            .collect();
        found.sort_by(|a, b| version::compare(b, a));
        found
    }

    pub fn exe_path(&self, version: &str) -> PathBuf {
        self.versions_dir.join(version).join(game_exe_name())
    }

    /// Downloads, checks and installs a release. `progress(done, total)` is called while
    /// downloading; setting `cancel` stops it. Returns the version folder or what went wrong.
    pub fn install(
        &self,
        release: &Release,
        cancel: &AtomicBool,
        progress: &mut dyn FnMut(u64, u64),
    ) -> Result<PathBuf, String> {
        self.with_download(release, cancel, progress, |zip_path| {
            self.install_zip(zip_path, &release.digest, &release.version)
        })
    }

    /// Repair game files: downloads the release zip, checks it, then rewrites only the files
    /// of the installed version that are missing or differ from it. Returns how many.
    pub fn repair(
        &self,
        release: &Release,
        cancel: &AtomicBool,
        progress: &mut dyn FnMut(u64, u64),
    ) -> Result<usize, String> {
        self.with_download(release, cancel, progress, |zip_path| {
            self.repair_zip(zip_path, &release.digest, &release.version)
        })
    }

    /// Compares every file in the zip with the installed copy (size and CRC-32 the zip keeps
    /// per file) and rewrites the ones that differ. Files the zip does not have stay.
    pub fn repair_zip(&self, zip_path: &Path, digest: &str, version: &str) -> Result<usize, String> {
        check_digest(zip_path, digest)?;
        let folder = self.versions_dir.join(version);
        let could_not = || format!("Could not repair {}. Close the game and try again.", folder.display());
        let mut archive = File::open(zip_path)
            .ok()
            .and_then(|file| zip::ZipArchive::new(file).ok())
            .ok_or("The download was damaged. Try again.")?;
        let mut replaced = 0;
        for index in 0..archive.len() {
            let mut entry = archive.by_index(index).map_err(|_| could_not())?;
            let Some(relative) = entry.enclosed_name() else {
                return Err("The download was damaged. Try again.".into());
            };
            if entry.is_dir() {
                continue;
            }
            let path = folder.join(relative);
            if file_matches(&path, entry.size(), entry.crc32()) {
                continue;
            }
            write_entry(&mut entry, &path).map_err(|_| could_not())?;
            replaced += 1;
        }
        Ok(replaced)
    }

    fn with_download<T>(
        &self,
        release: &Release,
        cancel: &AtomicBool,
        progress: &mut dyn FnMut(u64, u64),
        then: impl FnOnce(&Path) -> Result<T, String>,
    ) -> Result<T, String> {
        let downloads = self.versions_dir.join(DOWNLOADS);
        fs::create_dir_all(&downloads).map_err(|_| self.write_problem())?;
        let zip_path = downloads.join(format!("{}.zip", release.version));
        let source = Source {
            url: &release.url,
            size: release.size,
            stall_timeout: self.stall_timeout,
        };
        let result = download(&source, &zip_path, cancel, progress).and_then(|_| then(&zip_path));
        let _ = fs::remove_file(&zip_path);
        let _ = fs::remove_dir(&downloads);
        result
    }

    /// Checks the zip against the digest and unpacks it into `versions/<version>/`.
    pub fn install_zip(&self, zip_path: &Path, digest: &str, version: &str) -> Result<PathBuf, String> {
        check_digest(zip_path, digest)?;
        let final_dir = self.versions_dir.join(version);
        let temp_dir = self.versions_dir.join(format!("{version}.tmp"));
        let _ = fs::remove_dir_all(&temp_dir);
        if unzip(zip_path, &temp_dir).is_err() {
            let _ = fs::remove_dir_all(&temp_dir);
            return Err(format!(
                "Could not unpack the game into {}. Check that the drive has free space.",
                self.versions_dir.display()
            ));
        }
        let _ = fs::remove_dir_all(&final_dir);
        if !rename_with_retries(&temp_dir, &final_dir) {
            let _ = fs::remove_dir_all(&temp_dir);
            return Err(format!("Could not finish installing {version}. Try again."));
        }
        let mut keep = self.in_use.clone();
        keep.push(version.to_string());
        self.prune(&keep);
        Ok(final_dir)
    }

    /// Deletes all but the `KEEP` newest version folders (an install keeps the version it just
    /// installed too, even an older stable build next to newer test builds). Folders named in `in_use`, or that
    /// cannot be deleted yet (a running game), stay and are tried again next time.
    pub fn prune(&self, in_use: &[String]) {
        for name in self.installed().iter().skip(KEEP) {
            if !in_use.contains(name) {
                let _ = fs::remove_dir_all(self.versions_dir.join(name));
            }
        }
    }

    /// Bytes used by every installed version, for the Installation panel.
    pub fn size(&self) -> u64 {
        dir_size(&self.versions_dir)
    }

    /// Free bytes on the drive the game installs to (its nearest existing folder).
    pub fn free_space(&self) -> u64 {
        self.versions_dir
            .ancestors()
            .find(|dir| dir.is_dir())
            .and_then(|dir| fs4::available_space(dir).ok())
            .unwrap_or(0)
    }

    /// Deletes one version folder.
    pub fn remove(&self, version: &str) -> Result<(), String> {
        if !version::is_release_version(version) || self.in_use.iter().any(|name| name == version) {
            return Err(format!("v{version} is in use."));
        }
        fs::remove_dir_all(self.versions_dir.join(version))
            .map_err(|_| format!("Could not delete v{version}. Close the game and try again."))
    }

    /// Deletes every installed version that is not in use (Uninstall game).
    pub fn remove_all(&self) -> Result<(), String> {
        for name in self.installed() {
            self.remove(&name)?;
        }
        Ok(())
    }

    fn write_problem(&self) -> String {
        format!(
            "Could not write to {}. Pick a folder you own.",
            self.versions_dir.display()
        )
    }
}

/// Windows virus scanners briefly lock a folder that was just unpacked, so a failed rename is
/// tried a few more times before the install gives up.
fn rename_with_retries(from: &Path, to: &Path) -> bool {
    for attempt in 0..5 {
        if fs::rename(from, to).is_ok() {
            return true;
        }
        if attempt < 4 {
            std::thread::sleep(Duration::from_millis(500));
        }
    }
    false
}

fn check_digest(zip_path: &Path, digest: &str) -> Result<(), String> {
    match sha256_file(zip_path) {
        Ok(found) if found == digest => Ok(()),
        _ => Err("The download was damaged. Try again.".into()),
    }
}

/// True when the file exists with this size and CRC-32.
fn file_matches(path: &Path, size: u64, crc: u32) -> bool {
    if fs::metadata(path).map(|meta| meta.len()).ok() != Some(size) {
        return false;
    }
    let Ok(mut file) = File::open(path) else {
        return false;
    };
    let mut hasher = crc32fast::Hasher::new();
    let mut buffer = vec![0u8; CHUNK];
    loop {
        match file.read(&mut buffer) {
            Ok(0) => return hasher.finalize() == crc,
            Ok(read) => hasher.update(&buffer[..read]),
            Err(_) => return false,
        }
    }
}

fn write_entry(entry: &mut impl Read, path: &Path) -> io::Result<()> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    io::copy(entry, &mut File::create(path)?)?;
    make_executable(path)
}

fn dir_size(path: &Path) -> u64 {
    let Ok(entries) = fs::read_dir(path) else {
        return 0;
    };
    entries
        .filter_map(Result::ok)
        .map(|entry| match entry.file_type() {
            Ok(kind) if kind.is_dir() => dir_size(&entry.path()),
            Ok(_) => entry.metadata().map(|meta| meta.len()).unwrap_or(0),
            Err(_) => 0,
        })
        .sum()
}

/// Lowercase hex SHA-256 of a file, like GitHub's asset `digest` without its `sha256:` prefix.
pub fn sha256_file(path: &Path) -> io::Result<String> {
    let mut file = File::open(path)?;
    let mut hasher = Sha256::new();
    let mut buffer = vec![0u8; CHUNK];
    loop {
        let read = file.read(&mut buffer)?;
        if read == 0 {
            break;
        }
        hasher.update(&buffer[..read]);
    }
    Ok(hasher.finalize().iter().map(|byte| format!("{byte:02x}")).collect())
}

/// Where a download comes from and how long it may stall.
struct Source<'a> {
    url: &'a str,
    size: u64,
    stall_timeout: Duration,
}

fn download(
    source: &Source,
    target: &Path,
    cancel: &AtomicBool,
    progress: &mut dyn FnMut(u64, u64),
) -> Result<(), String> {
    let failed = || "The download failed. Check your connection and try again.".to_string();
    let not_saved = || {
        let folder = target.parent().unwrap_or(target);
        format!(
            "Could not save the download in {}. Check that the drive has free space.",
            folder.display()
        )
    };
    // The blocking client applies this timeout to each read, not to the whole download.
    let client = reqwest::blocking::Client::builder()
        .user_agent(USER_AGENT)
        .connect_timeout(Duration::from_secs(10))
        .timeout(source.stall_timeout)
        .build()
        .map_err(|_| failed())?;
    let mut response = client.get(source.url).send().map_err(|_| failed())?;
    if !response.status().is_success() {
        return Err(failed());
    }
    let total = response.content_length().unwrap_or(source.size);
    let mut file = File::create(target).map_err(|_| not_saved())?;
    let mut buffer = vec![0u8; CHUNK];
    let mut done: u64 = 0;
    loop {
        if cancel.load(Ordering::Relaxed) {
            return Err("Download cancelled.".into());
        }
        let read = response.read(&mut buffer).map_err(|_| failed())?;
        if read == 0 {
            break;
        }
        file.write_all(&buffer[..read]).map_err(|_| not_saved())?;
        done += read as u64;
        progress(done, total);
    }
    if total > 0 && done != total {
        return Err(failed());
    }
    Ok(())
}

fn unzip(zip_path: &Path, target: &Path) -> io::Result<()> {
    let mut archive = zip::ZipArchive::new(File::open(zip_path)?)?;
    fs::create_dir_all(target)?;
    for index in 0..archive.len() {
        let mut entry = archive.by_index(index)?;
        let Some(relative) = entry.enclosed_name() else {
            return Err(io::Error::new(io::ErrorKind::InvalidData, "unsafe path in zip"));
        };
        let path = target.join(relative);
        if entry.is_dir() {
            fs::create_dir_all(&path)?;
            continue;
        }
        write_entry(&mut entry, &path)?;
    }
    Ok(())
}

#[cfg(unix)]
fn make_executable(path: &Path) -> io::Result<()> {
    use std::os::unix::fs::PermissionsExt;
    if path.extension().is_some_and(|extension| extension == "x86_64") {
        fs::set_permissions(path, fs::Permissions::from_mode(0o755))?;
    }
    Ok(())
}

#[cfg(not(unix))]
fn make_executable(_path: &Path) -> io::Result<()> {
    Ok(())
}
