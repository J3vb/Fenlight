# Logging and diagnostics

Every run of the game or server writes a structured log that a person or an
AI agent can read to find, debug and fix problems. Code: `core/log.gd` (the
`Log` autoload), `systems/diagnostics/`.

## Where the files are

Folder `user://logs/`:

| Platform | Folder |
|---|---|
| Windows | `%APPDATA%\Godot\app_userdata\Fenlight\logs\` |
| Linux | `~/.local/share/godot/app_userdata/Fenlight/logs/` |
| Docker / Unraid server | `/data/godot/app_userdata/Fenlight/logs/` (the `/data` volume) |

Per run (the last 20 runs are kept):

- `run_<UTC time>_<client|server>_<pid>.jsonl`: the log, one JSON object per line.
- `run_<...>.summary.json`: counts, distinct problems and perf numbers.
  Written at start, every 30 s and on exit. `"clean_exit": false` means the run crashed
  or was killed.
- `godot.log`: Godot's own plain-text output (prints, engine errors). Use it
  only when the JSON log is not enough.

The server also prints every warning and error to stdout as
`[WARN] system.event {data}`, so `docker logs` shows them.

## Line format

```json
{"time":"2026-11-14T19:43:24","up_ms":2016,"frame":108,"level":"warn","system":"perf",
 "event":"long_frames","round":3,"peer":1,"session":"run_20261114T194323_client",
 "data":{"count":2,"worst_ms":143.9}}
```

- `level`: `info` (normal fact), `warn` (early warning sign, game goes on),
  `error` (something is broken).
- `system` + `event`: what happened. The catalogue is below.
- `up_ms` / `frame`: time since start and render frame, to line events up.
- `round`: current wave round (0 = between matches or not started).
- `peer`: network peer id (1 = server or solo).

## How to diagnose (steps for an AI agent)

1. Open the newest `*.summary.json`. Check `clean_exit`, `levels`, `problems`
   (each distinct warning/error with its first line and a count) and `perf`.
2. If `clean_exit` is false, read the last 50 lines of the matching `.jsonl`:
   the crash happened right after the last line. The next run also logs
   `build.previous_run_crashed` with the old log's path.
3. List warnings and errors: `grep -v '"level":"info"' run_X.jsonl`
   (or `jq -c 'select(.level != "info")'`).
4. For each problem, read the lines around its `frame` / `up_ms` to see what
   led up to it (round start, door bought, navmesh rebake ...).
5. `engine.*` lines carry `where` (file:line) and `stack`: go straight to that
   code.
6. Compare `perf.health` samples and `waves.round_started` lines over time:
   steadily rising `nodes`, `objects`, `orphan_nodes` or `memory_mb` across
   rounds is a leak.
7. Fix the cause, add a test that fails without the fix (AGENTS.md rule).

## Event catalogue

| system.event | level | Meaning / what to check |
|---|---|---|
| `build.run_started` | info | Version, commit, OS, CPU, GPU, args, log path |
| `build.run_ended` | info | Clean quit, run length |
| `build.previous_run_crashed` | warn | Last run did not quit cleanly; `previous_log` = its file |
| `engine.engine_error` / `engine_script` / `engine_shader` | error | `push_error` or a script/shader error. `where`, `function`, `stack` |
| `engine.engine_warning` | warn | `push_warning` or an engine warning |
| `player.body_clips_missing` | warn | The player model has no third-person clips, so teammates show a still body; rebuild `player.glb` |
| `player.world_model_missing` | warn | A teammate holds a gun whose `WeaponData` has no `world_model`, so its hands are empty; set the field in the gun's `.tres` |
| `player.mantle_landed_blocked` | warn | A mantle ended with the player inside world collision: the ledge clearance check missed something. `at` = the landing spot; check the geometry there |
| `hud.hud_icon_missing` | warn | The local player got a Serum (`serum`) or gun with no HUD icon, so its slot shows badge letters or no gun picture; set `icon` / `hud_icon` in its `.tres`. Once per id |
| `vendor.vendor_clip_missing` | warn | A Lantern Post stall keeper's model has no clip named by its `VendorData.idle_clip`, so they stand in rest pose; re-export the keeper (`tools/assets/tripo/vendors.json`, `clips: keeper`) or fix the data |
| `perf.long_frames` | warn | Frames over 50 ms in the last second (`count`, `worst_ms`, `draw_compiles`: shader pipelines compiled while drawing that second, `all_compiles`: pipelines of any kind since the last line, `enemies`). Hitch at load is normal; in a round it is not. `draw_compiles` > 0 means a first-use shader stutter |
| `perf.low_fps` | warn | Under 50 fps for 3 s in a row (windowed builds only), with a health snapshot |
| `perf.health` | info | Every 30 s: fps, process/physics ms, memory, objects, nodes, orphan nodes, enemies, draw calls |
| `perf.orphan_nodes_growing` | warn | Over 200 orphan nodes and still rising: nodes created and never freed |
| `level.navmesh_baked` / `navmesh_bake_slow` | info / warn | Navmesh bake time (`reason` load/rebake/rebake_parse). Load and the rebake's scene parse run on the main thread: over 100 ms = visible hitch. A door rebake bakes on a worker thread, so its `ms` is wall time, not a freeze |
| `level.navigation_ready` | info | Time from load until zombies can path |
| `level.navigation_not_ready` | error | No usable navmesh 10 s after load: zombies will not move |
| `enemies.zombie_stuck` | warn | A chasing zombie moved under 0.3 m in 2 s while out of reach (logged once per zombie). `at`, `next_path_point`, `path_finished`: navmesh hole, bad spawn point or geometry snag |
| `enemies.zombie_fell_out` | warn | Zombie below y = -50: missing floor collision (it relocates at once) |
| `enemies.zombie_relocated` | warn | A lost zombie moved to a hidden spawn: `reason` unreachable (20 s without progress), far (over 60 m for 15 s) or fell_out; `from`, `to` (spawn point). Many from one place = navmesh hole there |
| `enemies.zombie_voice_refused` | warn | A zombie sound stayed quiet because every voice in its cap (`cap`: 8 mouths or 6 feet) is closer to the listener. Once per run. Normal in big hordes; if players say zombies are silent nearby, check the caps in `zombie_voice.gd` |
| `waves.round_started` | info | Round number, enemies this round, health snapshot |
| `waves.round_ended` | info | Round cleared |
| `waves.round_stalled` | warn | 90 s in a round with no kill; lists where the living zombies are |
| `waves.blackout_pack_waiting` | warn | A Blackout pack (`pack` Glowers, `round`) waited over 10 s for room under the alive cap. Zombies are stuck alive somewhere or the cap is too low for the pack size |
| `waves.spawn_points_missing` | warn | The Spawner found no marker in its `spawn_group` (`spawn_group`), so no zombie spawns. The map has no spawn markers in that group, or the group name in the Spawner is wrong |
| `player.player_spawned` / `player_died` | info | Player `net_id`, spawn position |
| `player.weapon_has_no_grip` | warn | A gun has no `GripData`, so it shows no first-person arms. `weapon` id; once per gun per run. Add `content/grips/<base id>.tres` and set the gun's `grip` |
| `player.weapon_has_no_feel` | warn | A gun fired with no `FeelData`, so it has no view kick, shake or FOV punch. `weapon` id; once per gun per run. Set the gun's `feel` in its `.tres` |
| `player.reload_motion_unreachable` | warn | The left arm cannot reach a reload key pose, so the forearm stretches off the hand. `weapon` id, `gap` in metres; once per gun per run. Move the gun's reload pose in `WeaponPose` or the grab offsets in `ReloadMotion` |
| `gear.fp_piece_missing` | warn | A worn gear model has no first-person piece (a vest scene without `CuffFP_L`/`CuffFP_R`), so the first-person arms show nothing for it. `visual` id; once per visual per run. Rebuild the model with its first-person pieces |
| `progression.profile_save_failed` | warn | Character could not be saved; `id`, `path`, `error` (Godot Error code). Check folder permissions and disk space |
| `progression.skill_ranks_over_budget` | warn | A character holds more skill ranks than its level allows (edited save or a gate change). `level`, `ranks`; the Research screen asks for Reset all |
| `progression.profile_unreadable` | warn | Existing character is unreadable or malformed; file stays untouched, this match uses a temporary character. `id`, `path`; inspect nearby engine errors |
| `save.profile_newer` | warn | A character file was saved by a newer game version (`id`, `path`, `version` = its save_version). The file stays untouched, the main menu tells the player to update, and this run uses a temporary character. Happens after going back to an older build |
| `save.old_name_data_copied` | info | First run after the rename to Fenlight: the player's settings, saved servers and characters were copied from the old `Experiment Undead` user folder (`files`, `from`). The old folder stays as a backup. Once per PC |
| `save.old_name_copy_failed` | warn | One file from the old `Experiment Undead` user folder could not be copied (`path`, `error`). The player may miss that setting or character; copy it by hand from the old folder |
| `settings.binding_unknown_action` | warn | `user://settings.cfg` has a key binding for an action the game no longer has (`action`); it is ignored. Normal after an action is renamed or removed |
| `settings.binding_malformed` | warn | A saved key binding is not a list of up to 2 `{"type": "key", "physical": n}` / `{"type": "mouse", "button": n}` entries, or names Esc (`action`); that action uses its default keys |
| `settings.display_mode_failed` | warn | The window refused the chosen display mode (`mode`: 0 Windowed, 1 Borderless, 2 Fullscreen). Usually the OS or driver does not allow exclusive fullscreen; pick Borderless |
| `settings.row_unknown_key` | warn | A `content/settings/*.tres` row names a `section`/`key` that `Settings.DEFAULTS` does not have; the row is left off the settings screen. Fix the row or add the key |
| `game.game_over` | info | Final stats |
| `net.peer_connected` / `peer_disconnected` | info | Server side, peer id |
| `net.join_refused` | info | Client side: the server refused the hello (`reason`: `WRONG_VERSION`, `CONTENT_MISMATCH`, `SERVER_FULL`, `SERVER_UPDATING`, or `REFUSED` for a code from a newer server; `older`: `client`, `server` or empty for dev builds; `message`, `client_protocol`, `server_protocol`). `older` says which side to update |
| `net.join_failed` | warn | Client side: the pending join could not start (`error`, a Godot error string), so the game goes back to the main menu. Usually a bad address or a port the OS would not open |
| `net.connection_lost` | warn | Client side: the server disconnected, the connection failed or the server refused authentication. Run XP is banked and the game goes back to the main menu. Look at the server's log for the same time |
| `server.drain_started` | info | A dedicated server saw its drain file (`--drain-file=` / `EU_DRAIN_FILE`): a newer release is installed (`place`, `players`). A match plays on; the hub refuses new players with `SERVER_UPDATING` |
| `server.update_restart` | info | A draining server quits with exit code 3 (`place`): its hub had players (they get the "updating" notice) or it stayed empty for `EMPTY_GRACE`. The launcher restarts it on the newer version |
| `net.round_state_ignored` | warn | A round message reached a peer that must not take it (`sender`): the server got one, or a client got one not from the server. Should never appear |
| `power_ups.crate_expired_unopened` | warn | A Supply Crate vanished before anyone opened it (`name`). Often means players miss it or cannot reach it |
| `power_ups.timer_ignored` | warn | A power-up timer message reached a peer that must not take it (`sender`): the server got one, or a client got one not from the server. Should never appear |
| `net.interaction_rejected` | warn | Server refused a client's interact request (`peer`, `reason`, `path`): `player_not_alive`, `match_over`, `unknown_path`, `out_of_range`, `grant_pending` (last gun grant not applied yet), `bad_facts` (gun facts with wrong fields or ids). At most one per second. Many `out_of_range` = `InteractionSync.REACH_SLACK` too tight |
| `net.deploy_refused` | warn | The hub's deploy vote or `deploy()` was refused (`place`, `reason` or `hub`): an unknown place id on a deploy board, or a deploy outside the hub. A board with a typo in `place` |
| `net.place_change_kicked` | warn | A client was sent to another place but had not disconnected after `Net.CONNECT_TIMEOUT`, so the server dropped it (`peer`) and swapped place. Clients close as soon as the order arrives, so it never got the order: check the network |
| `net.place_changed` | info | The server changed place (`place`, `players` sent along) |
| `net.port_busy` | warn | Enter world could not open the world's port (`port`), so the world runs offline and friends cannot join. Another game or server holds it: change the port in Settings > Network |
| `net.upnp_opened` | info | The router opened the world's game and info ports (`port`) for an hour; renewed every 50 minutes while the game runs |
| `net.upnp_failed` | warn | The router could not open the world's ports (`port`, `reason`: `no_router` = no UPnP router answered, `failed` = it refused the mapping). Friends on the same network can still join; internet friends need the ports opened by hand |
| `net.upnp_cgnat` | warn | The router opened the ports but its internet address is private or provider-shared (100.64.0.0/10): internet friends cannot reach this world (`port`) |
| `net.info_port_busy` | warn | The server browser info port (game port + 1000) is taken by another program: the world runs but browsers cannot see it (`port`) |
| `net.info_bad_packet` | warn | A packet on the info port was not a server browser query; at most one line a second (`source`) |
| `net.coop_started` / `coop_ended` | info | The first friend joined this world, or the last one left (`peers`): the solo or co-op rules now apply (`Net.is_coop()`) |
| `net.go_to_place` | info | This peer loads another place (`place`, `online`) |
| `net.join_switches_place` | info | A joining client loaded another place than the server's and switches before spawning (`from`, `to`) |
| `throwables.grenade_lost` | warn | A grenade fell below the map before it went off (`at`): a hole in the level collision |
| `net.hit_claim_rejected` | warn | Server refused a client's hit, gravity well or grenade claim (`peer`, `reason`): `player_not_alive`, `zombie_not_alive`, `hit_out_of_bounds`, `zone_missing`, `claims_too_fast`, `well_out_of_bounds`, `well_wrong_weapon` (well or orb request named a gun whose `effect` is not WELL: a mismatched build or a cheat), `grenade_not_alive`, `grenade_none_left` (the client's count was out of date), `grenade_bad_throw` (origin, speed or fuse out of range), `grenade_too_fast`, `ability_not_alive`, `ability_not_now` (hub, match over or no ability), `ability_cooling` (the owner's countdown ran ahead by more than 0.25 s), `ability_too_fast`, `ability_locked` (the hello level is below the unlock), `ability_bad_aim` (a Decoy Siren aimed past its 20 m reach plus 3 m). At most one per second |
| `net.trait_rejected` | warn | Server refused a client's Cold Snap request (`peer`, `reason`): `player_not_alive`, `no_cold_snap` (the uid is not that player's Cold Snap gun: a mismatched loadout or a cheat), `cold_snap_too_fast`. At most one per second |
| `net.ability_unknown` | warn | A client's loadout named a field ability that does not exist or that its hello level has not unlocked (`peer`, `ability`): a mismatched build or a cheat; the server copy gets no ability |
| `net.loadout_rejected` | warn | Server refused a client's equipped loadout (`peer`, `reason`): `not_a_dictionary`, `too_much_gear` (more gear than `CharacterProfile.GEAR_SLOTS`), `too_many_guns` (more than the player's weapon slots), `unknown_gun` (gun base not in content), `not_gear` (a worn piece that is not vest, charm or implant), `slot_twice` (two pieces for one slot). The server keeps the last good loadout; check that both builds have the same content |
| `net.skills_rejected` | warn | Server refused a client's skill ranks sent with its loadout (`peer`, `reason`): `unknown_skill` (id not in `content/skills/`), `bad_rank` (not an int from 1 to the node's `max_ranks`), `too_many_points` (more than 54). The whole loadout is ignored; check that both builds have the same skills content |
| `loot.gear_worn` | info | The owner wore a Pack gear item mid-run (`uid`, `slot`); the old piece went into its Pack slot |
| `loot.gear_equip_refused` | warn | A Pack gear item could not be worn (`uid`, `banked`): the run was already banked or there is no character profile (soak bots, tests). In a normal run this should never appear |
| `loot.unknown_legendary` | warn | A saved item names a Legendary (`id`, `uid`) this build does not know (a save from a newer build or a removed Legendary). The item keeps its base name and no trait. Once per id |
| `net.interaction_rate_limited` | warn | A client sent interact requests less than 0.1 s apart; extra ones are refused. At most one per second |
| `ui.unknown_screen` | warn | `UI.push` or `UI.replace` got an id with no `content/screens/<id>.tres`; `id`. Nothing opens |
| `ui.pop_empty` | warn | `UI.pop()` with no screen open: a screen emitted `closed` twice or something popped a screen it did not push |
| `ui.skill_icon_missing` | warn | A skill has no `icon` (`id`); its Research tile shows text only. Add `assets/ui/skills/<id>.svg` and set `icon` |
| `ui.menu_backdrop_missing` | warn | A front-end screen opened with no backdrop texture (`screen`); it shows the dark shade only. The image in `assets/ui/backdrops/` is missing or failed to import |
| `ui.loading_failed` | warn | A root behind a loading screen failed its threaded load; `scene`. The router falls back to a plain scene change |

The separate launcher (F-82, `launcher/`) writes its own JSON lines to `launcher.log` in its data folder (`%LOCALAPPDATA%\com.experimentundead.launcher\` on Windows): `{"t", "level", "event", "message"}`. A hosted server writes its own game log, and its console output goes to `server/server.log` there (Open logs).

| Event | Level | Meaning |
|---|---|---|
| `check_failed` | warn | The launcher could not read the GitHub Releases list (`message` has the reason; "GitHub answered 403" = rate limit, 60 per hour per address). It plays the newest installed version offline |
| `installed` | info | A release is downloaded, checked and unpacked into `<game folder>/versions/<version>/` (`message` = "Installed v<version>.") |
| `install_failed` | warn | A download failed, was cancelled, had the wrong SHA-256, or could not be unpacked (`message` says which). Nothing was installed |
| `self_updated` | info | The launcher installed a newer launcher from the release's `latest.json` (`message` = manifest URL) and restarts |
| `self_update_failed` | warn | A launcher update could not be checked, downloaded or installed (`message`; "signature" = the setup exe was not signed with our key). The old launcher keeps running |
| `server_started` | info | Host a server started the newest installed game as a server (`message` = version and port) |
| `server_start_failed` | warn | The server exe could not start (`message`): the game is missing or damaged. Reinstall it |
| `server_stop_requested` | info | The player pressed Stop server; the server quits on its stop file within a second |
| `server_exited` | info | The hosted server quit and was not restarted (`message` = exit code, or "launcher closed"). A quick exit after `server_started` = port in use; read `server/server.log` |
| `server_draining` | info | A newer game is installed (`message` = version) and the drain file asks the hosted server to finish its match. No `server_update_restarted` within a match's length = the server never drained; read `server/server.log` |
| `server_update_restarted` | info | The hosted server drained (exit code 3) and runs again on the newer version (`message`), same port and player limit |
| `install_dir_picked` | info | The player picked a folder in the Install dialog (`message`); the game goes into a `Fenlight` folder inside it |
| `repaired` | info | Repair game files checked the newest version against its release zip (`message` says how many files it replaced) |
| `repair_failed` | warn | Repair could not download or check the zip, or could not write a file (`message`; "Close the game" = a file was in use). Nothing was deleted |
| `uninstalled` | info | Uninstall game deleted every installed version. Saves and settings stay |

## Adding log lines (rules for agents)

- Call `Log.info/warn/error(&"system", &"event_name", {data})`. System = the
  `systems/` folder name; event = past tense or a state, snake_case.
- `warn` is for early signs: things that should not happen but the game
  survives. Every new system should warn on its own "this looks wrong" cases.
- Put the facts needed to debug in `data`: ids, positions, counts, timings.
  No player names or other personal data.
- Never log per frame, per shot or per hit. Group repeats (see
  `perf.long_frames`) or report once per object (see `zombie_stuck`).
- Add new events to the catalogue above in the same PR.

## Soak test

Run `godot --headless --path . --script res://tools/soak/soak.gd -- --rounds 10 --seed 1 --timescale 4`.
It loads the normal Halcyon Labs session, powers on and opens every door, keeps
an immortal player stationary, and hits one living zombie every 30 physics ticks
only after spawning and window entry finish. Stops after the target round ends
or 10 real minutes. The table includes rounds, kills, points, real run time,
and counts plus the first JSON line for each warning/error in this run's log.

Exit 1: any `error` level, `waves.round_stalled`, `enemies.zombie_fell_out`,
`perf.orphan_nodes_growing`, `level.navigation_not_ready`, an unreadable or
malformed log, or a target round that never finishes. `enemies.zombie_stuck`
and `perf.long_frames` only warn (exit 0); other warning lines are also listed.
The event lists are constants at the top of `tools/soak/soak.gd`.
The separate PR/manual Soak workflow writes the table to the job summary and
uploads `user://logs/` on failure. It is a required check (`soak`).

**Fight mode (balance runs, not in CI).** Add `--fight 1 --wall <gun id>`, for
example `--rounds 16 --fight 1 --wall kestrel_smg`. The player is mortal and a
bot (`tools/soak/soak_bot.gd`) plays: it turns toward the nearest zombie it can
see at a human-like turn rate, aims down sights at the chest (no headshots),
holds fire, reloads when empty, walks backwards when a zombie is within 4 m,
buys the named wall gun the moment it can pay (from anywhere, no walking), and
rebuys its ammo when dry. A zombie it cannot see for 10 s is killed outright,
standing in for the player walking over to it. The run ends when the player
dies; the last table line says `died in round N` (or `survived`), how many
zombies were hunted that way and the gun in hand. A death is not a failure, but
log errors still are. Run several seeds and use the median death round. It is
a rough stand-in for a player: it never trains zombies or picks a spot, so read
it as a trend between two sets of numbers, not as how a human will do.

## Co-op soak

Run `godot --headless --path . --script res://tools/soak/coop_soak.gd -- --clients=2 --rounds=5`.
Other options (all `--name=value`): `--seed=1`, `--timescale=4`, `--gun=rifle_ar_reforged`,
`--port=24700`, `--limit=600` (real seconds before stragglers are killed) and
`--out=user://coop_soak`. It starts one headless dedicated server
(`tools/soak/coop_soak_server.gd`: players cannot die, power on, doors open) and
N bot clients (`tools/soak/coop_soak_bot.gd`). Each bot joins `127.0.0.1` through
the normal join and hello, gives itself the `--gun` on its own PC, moves its own
player to 4 m from the nearest chasing zombie when it is more than 15 m away (or
half the gun's range), and claims one body hit per fire interval (x1.2) through
the real `HitClaims` client path. So every claim should pass the server's damage,
range and rate checks, and kills, points and XP flow through the network code.

Each process runs with its own `XDG_DATA_HOME` (`<out>/server`, `<out>/bot1`, ...)
and writes `<out>/<name>.json`: `done`, the round it saw, its log path and counts
(bots: `claims`, `moves`, `points`, `joined`, `lost_server`; server: `kills`,
`players`). After the target round the bots leave one second apart, then the
server quits. Two clients dropping in the same server frame log an ENet
"Unable to send packet" engine error; that is a known separate issue.

The table has one row per process, then each warning or error with its first log
line. Every log goes through the solo soak's `check_log` (errors, fail events,
target round reached and finished; bots need the client round events from F-40).
On top of that every `net.*` warning fails, grouped by reason, except
`net.hit_claim_rejected (zombie_not_alive)`: two bots hitting the same zombie is
normal. The run also fails when a process wrote no result or did not finish, a
bot lost the server early, or the server saw fewer players than `--clients`.
The last line is `| PASS | co-op soak ... |` or `| FAIL | ...`.

Workflow `Co-op soak` (`.github/workflows/coop-soak.yml`, not a required check):
pull requests touching game code run 2 bots to round 5; nightly and manual runs
use 4 bots to round 20. On failure the `coop-soak-logs` artifact has every
result file and every process's `logs/` folder.
