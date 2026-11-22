# Structure rules checked by CI

Run `python tools/ci/check_rules.py` from the repository root. CI and the local
quality check run the same rules on tracked files outside `addons/` and `.godot/`.
Messages use `path:line: rule-name: message`. Game code means `core/`, `systems/`
and `levels/`; each rule below says when it has a narrower scope.

## 1. core-no-features

Files in `core/` cannot contain `res://systems/` or `res://levels/`. Keeping the
base independent lets features change without changing the autoloads.

- Good, in a feature: `var weapon: WeaponData = Content.weapon(&"rifle_ar")`
- Bad, in core: `const PlayerScene = preload("res://systems/player/player.tscn")`

Fix the reported dependency by moving feature wiring into the feature or level;
use a signal when core needs to announce a fact.

## 2. content-is-data

`content/` holds only `.tres` resources and their Godot `.uid` or `.import`
sidecars. Plain data keeps content additions small and easy to balance.

- Good resource line, in `content/weapons/rifle_ar.tres`: `damage = 34.0`
- Bad script line, in `content/weapons/rifle_ar.gd`: `extends Resource`

Move scripts and scenes to their feature under `systems/`; keep resource
instances in `content/`. Remove unrelated files and invalid sidecars.

## 3. file-names

Every `.gd`, `.tscn`, `.tres`, `.py` and `.glb` basename must match
`^[a-z0-9_]+\.[a-z]+$`. Consistent names make paths predictable.

- Good path: `systems/player/player_camera.gd`
- Bad path: `systems/player/PlayerCamera.gd`

Rename the file to snake_case and update every reference, including imports.

## 4. class-name-matches-file

A GDScript `class_name` must match its snake_case filename. This makes a type's
implementation easy to find.

- Good, in `player_camera.gd`: `class_name PlayerCamera`
- Bad, in `camera.gd`: `class_name PlayerCamera`

Rename the file to match the class and update its paths, or correct the class
name and its uses if the filename already describes the job.

## 5. input-only-in-input

Direct `Input.is_action_*`, `Input.get_vector`, `Input.get_axis`,
`Input.is_key_pressed` and `Input.is_mouse_button_pressed` calls belong only in
`systems/input/`, `systems/ui/`, `systems/debug/` or `tools/`. Gameplay reads
`InputFrame`s so the same logic can later consume another player's input.

- Good, in gameplay: `if frame.has(InputFrame.FIRE):`
- Bad, in gameplay: `if Input.is_action_just_pressed("fire"):`

Read the action in the input feature and pass it through an `InputFrame`.

## 6. session-rng

Gameplay uses the session's seeded RNG for repeatable multiplayer results.
Global `randf`, `randi`, `randf_range`, `randi_range`, `randfn`, `randomize` and
`seed` calls, plus array `.pick_random()` and `.shuffle()`, are allowed in game
code only when the line ends with `# cosmetic`.

- Good gameplay line: `var roll: float = session.rng.randf()`
- Bad gameplay line: `var roll: float = randf()`

Switch gameplay to `GameSession.rng` and add a fixed-seed test. For a verified
visual or sound variation only, end its line with `# cosmetic`; never use that
comment to exempt a gameplay decision.

## 7. log-not-print

Game code uses `Log` so diagnostics are available in saved run logs. Direct
`print`, `prints`, `printt`, `print_debug`, `printerr` and `push_warning` calls
are allowed only in `core/log.gd`, `core/build.gd` and
`systems/net/dedicated_server.gd`.

- Good: `Log.warn(&"spawner", &"spawn_failed", {"enemy_id": enemy_id})`
- Bad: `push_warning("Spawn failed")`

Replace the reported call with a structured `Log` event at the appropriate
level, following `docs/LOGGING.md`.

## 8. no-absolute-paths

Game code cannot look up `/root/...`, use a node path that climbs two parents,
or chain `get_parent().get_parent()`. Signals, autoload names and exported
`NodePath`s keep scenes movable without breaking their callers.

- Good: `Events.enemy_killed.emit(enemy, info)`
- Bad: `get_node("/root/Events").enemy_killed.emit(enemy, info)`

Use the autoload name directly, signal to the owning parent, or export the
needed node reference instead of depending on a particular scene hierarchy.

## 9. autoload-list

Every `[autoload]` name in `project.godot` must appear in `ALLOWED_AUTOLOADS`:
Events, Content, Net, Build, Log, Settings, UI, Audio, Pool or Game. A new global
owner must be visible in review and justified by the Keep it simple rules.

- Good autoload entry: `Events="*res://core/events.gd"`
- Bad unapproved entry: `EnemyManager="*res://core/enemy_manager.gd"`

Keep feature state in its existing owner. If a new autoload is justified,
review that decision and update the allowed list explicitly.

## 10. no-weakening

`gdlintrc` limits stay at or below 120 characters per line, 350 lines per file
and 6 function arguments. Every existing `gdscript/warnings/*` setting in
`project.godot` must keep at least its recorded level. This prevents quality
gates from becoming weaker to accommodate a change.

- Good setting: `max-line-length: 120`
- Bad setting: `max-line-length: 160`

Restore the limit or warning level and fix the code it reports. Missing
required settings must be restored too.

## 11. no-todo

No `.gd` or `.py` file may contain `TODO`, `FIXME`, `HACK` or `XXX`. Finish the
work now or record deferred work in an issue so the source stays clear.

- Good completed line: `return economy.try_spend(player, cost)`
- Bad deferred line: `return true # TODO: check the player's balance`

Implement the missing behavior and test it, or open an issue and remove the
unfinished marker without pretending the behavior exists.

## 12. warning-ignore-reason

Every `@warning_ignore` must have a same-line comment explaining why ignoring
that warning is correct. A local reason makes exceptions reviewable.

- Good: `@warning_ignore("integer_division") # Whole magazines intentionally discard partial rounds.`
- Bad: `@warning_ignore("integer_division")`

Fix the warning when possible; otherwise add a concrete reason on the
annotation's own line.

## 13. doc-comment

Every `.gd` file in `core/` and `systems/` needs a `##` doc comment within its
first five lines. One short description makes the script's job easy to find.

- Good opening line: `## Holds one player's spendable match points.`
- Bad opening line: `# Holds one player's spendable match points.`

Add or move a short `##` description into the first five lines.

## 14. no-triple-copy

In tracked text files in game code and `tools/`, a block of eight or more
consecutive code lines cannot occur in three places after trimming each line's
surrounding whitespace and ignoring blank and full-line comments. Scenes and
resources count too; adding spacing or comment lines cannot hide a copy.
Tests and Godot's `.import` sidecars (written by the engine) are excluded.
Two copies are fine; the third is evidence for sharing.

- Good third use: `apply_shared_visuals(mesh)`
- Bad third copy's opening line: `material = StandardMaterial3D.new()`

The bad example means copying the same eight-line material setup a third
time. CI reports every matching place. Extract the repeated operation into
its existing owner and call it from those places; do not disguise copies with
formatting or comments.

## 15. tested-scripts

Every `.gd` in `core/` and `systems/` must have its filename stem or
`class_name` mentioned in a file under `tests/`. The initial eight exceptions
live in `tools/ci/untested_baseline.txt`; no new paths may be added. A baseline
entry also fails when the script becomes tested or disappears, so exceptions
can only shrink.

For `wallet.gd`, whose class is `Wallet`:

- Good test line: `var subject: Wallet = Wallet.new()`
- Bad unrelated test line: `assert_eq(2 + 2, 4)`

Add a useful test covering the reported script. If CI says to remove a stale
baseline entry, remove that line from the baseline instead of changing the
test or adding another exception.

## 16. ui-router-only

Screens and the mouse have one owner, the `UI` autoload (ADR 0011). In
`core/`, `systems/` and `levels/`, calls to `change_scene_to_file` or
`change_scene_to_packed` and assignments to `Input.mouse_mode` are allowed only
in `core/ui.gd`. Reading `Input.mouse_mode` is fine, and tests and tools are not
checked.

- Good: `UI.replace(&"main_menu")`, `UI.push(&"settings")`, `UI.hold_mouse(self, open)`
- Bad: `get_tree().change_scene_to_file("res://systems/ui/main_menu.tscn")`

Open a screen with `UI.push` (a scene with `signal closed` plus one
`content/screens/<id>.tres`), go to a root place with `UI.replace`, and let a
panel that is not a screen ask for the mouse with `UI.hold_mouse`.

## 17. no-content-id-literals

Code picks behaviour from a field on the data, never from a content id, so a
new `.tres` works without a code edit (foundation 2). Any string or
`StringName` literal in `core/` or `systems/` that equals the file name of a
weapon, enemy, serum, power-up, gear visual, loot gear base, grip, melee
weapon, skill or wave file fails. Comments are ignored. Left out on purpose: affixes (their ids
are also stat keys code must name), rarities and rarity looks (a fixed ordered
rule), singletons loaded by one name (economy, progression, stat caps) and UI
screens (screen flow is code).

- Good: `if data.effect == WeaponData.Effect.WELL:`
- Bad: `if data.id == &"siphon":`

Known leftovers live in `tools/ci/content_id_baseline.txt` as `path: id`
lines. The checker also holds the first list, so no new pair can be added, and
a pair that no longer appears must be deleted from the file. Fix a finding by
adding a field to the data type (see `docs/HOW_TO_ADD.md`), not by adding a
baseline line.

## 18. decisions-short

Every list entry in `docs/DECISIONS.md` is one line of at most 300 characters,
so agents can read the entries for their systems without wading through build
notes. Detail goes in the linked plan, ADR or doc. A line that does not start
with `- ` directly under an entry (a wrapped or nested line) fails.

- Good: `- **Range falloff** uses start and end distances, not a Curve. Fix when: a gun needs a curve.`
- Bad: an entry that wraps onto a second line, or a paragraph of build notes.

Cut the entry to what a future agent must not undo, and link the plan for the rest.

## 19. rpc-rules

Co-op messages keep one shape (foundation 1; patterns in `docs/MULTIPLAYER.md`
"Writing co-op code"). In game code:

- Every `@rpc(...)` names its mode (`"authority"` or `"any_peer"`) and its
  transfer mode (`"reliable"`, `"unreliable"` or `"unreliable_ordered"`).
  Godot's default transfer is unreliable, a silent trap for state.
- The first code line of an `"any_peer"` RPC's body contains
  `multiplayer.is_server()`. A signature over several lines, blank lines and
  comments before it are skipped. The check comes before reading the sender.

- Good:

  ```gdscript
  @rpc("any_peer", "call_remote", "reliable")
  func _request_open(path: NodePath) -> void:
  	if not multiplayer.is_server():
  		return
  ```

- Bad: `@rpc("any_peer")`, or a handler that starts with
  `var sender: int = multiplayer.get_remote_sender_id()`.

## 20. log-catalogue

Every `Log.warn(&"<system>", &"<event>", ...)` in `core/` and `systems/` whose
event is written as a literal must have its event name in `docs/LOGGING.md`
(the event catalogue), so an agent reading a log can look it up. Events passed
as a variable (`Log.warn(&"net", event, ...)`) are not checked; list every value
they can take in the catalogue by hand.

- Good: `Log.warn(&"net", &"join_failed", {...})` with a `net.join_failed` row.
- Bad: a new `Log.warn` event with no row in `docs/LOGGING.md`.

## 21. instance-children-editable

A scene that adds or changes nodes inside an instanced scene or model, such as
a muzzle flash under `Rifle/Receiver/Muzzle` of an imported `.glb`, or a
changed property on the model's `Receiver`, must mark that instance
`[editable path="Rifle"]`. Without it the editor runs the scene fine but the
exported game drops those nodes and changes: v0.1.2 shipped with a black MR-28
scope, no AR-17 red dot and no muzzle flashes. Nodes added straight under the
instance's root are kept.

- Good: `[editable path="Talon"]` at the end of `talon_viewmodel.tscn`.
- Bad: `[node name="ScopeLens" parent="Talon/Receiver/ScopeLensMount"]` with no
  `[editable path="Talon"]` line.

Fix: add the line at the end of the scene, or open the scene in the editor and
tick Editable Children on the instance. `tools/ci/export_content_check.gd` also
checks the exported build keeps every gun's flash, scope lens and red dot.
