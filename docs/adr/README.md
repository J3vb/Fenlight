# Decision records

One short file per big technical choice, so nobody (human or agent) goes
against it by accident. `docs/DECISIONS.md` lists the small differences,
simplifications and provisional picks, one line each; these files hold the big
rules.

## When to write one

Write a new record **before** the code when a change:
- picks or replaces a core technology, pattern or file format,
- changes who decides what in co-op,
- changes a foundation in `docs/FOUNDATIONS.md`,
- goes against an existing record.

Small choices inside one feature belong in its plan, not here.

## How

1. Copy `TEMPLATE.md` to `NNNN-short-name.md` with the next number.
2. Keep it under a page. Plain words.
3. Add it to the list below.
4. To change a decision, write a new record and set the old one's status to
   "Replaced by NNNN". Never rewrite an accepted record.

Status: **accepted** (follow it), **proposed** (agent pick, the person can
change it), **replaced** (see the newer record).

## Records

| # | Decision | Status |
|---|---|---|
| [0001](0001-godot-typed-gdscript.md) | Godot 4 with typed GDScript, no C# | accepted |
| [0002](0002-content-as-resources.md) | Content is Resource data, id = file name | accepted |
| [0003](0003-trusted-client-co-op.md) | Trusted-client co-op, server owns shared state | accepted |
| [0004](0004-one-code-path.md) | One code path: solo is a server with one player | proposed |
| [0005](0005-local-versioned-saves.md) | Characters saved on the player's PC as versioned JSON | accepted |
| [0006](0006-self-hosted-servers.md) | Self-hosted dedicated servers, no accounts or anti-cheat | accepted |
| [0007](0007-signals-and-events.md) | Signals up, Events for facts, direct calls for requests | accepted |
| [0008](0008-code-built-assets-first.md) | Code-built assets first, asset packs later | accepted |
| [0009](0009-ci-is-the-gate.md) | CI is the merge gate, keep it simple | accepted |
| [0010](0010-personal-loot-kept-on-death.md) | Personal loot, kept on death, no trading in v1 | accepted |
| [0011](0011-one-ui-router.md) | One UI router owns screen flow and the mouse | proposed |
| [0012](0012-updates-and-release-channels.md) | Exact versions, a built-in launcher, self-updating servers | proposed |
| [0013](0013-every-game-joinable.md) | Every game is joinable; alone means solo | proposed |
| [0014](0014-baked-gun-textures.md) | Guns may use baked texture maps, 30,000-triangle budget | accepted |
| [0015](0015-baked-player-body.md) | The player body may use baked texture maps | accepted |
| [0016](0016-baked-town-npcs.md) | Town NPC bodies may use baked texture maps | accepted |
| [0017](0017-tripo-models.md) | Models made in Tripo may go in assets/ | accepted |
| [0019](0019-supplied-2d-menu-art.md) | Supplied painted art may go in assets/ui/ as menu backdrops | accepted |
| [0020](0020-shared-weapon-surface-detail.md) | One shared surface tile for weapon finishes | proposed |
