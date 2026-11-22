# Rules for coding agents (Codex, Claude, others)

Fenlight is an original wave-based zombie FPS in **Godot 4.7.2**,
written in **typed GDScript**, with RPG progression and co-op on self-hosted
servers of up to 8 players. Every line of code must work in co-op.

This file is the one entry point. Read it all, then only the docs the reading
map names for your task.

## Reading map

| Your task | Also read |
|---|---|
| Any task | This file. `docs/DECISIONS.md` entries for the systems you touch (not the whole file) |
| A feature | Its row in `docs/ROADMAP.md`, its approved plan in `docs/plans/`, `docs/FOUNDATIONS.md` (fill in its **Ready to build** checklist), the `docs/adr/` records it touches |
| Co-op code (RPCs, shared state) | `docs/MULTIPLAYER.md`, section "Writing co-op code", and `docs/adr/0003-trusted-client-co-op.md` |
| New content or a new system | `docs/HOW_TO_ADD.md` |
| Anything visual, audio, UI, gun, enemy or map | `docs/design/README.md`; for visuals `docs/design/look-rules.md` (use its colours, names and numbers) |
| Anything the player sees or reads | `docs/design/lore.md` "Story links for game content" (see Lore link below) |
| A bug, crash or test run | `docs/LOGGING.md` |
| A CI structure rule fails | `docs/CODE_RULES.md` |
| How work flows (pillars, milestones) | `docs/PROCESS.md` |

**Plan first.** Before building a feature, find it in `docs/ROADMAP.md`. If it
needs a plan, build only from an approved plan in `docs/plans/` and only the
step your task names. No approved plan: write one first
(`docs/plans/README.md`). Your PR says `Plan: docs/plans/<file>.md, step N`.
Do not go against a decision record in `docs/adr/` without writing a new one first.

**Lore link:** nothing goes in the game without a story reason. Before adding
anything the player sees or reads (zombie, gun, item, prop, sign, screen,
name), find its reason in `docs/design/lore.md`. No reason yet: add a
provisional row there in the same PR, and ask the person about any choice that
sets the story or tone. Points and score stay a game abstraction.

## Skills

Step-by-step guides in `.agents/skills/<name>/SKILL.md` (Codex) and the same
files in `.claude/skills/` (Claude Code). Load the one that fits your task:

| Skill | Use it for |
|---|---|
| `blender-model` | Building or changing a code-made model in `tools/assets/` |
| `godot-asset-import` | Import settings, files to commit and tests for anything in `assets/` |
| `look-check` | Rendering a visual change and comparing it with the style guide |
| `design-change` | Changing a game number or adding content in line with the balance sheet |
| `write-plan` | Writing a feature plan in `docs/plans/` before building |
| `review-plan` | Reviewing a plan PR before it is approved |
| `finish-feature` | Checking a feature against the Definition of done and closing it |
| `pre-merge-review` | An independent review of your diff before the PR is marked ready |

Third-party skills (Apache-2.0, from gamedev-skills/awesome-gamedev-agent-skills, see
`docs/CREDITS.md`) are general Godot 4.7.2 and game-design guides; each one's
description says when to use it: `godot-3d-essentials`, `godot-shaders`,
`godot-physics`, `godot-resources`, `godot-gdscript`, `godot-signals-groups`,
`godot-nodes-scenes`, `godot-animation`, `godot-audio`, `godot-ui-control`,
`godot-multiplayer`, `fps-shooter`, `rpg`, `game-feel`, `level-design`,
`game-ai`, `camera-systems`, `input-systems`, `game-ui-ux`, `audio-design`,
`performance-optimization`.

**Our rules win.** When a third-party skill disagrees with this file, `docs/design/`
or one of our own skills, follow ours: no new autoloads or event buses without the
Keep it simple check, GUT is our test runner, co-op follows `docs/MULTIPLAYER.md`,
numbers come from the balance sheet. Ignore their links to skills we did not copy.
Do not edit these folders; update them by copying a newer upstream release.

**EGM** (`.agents/plugins/egm/`, Google, Apache-2.0): fresh-context plan reviewers, enabled by the session hook. Run `egm-review` on size M/L plans and `egm-drift-report docs/plans/`; our template and rules win.

Edit skills in `.agents/skills/` only, then run
`python tools/ci/check_skills_mirror.py --fix`. CI fails if the copies differ.

## Folders

| Folder | What goes there |
|---|---|
| `core/` | Autoloads only (Events, Content, Net, ...) |
| `systems/<feature>/` | Code and scenes for one feature |
| `content/<type>/` | Data only: `.tres` files. The file name is the id |
| `levels/` | Maps |
| `assets/` | Models, sounds, textures |
| `tests/` | GUT tests (`unit/`, `content/`, `integration/`) |
| `tools/` | Editor and command-line scripts |
| `docs/` | Decisions and credits |

## Code rules

1. **Typed GDScript everywhere.** Untyped and inferred declarations are errors
   in this project. Write `var speed: float = 5.0`, never `var speed = 5.0` or
   `var speed := 5.0`. Type loop variables: `for id: StringName in ids:`.
2. **Content is data.** New guns, enemies, waves = new `.tres` files, not new
   code. Never change a loaded `.tres` at runtime; keep live state in a
   separate object (like `WeaponInstance`).
3. **Signals:** a node signals up to its parent. Game-wide facts go through
   the `Events` autoload, named in the past tense (`enemy_killed`). Requests
   are direct calls (`Economy.try_spend()`), never signals.
4. **No global player.** Loop over the `players` group.
5. **Multiplayer rules:**
   - The player reads `InputFrame`s, never the keyboard directly.
   - Damage, spawns, points and XP only change on the server. Node code asks
     `multiplayer.is_server()` (true in solo); `Net.is_authority()` is only for code
     with no node; never both. Co-op messages follow `docs/MULTIPLAYER.md`
     "Writing co-op code" (CI rule `rpc-rules`).
   - Gameplay runs in `_physics_process`. `_process` is for visuals only.
   - All enemies come from `Spawner`.
   - Gameplay randomness uses `GameSession.rng`, never `randf()`.
   - XP and items go through `ProgressionService`.
6. **Performance:** hold 60 fps with 24 zombies alive (v0.1); the long-term
   target is 120 fps on an RTX 4080 Super at 1440p High. No per-frame
   allocations in hot paths, no `get_node()` in loops, cache lookups.
7. Short doc comment (`##`) at the top of every new script. Few other comments.
8. **Assets.** Up to v0.1, art is built in code to match the style-guide
   previews (Cold Containment): Godot grey boxes and shaders, Blender Python
   scripts in `tools/assets/` that export `.glb` into `assets/`, and
   generated sounds (`tools/generate_sfx.py`). The script is the source; never
   hand-edit its output. Every third-party file (code or asset) gets one line
   in `docs/CREDITS.md`: name, author, link, licence. CC0 first, CC-BY with
   credit, MIT for code. No "non-commercial" or "no AI" licences. No Git LFS.
9. **Names.** Use the design doc's words in code and data:
   - Machines: `SpecimenVault` (random gun), `MedDispenser` (gives a serum),
     `Reforger` (upgrades a gun). Not "mystery box" or "perk machine".
   - Data types: `WeaponData`, `RecoilData`, `EnemyData`, `WaveRules`,
     `EconomyRules`, `SerumData`, `AmmoModData`, `BuyableData`,
     `PowerUpData`, `MapData`. Not `PerkData` or `RoundCurve`.

**Structure rules** (`tools/ci/check_rules.py`): each rule, its reason and its
fix are in `docs/CODE_RULES.md`.

## Keep it simple

Grow the game by adding **small, plain pieces**, not frameworks. When two
readings of a task are possible, pick the one with less code. Examples and the list of things to build only when needed:
`docs/KEEP_IT_SIMPLE.md`.

1. **Build only what your task's phase needs.** The phases are P0 to P10 in the
   architecture doc. Do not add fields, functions, signals, enum values, settings
   or files for a later phase "because we'll need it".
2. **No abstraction before the third use.** Write the code plainly the first
   time, copy it the second time, and only pull out a shared function, base
   class or helper when the third real use arrives.
3. **No interface with one implementation.** No base class whose methods are
   empty stubs, no "Service" that only forwards to another class.
4. **Size limits** (CI `quality` check): function 50 lines, complexity 10,
   file 350 lines, 6 function arguments. If you hit a limit, split by job
   (move the zombie's attack logic to its own function), not by layer (no
   `ZombieAttackHelper`, `ZombieAttackManager`).
5. **New autoload:** only the ones in the architecture doc's autoload table
   (Events, Content, Settings, Audio, Pool, Game, Net, plus Build, Log, UI),
   and only when your task actually needs it. Any other autoload: stop and ask in the PR. Add exactly
   one line at the end of the `[autoload]` block in `project.godot`.
6. **New manager / director / service node:** only if it owns state or a rule
   that no existing node owns. If it would just pass calls through, put the code
   in the node that owns the data.
7. **New base class:** only when there are already 3 concrete classes that need
   it, or the architecture doc names it (HealthComponent, HitZone, Interactable).
8. **Godot first.** Use the built-in tool before writing your own: signals,
   groups, Timer/Tween, AnimationPlayer, Resources, NavigationAgent3D,
   AudioStreamRandomizer, ConfigFile, JSON, MultiplayerSpawner/Synchronizer.
   No custom event bus, state-machine framework, dependency injection,
   object factory, plugin system or service locator.
9. **Co-op: follow the written pattern.** Co-op is trusted client: the client
   asks, the server decides shared state (`docs/MULTIPLAYER.md`, ADR 0003). Use
   the seams in code rule 5. Do **not** add prediction, interpolation buffers
   or lag compensation without a new decision record.
10. **No config for things nobody tunes.** Export a value to data only if a
    designer will change it for balance or feel. Fixed rules stay as constants.
11. **Delete, don't disable.** Remove dead code, unused functions and
    commented-out blocks in the same PR that makes them dead. Git keeps history.
12. **Prefer changing data over changing code.** A new gun, zombie, wave mix or
    serum is a `.tres` file. If it needs code, add the smallest script that data
    can point to.

Every PR answers the **Simplicity check** in the PR template. Reviewers reject
a PR if an answer is "no" without a good reason.

## How to run checks

```bash
# Godot 4.7.2 headless binary, if not already installed:
curl -sSL -o godot.zip https://github.com/godotengine/godot/releases/download/4.7.2-stable/Godot_v4.7.2-stable_linux.x86_64.zip
unzip -q godot.zip && mv Godot_v4.7.2-stable_linux.x86_64 godot && chmod +x godot

./godot --headless --path . --import                       # import assets
./godot --headless --path . --quit-after 300               # boot test: no SCRIPT ERROR / Parse Error
./godot --headless --path . -s addons/gut/gut_cmdln.gd     # all GUT tests
./godot --headless --path . -s addons/gut/gut_cmdln.gd -gconfig= -gtest=res://tests/unit/<file>.gd -gexit  # one file

pip install "gdtoolkit==4.5.0" "ruff==0.17.5"              # the quality check
python -m unittest discover -s tools/ci -p "test_*.py"
python tools/ci/check_pr.py origin/main
python tools/ci/check_rules.py
```

Claude Code cloud sessions install Godot (as `godot` on PATH), gdtoolkit and ruff
automatically (`.claude/hooks/session-start.sh`). Run the import once before tests.
All of these must pass before you open a pull request. If you cannot download
Godot, say so in the PR and let CI run the checks.

## CI checks (the merge gate)

- **`quality`**: `gdlint` (repo `gdlintrc`) and `gdformat --check --line-length 120`
  (fix with `gdformat --line-length 120 <files>`; format the whole file when you
  touch an old one), the size limits above (`gdradon cc`), `ruff check` and
  `ruff format --check` (line length 120), the tests in `tools/ci/`, and the
  structure rules. **Tests required:** a changed `.gd` in `core/` or `systems/`
  needs a changed file in `tests/`. Only visual-only or pure-rename changes get
  the label `no-tests-needed`, with the reason in the PR.
- **`test`**: import, boot test, all GUT tests. Any `SCRIPT ERROR` or
  `Parse Error` fails it. `tests/unit/test_scripts_compile.gd` loads every
  script, so the warnings set to error in `project.godot` (unused variables,
  shadowing, unreachable code) fail CI too.
- **`soak`**: plays Halcyon Labs rounds 1-10 headless (seed 1, 4x speed) and
  must print `| PASS |` with no `SCRIPT ERROR`. When it fails, read the job
  summary table and the `soak-logs` artifact.

Never lower warning levels, loosen thresholds, or skip or delete a test to get
green. If a check seems wrong, ask the person first.

**Test rules.** `tests/unit/`: one file per system, pure logic (no scene tree
when possible). `tests/content/`: data checks for every `content/` type; a new
Resource type gets new content checks. `tests/integration/`: a real
`GameSession` run headless, for flows across systems. Every bug fix adds a test
that fails without the fix. Tests use `GameSession.rng` with a fixed seed,
never real time or `randf()`.

**Logs.** When you build a system, add `Log.warn` lines for its early warning
signs and list them in the `docs/LOGGING.md` catalogue.

## Gotchas

- `godot -s <script>` runs without autoloads. For a script that needs them,
  run a temporary `.tscn` that holds the script instead.
- After pulling main, run `godot --headless --path . --import` once. A stale
  `.godot` class cache makes scripts fail to load.
- Never commit an editor-churned `project.godot`, and commit only the
  `.tres` / `.tscn` files you meant to change: editor-local uids break CI.
- The game pauses when its window loses focus.
- `Array.sort()` on StringNames orders them by memory address, which differs
  between machines. Use `Content.sorted_ids()` or sort a `PackedStringArray`.
- Model imports: `meshes/light_baking=2` for kit and static props (baked into
  lightmaps), `3` for anything that moves (zombies, guns, doors, pickups).
  Details: the `godot-asset-import` skill.

## Merging

- You may squash-merge your own PR, no human approval needed, when `quality`,
  `test` and `soak` are green on the head commit. CI is the merge gate.
- **Review before ready.** Run the `pre-merge-review` skill: a fresh
  subagent reviews your diff. Fix every Blocking finding, give a reason for
  each declined Suggestion, and fill the PR's `Review:` line (CI checks it).
  Handle other review comments the same way; resolve each conversation.
- Never merge with a red or pending check, and never merge someone else's PR.
- Each PR gets exactly one label for release notes: `new`, `fix`, `balance`
  or `tech`.

## Working rules

- One task = one branch = one pull request. Branch name: `codex/<task-name>`
  (Claude: `claude/<task-name>`).
- Only touch the files and folders your task allows. If you must touch
  something else, stop and explain why in the PR instead of doing it.
- Add or update tests for everything you build.
- Add one line to `docs/DECISIONS.md` (at most 300 characters, with a link) for
  each design difference, simplification or provisional pick; remove the line
  when you fix it.
- Open the PR as a **draft** and fill in the PR template.
