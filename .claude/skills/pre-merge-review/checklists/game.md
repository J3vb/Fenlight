# Game code (GDScript, scenes, data)

1. **Server only.** Damage, health, spawns, points, XP and items change only
   behind `multiplayer.is_server()` (true in solo). Can any path change them
   on a client? Is `Net.is_authority()` used only where there is no node?
2. **No local player assumed.** A dedicated server has no local player,
   camera, HUD or sound. Does the code loop over the `players` group, and
   work with 1 and with 8 players?
3. **Freed and stale references.** A stored enemy, player or node used after
   `queue_free()`, after an `await`, or in a later frame without
   `is_instance_valid`. State assumed unchanged across an `await` (round
   ended, player left, node freed).
4. **Signals.** Connected twice (re-entered `_ready`, reused node), never
   disconnected from a longer-lived object (`Events`), or a handler that
   runs on every peer when it should run on one.
5. **Runs twice or never.** Can the action fire twice (two quick presses, a
   timer and a signal, two players in the same tick)? Is every flag reset on
   every way out: early return, death, downed, disconnect, round restart?
6. **Physics tick.** Gameplay in `_physics_process`, visuals in `_process`.
   Anything that depends on frame rate or misses `delta`?
7. **Randomness and order.** Gameplay uses `GameSession.rng`; `# cosmetic`
   only on real cosmetics. No `Array.sort()` on StringNames (use
   `Content.sorted_ids()` or a `PackedStringArray`).
8. **Loaded `.tres` never changed.** Any write to a loaded Resource, its
   arrays or its sub-resources at runtime? Live state belongs in an instance
   object such as `WeaponInstance`.
9. **Hot paths.** Per-frame arrays, dictionaries, strings or lambdas;
   `get_node()`, `find_child()`, group lookups or `load()` in a loop or in a
   tick. Count the cost with 24 zombies and 8 players.
10. **Types and numbers.** `as` casts that give null silently, integer
    division, empty array picked from, divide by zero, off-by-one on round
    or index, round 1 and very high rounds, negative or zero amounts.
11. **Input.** Players read `InputFrame`s, never `Input` directly. Behaviour
    when the window loses focus and the game pauses.
12. **Saved data.** A new, renamed or removed saved field or content id: do
    old saves still load (ADR 0005)?
13. **Files.** No editor-churned `project.godot`, no `.tscn` / `.tres` changed
    by accident, no editor-local uids, no hand-edited generated output, new
    files have their `.uid` / `.import` sidecars.
14. **Tests.** Does each new test fail without the change, use a fixed seed,
    and check behaviour, not only "no crash"? New early warnings have a
    `Log.warn` and a row in `docs/LOGGING.md`.
15. **Simple.** Nothing built for a later phase, no dead code left, no
    manager that only forwards, no number hard-coded that the balance data owns.
