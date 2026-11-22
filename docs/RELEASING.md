# Builds and releases

Plan and reasoning: https://claude.ai/artifact/HApjhDRXmDDVDYLezv4ozt

## What happens automatically

| When | Workflow | You get |
|---|---|---|
| Push or PR | `ci.yml` | tests and lint (owned by the code quality setup) |
| Merge to main | `build.yml` | Windows + Linux builds under the run's **Artifacts** (kept 3 days), server image `edge` |
| Pull request (not docs-only) | `build.yml` | same export and smoke test, builds under **Artifacts**, no image |
| Actions tab, "Cut release", **Run workflow** | `cut-release.yml` | checks CI, makes the tag, starts `release.yml` on it |
| Tag `v1.2.3` | `release.yml` | GitHub Release with zips and notes, server image `1.2.3`, `1.2`, `latest` |
| Actions tab, "Build", **Run workflow** | `build.yml` | builds of any branch, no image |

All exports run on Linux runners (the Windows .exe is cross-exported), so they
use the cheap 1x minutes. Every build is smoke-tested: the exported client and
server must boot without script errors, the client must join the server, and
the server must stop cleanly before anything is uploaded.

## Cut a release

1. Merge what you want into main.
2. GitHub, **Actions**, **Cut release**, **Run workflow**. Pick the channel (`stable` or
   `test`) and leave **version** empty for the next one (stable: next patch after the newest
   stable tag, test: the next `-test.N` of that patch), or type one like `0.2.0`. A Claude
   thread can start it too (the GitHub `actions_run_trigger` tool), so nobody has to push a tag.
3. Cut release refuses a version that exists, is not newer, or does not fit the channel, and a
   commit whose CI `test` check has not passed or has a failed check. Then it makes the tag
   and starts **Release** on it, which builds, tests and publishes everything. About 10 minutes.

**Player notes:** put them in `docs/release-notes/v0.2.0.md` (named after the tag) on main
before cutting. They go above the PR list GitHub writes from the `new`, `fix`, `balance`
and `tech` labels.

**Channel flags:** Release sets them from the tag every time, also when the release was made
by hand in the GitHub UI: stable (`v1.2.3`) is a full release marked latest, test
(`v1.2.3-test.1`) is a pre-release that never becomes latest. Pushing a tag by hand or
publishing from the GitHub UI still works and gets the same files and flags.

## Channels (F-65)

| Channel | Tag | Who gets it |
|---|---|---|
| stable | `v0.1.0` | everyone (launcher default) |
| test | `v0.1.0-test.1` (GitHub pre-release) | players who pick "Test builds" in the launcher |
| dev | none (main builds, `0.1.1-dev.N+sha`) | Actions artifacts only; never shows in the launcher |

- Players install and update the game with the separate launcher (next section). The game
  exe has no launcher screen any more: started by hand, it opens the main menu.
- **Restart to update:** "your game is older" offers a button only when the separate
  launcher started the game (`--launcher-exe=<path>`). It starts the launcher, which updates.
- **Frozen from v0.1.0 (the launcher depends on them):** asset names end in
  `-windows.zip`, `-linux.zip`, `-server.zip` (today `Fenlight-<version>-windows.zip`; before
  the rename they started `ExperimentUndead-`, and the launcher only reads the end); zip root
  holds `ExperimentUndead.exe` / `.x86_64` and its pck (file names kept through the rename); tags `vX.Y.Z` and `vX.Y.Z-test.N`; GitHub's `digest` field.
- **Cut a test build:** run **Cut release** with channel `test`. Save version bumps go to
  test first. A bad release is fixed by releasing a newer one (roll forward), never by
  deleting the old one.
- Main builds count up from the last **stable** tag (`stamp_version.sh` ignores test tags).
- **Host a server** is a panel in the separate launcher (next section).

## The separate launcher (F-82)

The launcher is its own program in `launcher/` (Tauri 2, ADR 0018). The game has no
launcher screen of its own (removed in F-82 step 3).

- **Install:** download `Fenlight-Setup-<version>.exe` from Releases and run it.
  It installs per user (no admin) to `%LOCALAPPDATA%\Fenlight Launcher\`, with a
  Start menu and desktop shortcut and an uninstall entry. Windows SmartScreen warns once
  (the exe is not code-signed): **More info**, **Run anyway**.
- **Game files:** the launcher installs the game into
  `%LOCALAPPDATA%\com.experimentundead.launcher\game\versions\<version>\` (SHA-256 checked,
  the 2 newest kept). Its settings (`launcher.json`) and log (`launcher.log`) sit in that
  same folder. Uninstalling with "Delete the application data" ticked removes the game too.
- **Launcher updates:** each release also carries `Fenlight-Setup-<version>.exe.sig`
  and `latest.json`. On start the launcher reads `latest.json` from the newest release on its
  channel; when it is newer, it downloads the setup exe, checks its signature against the
  public key built into the launcher, installs it quietly and restarts.
- **Signing key:** the private key is the repository secret `TAURI_SIGNING_PRIVATE_KEY` (no
  password). Without it a release still gets the setup exe but no `.sig` or `latest.json`,
  so installed launchers do not update to it. Losing the key means every player reinstalls
  once from a new setup exe built with a new key; keep a copy in a password manager.
- **Host a server:** the launcher's Host a server panel runs the newest installed game with
  `--headless -- --server --port=<p> --max-players=<n> --stop-file=<f> --drain-file=<d>` (port and player
  limit saved in `launcher.json`). Its console output goes to `server\server.log` in the
  launcher's data folder (Open logs). Stop writes the stop file; closing the launcher while
  hosting asks, then stops the server. Players, the host too, join from Servers in the game;
  Play keeps the launcher open while it hosts. The version a server runs is never deleted.
- **Hosted servers update between matches:** while hosting, the launcher checks the channel
  every 15 minutes and installs a newer release next to the running server, then writes the
  drain file. The server finishes its match; in the hub it refuses new players ("restarting
  for an update"), tells everyone there, and quits with exit code 3 (an empty server waits
  12 s first). The launcher then starts the new version on the same port. Any other exit is
  left alone. Players see a Restart to update button that opens the launcher.
- **News:** the launcher's Play and News pages read `launcher/news/news.json` on `main`, so
  posting news is a PR that adds an item there (a new, higher `id`; newest first is sorted
  for you). Pictures must ship in `launcher/ui/news/`; a picture that an older launcher lacks
  shows the Kessel Dam fallback. Offline, the launcher shows the copy it was built with.
  Patches lists the release notes of every release on the player's channel.
- **Frozen from v0.1.0:** `latest.json` and the `.sig` beside the setup exe it names
  (`Fenlight-Setup-<version>.exe`; `ExperimentUndead-Setup-` before the rename).
- **Version:** the release workflow stamps the tag's version into the launcher
  (`tools/ci/launcher_release.py stamp`); builds outside a release say `0.0.0`.

## Version numbers

- The git tag is the version. Never edit a version number by hand.
- Main builds are `next-patch-dev.N+commit`, for example `0.1.1-dev.4+a1b2c3d`.
- CI writes `version.json` before export; the `Build` autoload reads it and
  the HUD shows it bottom right. In the editor it shows `dev (editor)`.
- `Build.PROTOCOL_VERSION`: bump when client/server messages change.
- `SaveFile.CURRENT_VERSION`: bump when save fields change, and add an
  upgrade step plus a test (see `systems/save/save_file.gd`).

## Guards that keep old versions working

- **Saved ids are permanent.** Every weapon, gear, affix, rarity and skill
  file and every map folder can be in a player's save, so each is listed in
  `tools/ci/saved_ids.txt`. The `quality` check fails when a listed id
  disappears (also when its line is deleted with it) or a new one is not
  listed. Add new ids with `python tools/ci/check_saved_ids.py --fix`. To
  rename one, add a `SaveFile` migration and keep the old line.
- **Save versions never go down.** `quality` fails when
  `SaveFile.CURRENT_VERSION` is lower than at the newest stable `v*` tag.
- **Old clients get a clear refusal.** Every Build downloads the newest
  stable release that is not its own version, joins this build's exported
  server with that old client and requires a `join_refused` with
  `WRONG_VERSION` within 15 s. Releases from before the JSON handshake
  (protocol below 17), or no release at all, print "skipped".
- **Frozen handshake keys.** See `docs/MULTIPLAYER.md` (The handshake).

## Crash logs

- Logs: `%APPDATA%\Godot\app_userdata\Fenlight\logs` on Windows,
  `~/.local/share/godot/app_userdata/Fenlight/logs` on Linux. Godot
  keeps the last few runs. The first lines hold version, commit, OS and GPU.
- If the game did not quit cleanly, the next start shows "Last session crashed"
  with the log folder in the HUD corner.
- Release builds keep GDScript call stacks, so errors name the function.

## Server on Unraid

1. One time: GitHub, **Settings**, **Developer settings**, **Personal access
   tokens**, create a classic token with only `read:packages`.
2. On Unraid: `docker login ghcr.io -u <github user>` with that token as password.
3. Copy `deploy/unraid/experiment-undead-server.xml` to
   `/boot/config/plugins/dockerMan/templates-user/` and add the container from
   **Docker**, **Add Container**, template `experiment-undead-server`.
4. It runs as `99:100` (nobody:users) so it can write to appdata. Ports 7777/udp (game) and 8777/udp (server browser info; set `EU_SERVER_NAME` to name the server).

Run it anywhere else:

```bash
docker run -d --name eu-server -p 7777:7777/udp -p 8777:8777/udp -v eu-data:/data \
  ghcr.io/j3vb/experiment-undead-server:latest
```

Settings: `EU_PORT` (7777), `EU_MAX_PLAYERS` (8, max 8), or `-- --port=7777`.
`docker stop` shuts down cleanly (Godot ignores SIGTERM, so the entrypoint
drops a stop file the server watches).

The server is a placeholder until co-op lands: it opens the port and accepts
connections, but runs no match yet.

## Running a downloaded Linux build

Artifacts from the Actions page lose the executable bit: run
`chmod +x ExperimentUndead.x86_64` once. Release zips already have it.

## Costs and limits

- GitHub Pro includes 3,000 Actions minutes and 2 GB storage a month. A build
  takes about 10 to 15 minutes. Keep the Actions spending limit at $0 so
  nothing is ever charged; builds pause instead.
- The Godot download and export templates live in the Actions cache (not billed).
- Old untagged server images are deleted, keeping the newest 5.

## Not yet

- **Code signing:** Windows shows a SmartScreen warning on unsigned builds.
  Azure Artifact Signing is not open to individuals in the EU yet; Steam does
  not need signing. Revisit before a public download outside Steam.
- **itch.io:** add a `butler push` job to `release.yml` with a `BUTLER_API_KEY` secret.
- **Steam:** after the app fee, add a `steamcmd` upload job to a beta branch.
- **Windows file details:** the .exe shows Godot's icon and details because
  setting them needs rcedit + Wine on the runner.
