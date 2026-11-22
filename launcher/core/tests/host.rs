use launcher_core::host::{server_args, Host, Tick, LOG_FILE};
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

mod common;

/// The fake server `cargo test` builds from `examples/fake_server.rs`.
fn fake_server() -> PathBuf {
    let deps = std::env::current_exe().unwrap();
    let name = format!("fake_server{}", std::env::consts::EXE_SUFFIX);
    deps.parent().unwrap().parent().unwrap().join("examples").join(name)
}

fn wait_for_exit(host: &mut Host) -> Option<i32> {
    let start = Instant::now();
    while start.elapsed() < Duration::from_secs(10) {
        if let Some(code) = host.poll() {
            return Some(code);
        }
        std::thread::sleep(Duration::from_millis(20));
    }
    None
}

#[test]
fn server_args_match_the_game_and_clamp() {
    let stop = Path::new("/tmp/eu.stop");
    let drain = Path::new("/tmp/eu.drain");
    assert_eq!(
        server_args(7790, 4, stop, drain),
        vec![
            "--headless",
            "--",
            "--server",
            "--port=7790",
            "--max-players=4",
            "--stop-file=/tmp/eu.stop",
            "--drain-file=/tmp/eu.drain"
        ]
    );
    let clamped = server_args(0, 99, stop, drain);
    assert_eq!(clamped[3], "--port=1");
    assert_eq!(clamped[4], "--max-players=8");
    assert_eq!(server_args(7777, 0, stop, drain)[4], "--max-players=1");
}

#[test]
fn start_runs_the_game_as_a_server_and_stop_ends_it() {
    let dir = common::temp_dir("host");
    let mut host = Host::new(dir.join("server"));
    host.start(&fake_server(), "0.1.1", 7790, 4).expect("started");
    assert_eq!(host.running().as_deref(), Some("0.1.1"));
    assert!(
        host.start(&fake_server(), "0.1.1", 7790, 4).is_err(),
        "one server at a time"
    );
    host.stop();
    assert_eq!(wait_for_exit(&mut host), Some(0));
    assert_eq!(host.running(), None);
    let log = std::fs::read_to_string(host.dir.join(LOG_FILE)).unwrap();
    assert!(
        log.contains("--server --port=7790 --max-players=4 --stop-file="),
        "{log}"
    );
}

#[test]
fn exit_code_is_reported_once() {
    let dir = common::temp_dir("host-code");
    let mut host = Host::new(dir.join("server"));
    host.start(&fake_server(), "0.1.1", 7790, 4).expect("started");
    std::fs::write(host.stop_file(), "3").unwrap();
    assert_eq!(wait_for_exit(&mut host), Some(3));
    assert_eq!(host.poll(), None);
}

#[test]
fn a_new_start_clears_an_old_stop_file() {
    let dir = common::temp_dir("host-stale");
    let mut host = Host::new(dir.join("server"));
    std::fs::create_dir_all(&host.dir).unwrap();
    std::fs::write(host.stop_file(), "stop").unwrap();
    host.start(&fake_server(), "0.1.1", 7790, 4).expect("started");
    std::thread::sleep(Duration::from_millis(200));
    assert_eq!(
        host.running().as_deref(),
        Some("0.1.1"),
        "an old stop file does not stop it"
    );
    host.stop_and_wait(Duration::from_secs(10));
    assert_eq!(host.running(), None);
}

#[test]
fn missing_game_is_a_plain_error() {
    let dir = common::temp_dir("host-missing");
    let mut host = Host::new(dir.join("server"));
    let problem = host.start(&dir.join("nope.exe"), "0.1.1", 7790, 4).unwrap_err();
    assert!(problem.starts_with("Could not start the server"), "{problem}");
    assert_eq!(host.running(), None);
}

fn wait_for_tick(host: &mut Host, newest: Option<(&Path, &str)>) -> Tick {
    let start = Instant::now();
    loop {
        let tick = host.tick(newest);
        if tick != Tick::Running || start.elapsed() > Duration::from_secs(10) {
            return tick;
        }
        std::thread::sleep(Duration::from_millis(20));
    }
}

#[test]
fn a_newer_install_drains_once_then_restarts_on_it() {
    let dir = common::temp_dir("host-drain");
    let mut host = Host::new(dir.join("server"));
    let exe = fake_server();
    host.start(&exe, "0.1.1", 7790, 4).expect("started");
    assert_eq!(
        host.tick(Some((&exe, "0.1.1"))),
        Tick::Running,
        "same version: nothing to do"
    );
    assert!(!host.drain_file().exists());
    assert_eq!(host.tick(Some((&exe, "0.1.2"))), Tick::Draining("0.1.2".into()));
    assert!(host.drain_file().exists(), "the server is asked to finish, not stopped");
    assert_eq!(
        wait_for_tick(&mut host, Some((&exe, "0.1.2"))),
        Tick::Restarted("0.1.2".into())
    );
    assert_eq!(host.running().as_deref(), Some("0.1.2"));
    assert!(!host.drain_file().exists(), "a fresh start clears the drain file");
    assert_eq!(host.tick(Some((&exe, "0.1.2"))), Tick::Running);
    let start = Instant::now();
    let mut log = String::new();
    while !log.contains("--server") && start.elapsed() < Duration::from_secs(5) {
        std::thread::sleep(Duration::from_millis(20));
        log = std::fs::read_to_string(host.dir.join(LOG_FILE)).unwrap();
    }
    assert!(
        log.contains("--port=7790 --max-players=4"),
        "same port and limit: {log}"
    );
    host.stop_and_wait(Duration::from_secs(10));
}

#[test]
fn a_stopped_or_crashed_server_is_not_restarted() {
    let dir = common::temp_dir("host-no-restart");
    let mut host = Host::new(dir.join("server"));
    let exe = fake_server();
    for (written, code) in [("stop", 0), ("7", 7)] {
        host.start(&exe, "0.1.1", 7790, 4).expect("started");
        std::fs::write(host.stop_file(), written).unwrap();
        assert_eq!(wait_for_tick(&mut host, Some((&exe, "0.1.1"))), Tick::Exited(code));
        assert_eq!(host.tick(Some((&exe, "0.1.1"))), Tick::Idle);
        assert_eq!(host.running(), None);
    }
}

#[test]
fn checking_running_keeps_the_exit_code() {
    let dir = common::temp_dir("host-keep-code");
    let mut host = Host::new(dir.join("server"));
    host.start(&fake_server(), "0.1.1", 7790, 4).expect("started");
    std::fs::write(host.stop_file(), "3").unwrap();
    let start = Instant::now();
    while host.running().is_some() && start.elapsed() < Duration::from_secs(10) {
        std::thread::sleep(Duration::from_millis(20));
    }
    assert_eq!(host.poll(), Some(3), "the status poll did not swallow the update exit");
}

#[test]
fn an_update_restart_keeps_the_old_log() {
    let dir = common::temp_dir("host-log-kept");
    let mut host = Host::new(dir.join("server"));
    let exe = fake_server();
    host.start(&exe, "0.1.1", 7790, 4).expect("started");
    assert_eq!(host.tick(Some((&exe, "0.1.2"))), Tick::Draining("0.1.2".into()));
    assert_eq!(
        wait_for_tick(&mut host, Some((&exe, "0.1.2"))),
        Tick::Restarted("0.1.2".into())
    );
    host.stop_and_wait(Duration::from_secs(10));
    let log = std::fs::read_to_string(host.dir.join(LOG_FILE)).unwrap();
    assert!(log.contains("--- Server v0.1.1 on port 7790 ---"), "{log}");
    assert!(log.contains("--- Server v0.1.2 on port 7790 ---"), "{log}");
}

#[test]
fn a_drain_file_that_cannot_be_written_is_tried_again_quietly() {
    let dir = common::temp_dir("host-drain-blocked");
    let mut host = Host::new(dir.join("server"));
    let exe = fake_server();
    host.start(&exe, "0.1.1", 7790, 4).expect("started");
    std::fs::create_dir_all(host.drain_file()).unwrap();
    for _ in 0..3 {
        assert_eq!(
            host.tick(Some((&exe, "0.1.2"))),
            Tick::Running,
            "no Draining (and no log line) while the write fails"
        );
    }
    std::fs::remove_dir(host.drain_file()).unwrap();
    assert_eq!(host.tick(Some((&exe, "0.1.2"))), Tick::Draining("0.1.2".into()));
    host.stop_and_wait(Duration::from_secs(10));
}
