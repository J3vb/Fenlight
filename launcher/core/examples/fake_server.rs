//! Stands in for the game in the host tests: prints its arguments, then waits. Its
//! `--stop-file=` makes it exit with the number written in it (0 for any other text); its
//! `--drain-file=` makes it exit with 3, like an empty server that drained. While it runs it
//! counts up in `<stop file>.alive`, so tests can see whether it still runs.

use std::path::PathBuf;
use std::time::Duration;

fn file_arg(args: &[String], name: &str) -> PathBuf {
    let prefix = format!("--{name}=");
    args.iter()
        .find_map(|arg| arg.strip_prefix(&prefix).map(PathBuf::from))
        .unwrap_or_else(|| panic!("{prefix}"))
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    println!("{}", args.join(" "));
    let stop_file = file_arg(&args, "stop-file");
    let drain_file = file_arg(&args, "drain-file");
    let alive = stop_file.with_extension("alive");
    let mut beat: u64 = 0;
    loop {
        std::thread::sleep(Duration::from_millis(20));
        beat += 1;
        let _ = std::fs::write(&alive, beat.to_string());
        if drain_file.exists() {
            std::process::exit(3);
        }
        if stop_file.exists() {
            std::thread::sleep(Duration::from_millis(50));
            let code = std::fs::read_to_string(&stop_file)
                .ok()
                .and_then(|text| text.trim().parse().ok())
                .unwrap_or(0);
            std::process::exit(code);
        }
    }
}
