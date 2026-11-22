# Launcher: Rust core and Tauri app

Each line comes from a bug class that reached review after CI was green.

1. **Nothing slow on the UI thread.** A `#[tauri::command] fn` without
   `async`, a setup hook or a window event handler runs on the main thread.
   Any network call, big file work, process wait, sleep, blocking dialog or
   wait on a lock there freezes the window on Windows. Slow work goes to
   `spawn_blocking` or a thread.
2. **Locks.** A `Mutex` held across a download, file work, a child wait or
   an `.await`. Two locks taken in different orders. A value read, the lock
   dropped, then acted on (check-then-act). `lock().unwrap()` after a worker
   panicked.
3. **Starts once.** Play, Install, Repair, self-update and host start: can a
   double click or two events start it twice? Is the busy flag set before
   the work starts and cleared on every error and cancel path?
4. **Right version.** After a channel switch (Test to Stable and back), an
   install, a cancel, a failed update or going offline, does Play start the
   build for the current settings? Any cached "newest" or "installed" left stale?
5. **Deletes.** For every `remove_dir_all`, `remove_file` and prune: what
   exact path, and can it be the folder the player picked, a parent, an
   empty or `..` version string, or a file the launcher did not create?
   Repair replaces only files that do not match. Nothing is deleted under a
   running game or server.
6. **Unzip and install.** Digest checked before unpack. Entry paths cannot
   leave the target folder. Unpack to a temp folder, then rename; a failed
   or half install is cleaned up and never looks complete. Rename when the
   target exists or a file is in use.
7. **Saved files are atomic.** Settings and state: write a temp file, then
   rename. A crash mid-write keeps the old file. A missing, broken or older
   file loads defaults without wiping the rest.
8. **Network.** Connect timeout and a read or stall timeout on every
   request (a download with `timeout(None)` needs its own stall check).
   HTTP status checked. Size and digest verified. 403 rate limit handled.
9. **True error messages.** Disk full, no permission, file in use, offline,
   403 and bad digest each say what they are; no catch-all "check your
   connection". No `let _ =` on a result the player needs to hear about. The
   cause also goes to `launcher.log`.
10. **Child processes.** The game and the hosted server are reaped. The
    server stops when the launcher quits, crashes or is killed (no orphan).
    Old stop and drain files are cleared. Port already in use. Restart on
    exit code 3 cannot loop forever.
11. **Cancel.** Mid-download, mid-unzip and mid-repair: state goes back to
    idle, temp files go, and the next Install works.
12. **Disk space.** Checked before download for zip plus unpacked size; what
    happens when it runs out half way?
13. **Windows paths.** Spaces, non-ASCII user names, long paths, read-only
    folders, a locked exe, no console window flashing for a child.
14. **Contract with the UI.** Command names, argument names (JS camelCase to
    Rust snake_case), `Status` fields, event names and payloads changed on
    both sides; `src-tauri/capabilities` allows what is called.
15. **Frozen release contract and layering.** Asset names, zip root and
    version table as in `docs/RELEASING.md`. Logic lives in `launcher/core`
    with a test in `launcher/core/tests`; `src-tauri` stays thin.
