# Plan: Separate launcher program

Status: Building
Roadmap: F-82
Phase: P8 (steps 1-4 land before Release v0.1.0, F-11)
Size: L
Approved by: the person in the project thread, 2026-11-19 ("Approve, start building" card, after picking Tauri and a Windows installer); plan PR #378
Lore link: the launcher shows the game's name, its news and the Oriel/Halcyon/Cordon names from docs/design/lore.md (Factions); the tagline "The cold kept it asleep." is a provisional row in "Story links for game content" (Maps, rooms and props)

## Goal

Players install one small program, the Fenlight launcher, like
Steam or Battle.net. It installs the game, keeps it updated, shows news and
patch notes, hosts a server, and keeps itself updated. The game exe itself
goes straight to the main menu. Serves "Better together": friends are always
on the same version with no manual downloads.

This replaces the launcher built into the game (F-65 steps 5-6, PR #331).
The person changed direction on 2026-11-19: "with launcher I mean a separate
program that updates and installs the game, not a built-in launcher into the
.exe that just goes to the menu screen".

## Scope

In:

- A Tauri 2 app in `launcher/`: a small Rust core (downloads, checksums,
  unzip, starting the game and a server) and a plain HTML/CSS/JS window
  (step 1). About 10 MB, using the WebView2 that ships with Windows 10 and 11.
- A per-user Windows installer, `Fenlight-Setup-<version>.exe`, made
  by Tauri's own NSIS bundler, and launcher self-update through Tauri's
  updater plugin (step 2).
- The in-game launcher screen is deleted; "Restart to update" in the join
  error dialog starts the launcher instead (step 3).
- Host a server from the launcher, updated between matches (step 4, takes
  over F-65 step 9).
- The concept look: sidebar (Play, News, Patches, Settings, Support), hero
  banner, news list, big green Play, channel dropdown, install size and free
  space (step 5).

Not in (non-goals, and where each one goes instead):

- Mods page: no mod system exists. Added when one does.
- Accounts, login, friends list, store: no accounts (ADR 0006).
- A Linux launcher: Linux players and servers keep the plain zip (servers
  use Docker). Later, if a Linux player asks (Tauri builds an AppImage).
- A JS framework or npm bundler: plain HTML/CSS/JS files, no build step for
  the window. Later, only if the pages outgrow it.
- Delta patches: full zip download, as in F-65. Later, when builds pass 1 GB.
- Moving an installed game to another folder, playing an older version: later, if asked
  (step 6 picks the folder before the first install only).
- Code signing of the exe: still blocked for EU individuals
  (`docs/RELEASING.md`). Tauri's update signature is separate and is in.
- Server image, handshake, saves, channels: unchanged, stay in F-65.

## How it fits together

```
%LOCALAPPDATA%\Fenlight Launcher\   installed by the setup exe (per user, no admin)
  fenlight-launcher.exe
%LOCALAPPDATA%\com.experimentundead.launcher\  the launcher's data folder (the uninstaller offers to delete it)
  launcher.json                              channel, server port, max players
  launcher.log
  game\versions\0.1.0-test.2\               full game, installed by the launcher
  game\versions\0.1.0-test.3\               newest; Play starts this one
```

| Piece | Rule |
|---|---|
| Launcher project | `launcher/` with `src-tauri/` (Rust, Tauri 2) and `ui/` (static HTML/CSS/JS served as Tauri's `frontendDist`). `launcher/.gdignore` keeps the game project from importing its images. |
| Game install | Rust port of `ReleaseFeed` and `VersionInstaller`, same rules as F-65: newest release on the channel with a `-windows.zip` and a SHA-256 digest, download, check, unzip through a temp folder, keep the 2 newest. Play starts the newest with `--from-launcher --launcher-exe=<path>`. Crates: `reqwest`, `sha2`, `zip`, `serde_json`. |
| Version compare | Ported to Rust once. `tests/fixtures/version_table.json` is read by both the game's GUT test and the launcher's `cargo test`, so the two can never disagree. |
| Launcher version | Built from the same tag as the game, same version (`tauri.conf.json` version set by `tools/ci/stamp_version.sh`). |
| Launcher self-update | Tauri's updater plugin: on start it reads `latest.json` from the newest release on the channel, downloads the new setup exe, checks its signature with the public key built into the launcher, runs it quietly and restarts. The signing key is a GitHub secret (`TAURI_SIGNING_PRIVATE_KEY`). Any failure keeps the old launcher running. |
| Release assets | Add `Fenlight-Setup-<version>.exe`, its `.sig`, and `latest.json`. Existing zip names unchanged. From v0.1.0 these join the F-65 asset contract. |
| Game finds the launcher | The `--launcher-exe=` path it was started with. Started by hand or a dev build: no "Restart to update" button. |
| News | `launcher/news/news.json` + images on `main`, fetched from `raw.githubusercontent.com` (one call per start). Offline: the copy built into the launcher. Adding news is a docs-style PR, no release. |
| Patches | The release notes of every release on the channel, from the Releases call the launcher already makes. |

## Ready to build

- Foundations touched (docs/FOUNDATIONS.md): 9 tests and CI, 10 exported
  builds. Both solid. Step 1 adds a Rust job to CI.
- Decision records: 0012 (built-in launcher; "do not add a second launcher
  program without a new record"), 0006, 0005. New record
  [0018](../adr/0018-separate-launcher.md) replaces 0012's launcher point.
- Co-op: the launcher has no network game code. The hosted server is the
  game build with `--server`, unchanged.
- Data: no Resource types, no save change. New `launcher/news/news.json`.
- Events and UI: no new Events. The game loses the `launcher` screen
  (`content/screens/launcher.tres`) in step 3.
- Input, gameplay, randomness: not touched.
- Tests: `cargo test` in `launcher/src-tauri` (feed, installer with a local
  HTTP server in the test, server host), `cargo fmt --check` and
  `cargo clippy -D warnings`, a Windows build on PRs touching `launcher/`,
  game tests updated for the removed screen.
- Logging: the launcher writes `launcher.log` in its data folder with
  `check_failed`, `installed`, `install_failed`, `self_updated`,
  `self_update_failed`; listed in `docs/LOGGING.md`.
- Performance: nothing in the game loop.

## Design references

- `docs/plans/client-server-updates.md` "How the launcher works", steps 4-6
  and 9: the install, channel and hosting rules this plan keeps.
- `docs/adr/0012-updates-and-release-channels.md`: amended by ADR 0018.
- `/mnt/project-files/launcher/launcher_concept.png` (copied to
  `docs/design/reference/launcher_concept.png` in step 5): the look target.
- `docs/design/look-rules.md`: Cold Containment colours; the concept's acid
  green is Fenlight green.
- `docs/RELEASING.md`: tags, channels, asset names.
- `docs/KEEP_IT_SIMPLE.md` rule 8, read as "the tool's built-in first":
  Tauri's NSIS bundler and updater plugin instead of our own.

## Systems touched

| Folder or file | New / changed | What changes |
|---|---|---|
| `launcher/core/` | new | Rust library with no window code, so Linux CI tests it without WebView: `version.rs`, `feed.rs`, `install.rs`, `settings.rs`, `log.rs`, `host.rs` (step 4), `tests/` |
| `launcher/src-tauri/` | new | the thin Tauri app: `Cargo.toml`, `tauri.conf.json`, `src/main.rs` (commands the window calls), icons from `tools/assets/launcher_icon.py` |
| `launcher/ui/` | new | `index.html`, `app.js`, `style.css`, one JS file per page (step 5), images |
| `launcher/news/` | new | `news.json` + images |
| `systems/launcher/` | removed | step 3 (screen, feed, installer) and step 4 (`server_host.gd`) |
| `content/screens/launcher.tres` | removed | step 3 |
| `systems/ui/main_menu.gd` | changed | no launcher hand-over or root refresh (step 3); `--server` stays |
| `systems/ui/net_error_dialog.gd` | changed | "Restart to update" starts `--launcher-exe` (step 3) |
| `.github/workflows/launcher.yml` | new | fmt, clippy, test (Ubuntu); build (Windows) |
| `.github/workflows/release.yml` | changed | build and attach setup, `.sig`, `latest.json` (step 2) |
| `docs/` | changed | RELEASING, LOGGING, DECISIONS, ADR 0018, F-65 plan note, lore row |

Autoloads, managers or base classes added: none.

Files over 300 lines this plan grows: none. `launcher_screen.gd` (320) is
deleted. Rust and JS files follow the same 350-line limit by hand (one file
per job).

## Data

- `launcher/news/news.json`: `{"items": [{"title", "summary", "date",
  "image", "url"}]}`; `image` is a path under `launcher/news/`. The first
  item is the hero banner. Provisional first items: the v0.1.0-test.2 notes
  and the Halcyon Labs map.
- `launcher.json` in the launcher data folder: `channel`, `port`,
  `max_players`. Not a save.
- `tests/fixtures/version_table.json`: `[[a, b, expected]]` rows.
- Save format change: none.

## Co-op behaviour

- Who owns the state: the launcher owns nothing shared. The hosted server is
  the game build run as a dedicated server (F-65 step 6), unchanged.
- What clients send: nothing new.
- What players see: nothing changes in a match.
- Late joiner: not affected.
- Dedicated server: the launcher never runs on a server. Docker stays.

## Performance

No cost in the game. The launcher makes three calls per start (Releases
API, `latest.json`, `news.json`), far under GitHub's 60 an hour
unauthenticated limit. Idle it uses one WebView2 window and no game code.

## Steps

### Step 1: The Tauri launcher installs and starts the game

- Build: `launcher/` Tauri 2 project with one plain page: channel dropdown,
  status, progress bar, Play. Rust commands (as built) `status`, `refresh`,
  `set_channel`, `install` (emits progress events), `cancel` and `play`. Port
  `ReleaseFeed`/`VersionInstaller` rules (see table). Shared version table
  fixture. `launcher/.gdignore`. New `launcher.yml` workflow: fmt, clippy,
  `cargo test` on Ubuntu; `cargo build --release -p fenlight-launcher` on Windows for
  PRs touching `launcher/`. The game is untouched in this step. ADR 0018
  accepted.
- Files: `launcher/**`, `.github/workflows/launcher.yml`,
  `tests/fixtures/version_table.json`, `tests/unit/test_build.gd` (reads the
  fixture), `tools/ci/test_workflows.py`, `docs/LOGGING.md`,
  `docs/adr/0018-separate-launcher.md`.
- Tests: `cargo test`: feed picks per channel (fixture JSON copied from
  `tests/fixtures/releases.json`), skips releases without zip or digest;
  installer against a local HTTP server: a good zip lands in
  `versions/<v>/`, a wrong digest or cut-off download leaves nothing, only 2
  newest stay; version table. GUT: `test_build.gd` reads the same table.
- Done when: the launcher built on Windows installs the newest release on
  its channel and Play starts it. Done 2026-11-20, PR #397.

### Step 2: Setup exe and self-update

- Build: Tauri NSIS bundle (`installMode: currentUser`, Start menu and
  desktop shortcut, uninstall entry), product name "Fenlight
  Launcher". Updater plugin with the public key in `tauri.conf.json` and the
  endpoint `https://github.com/J3vb/Fenlight/releases/latest/download/latest.json`
  for stable; test reads `latest.json` from the newest pre-release through
  the Releases API. `release.yml` builds on `windows-latest` with
  `TAURI_SIGNING_PRIVATE_KEY` and attaches the setup, `.sig` and
  `latest.json`. Uninstall asks whether to remove the game folder too.
  Needs the person once: add the signing key as a repository secret (the
  step's thread makes the key and gives exact clicks).
- Files: `launcher/src-tauri/tauri.conf.json`, `src/main.rs`,
  `.github/workflows/release.yml`, `tools/ci/launcher_release.py` (new: stamp and manifest),
  `tools/ci/test_launcher_release.py` (new), `tools/ci/test_workflows.py`,
  `docs/RELEASING.md`.
- Tests: `test_make_latest_json.py` (version, notes, URL, signature);
  `test_workflows.py` (release attaches the three files); the release job
  installs the setup with `/S`, checks the exe and shortcut, then uninstalls
  and checks they are gone.
- Done when: a release has a setup exe that installs and uninstalls cleanly,
  and a launcher one release behind updates itself (play-tested by the
  person on the release after the first one that has it).

### Step 3: Remove the launcher from the game

- Build: delete `systems/launcher/launcher_screen.gd`, `.tscn`,
  `release_feed.gd`, `version_installer.gd`, `content/screens/launcher.tres`,
  their tests, and the hand-over and root refresh in `MainMenu._hand_over()`
  (keeps `--server`). `NetErrorDialog.can_update()` is true only with a
  `--launcher-exe=` argument whose file exists; the button starts it and
  quits. `tools/ci/smoke_test.sh` drops the `--launcher` checks. Testers on
  v0.1.0-test.1 keep their old built-in launcher; RELEASING tells them to
  install the new launcher.
- Files: `systems/launcher/*` (except `server_host.gd`),
  `content/screens/launcher.tres`, `systems/ui/main_menu.gd`,
  `systems/ui/net_error_dialog.gd`, `tools/ci/smoke_test.sh`,
  `tests/unit/test_launcher_screen.gd`, `test_release_feed.gd`,
  `test_version_installer.gd` (removed), the net error dialog test,
  `docs/RELEASING.md`, `docs/plans/client-server-updates.md` (steps 5-6 and
  9 point here).
- Tests: a release build in a root folder goes straight to the main menu
  (fails today: launcher opens); "Restart to update" shows only with an
  existing `--launcher-exe`.
- Done when: the game exe never shows a launcher screen.

### Step 4: Host a server from the launcher

> 2026-11-20: built in two PRs. 4a (PR #428): the Host page (start, stop, status, Open logs, ask
> before closing) and deleting the game's `server_host.gd`. 4b: the 15-minute update
> check, drain file and exit-code-3 restart, together with the game's drain mode from
> F-65 step 8, which was not built yet.

- Build: `src/host.rs`: start `versions/<newest>/ExperimentUndead.exe
  --headless -- --server --port=<p> --max-players=<n> --stop-file=<f>
  --drain-file=<d>`, stop through the stop file, status. Host page: port,
  max players 1-8, Start, Stop, running version, Open logs, the
  firewall/port-forward line. Closing the launcher while hosting asks, then
  stops the server. Every 15 minutes: check the channel, install a newer
  game while the server runs, write the drain file, restart on exit code 3
  only (F-65 step 9 rules). Delete `systems/launcher/server_host.gd` and its
  test.
- Files: `launcher/src-tauri/src/host.rs`, `src/main.rs`,
  `launcher/ui/host.js`, `index.html`, `systems/launcher/` (removed),
  `tests/unit/test_server_host.gd` (removed), `docs/RELEASING.md`.
- Tests: `cargo test`: argument building and clamping; with a fake server
  process (a tiny test binary that exits with a given code), exit 3
  restarts on the new version, exit 0 or a crash does not; a newer release
  installs and writes the drain file without stopping the server; the
  running version is never pruned.
- Done when: a player hosts, stops and auto-updates a server from the
  launcher with no second download.

### Step 5: The concept look

> 2026-11-20: built. News tests live in `launcher/core/tests/news.rs` (the window crate
> has no tests); the concept copy is `docs/design/images/launcher_concept.jpg`. Repair game
> files deletes the newest version and downloads it again (step 6 replaces this; the SHA-256 check runs on the
> zip). The person signed off the look on 2026-11-20.

- Build: the concept layout, 1280x720 minimum, resizable, custom title bar:
  left sidebar (Play, News, Patches, Settings, Support; News dot when an item
  is newer than the last one seen), logo and tagline, hero banner from the
  first news item with Read more, Latest news (3 items, View all), bottom
  bar with the big Fenlight-green **Play** (Install / Update / Installing
  42% / Play), Game version dropdown (Stable vX / Test vX) with "Up to
  date", Installation (installed size, free space, "..." menu: open game
  folder, check files, uninstall game). Patches: release notes list.
  Settings: channel, close launcher on Play. Support: logs folder, GitHub
  issues link. Background: a render of Halcyon Labs at night (provisional,
  made with the look-check skill). Mods left out.
- Files: `launcher/ui/*`, `launcher/news/news.json` + images,
  `launcher/src-tauri/src/main.rs` (disk space, sizes),
  `launcher/src-tauri/tests/news.rs`,
  `docs/design/reference/launcher_concept.png`.
- Tests: `cargo test`: news.json parses, every image exists, a broken feed
  falls back to the built-in copy; installed size and free space commands.
  Look: a Playwright screenshot of `ui/index.html` with fake data next to
  the concept, sent to the person.
- Done when: the person signs off the launcher look against the concept.

### Step 6: Pick where to install, Repair that checks files, fixed window

> 2026-11-22, asked by the person after v0.1.1: the launcher installed the game on start,
> Repair deleted the game and could end on Retry, a long status pushed the bottom bar out of
> the window, and the window could be resized.

- Build: no download on start. With no game installed, Play reads **Install** and opens an
  Install dialog: the game folder (default `<data folder>/game`, where older installs
  already are), **Browse…** (system folder picker; the game goes into a `Fenlight` folder
  inside the pick), the space it needs (zip + unpacked, about 2.5x the zip) and the free
  space on that drive; Install is off when the drive is too small. The folder is saved as
  `install_dir` in `launcher.json`; updates, Repair, the hosted server and Open game folder
  use it. Browse is refused once a version is installed (uninstall first). Updates still
  install on their own once the game is installed.
- Repair downloads the installed version's zip, checks its SHA-256, and rewrites only the
  files whose size or CRC-32 differ from the zip; nothing is deleted first.
- Window: one fixed size (1440x860), not resizable, no maximise button. The status line has
  a fixed width and at most two lines.
- Files: `launcher/core/src/{settings,install,feed}.rs`, `launcher/src-tauri/src/{main,pages}.rs`,
  `tauri.conf.json`, `capabilities/default.json`, `launcher/ui/*`, `tauri-plugin-dialog`.
- Tests: `cargo test` (install folder, old settings keep the old folder, repair replaces
  only bad files and leaves player files, a bad zip touches nothing, no auto install with
  nothing installed); `tools/ci/test_launcher_window.py` (fixed window, status width,
  Install dialog, the window only downloads for updates).
- Done when: a fresh launcher waits for Install, installs where the player picked, and v0.1.2
  is released.

## Acceptance

- [ ] A player who runs the setup exe gets the launcher, which installs the
  newest game on their channel and plays it (steps 1-2).
- [ ] A launcher one release behind updates itself and the game (step 2,
  and a play-test by the person).
- [ ] The game exe never shows a launcher screen (step 3 test).
- [ ] A player hosts and stops a server from the launcher, and it updates
  between matches (step 4 tests).
- [x] The launcher matches the concept (step 5, the person's sign-off, 2026-11-20).

## Risks

- WebView2 missing on an old Windows 10: the NSIS setup uses Tauri's
  `downloadBootstrapper` mode, which installs it.
- Rust build time on Windows runners (first build ~10 minutes): cache
  `target/` with `Swatinem/rust-cache`; the Windows job runs only on PRs
  touching `launcher/` and on release tags.
- Lost signing key: launchers already installed cannot self-update; players
  reinstall from the setup exe once. The key's thread says where to back it
  up.
- Unsigned exe that downloads exes looks like malware to some scanners:
  same as F-65; the setup exe gets one SmartScreen warning.
- Two version compare copies drift: the shared fixture fails one side.
- A second language (Rust, JS) in the repo: kept inside `launcher/`, with
  its own fmt/clippy checks, and no framework.

## Open decisions

- [x] What is the launcher built with? Tauri (the person, 2026-11-19,
  decision card, asked for something light).
- [x] How do players first get the launcher? A Windows installer (the
  person, 2026-11-19, decision card). Tauri's NSIS bundler makes it.
