# Roadmap: what we build, in what order

The order of upcoming features and what each one waits on. Phases P0-P10 and
milestone gates come from `docs/design/game-design.md` (Build roadmap) and
`docs/PROCESS.md`. The issues hold the details; this file holds the order.

## Rules

1. Work top to bottom. Start a feature only when everything in its
   **Needs** column is Done.
2. A feature with **Plan: needed** starts with a plan
   ([docs/plans/README.md](plans/README.md)). No approved plan, no code.
3. **Plan: issue** means the Task issue is enough (one PR, follows a recipe).
4. Foundation fixes (F-00) go before new features that touch the same system.
5. When a feature finishes, set its Status to Done in the same PR. New
   features get a new row in the right place, with the next free id.

The game is in **Early Alpha** (shown in the main menu version label).
v0.2 features may start before the v0.1.0 tag (the person's call, 2026-11-20): read F-11 in their Needs as F-10.

Status values: Todo, Planning, Ready (plan approved), Building, Done, Check
(may already be done, verify and close).

## Now: foundations and v0.1 Vertical slice

| Id | Feature | Issue | Needs | Plan | Size | Status |
|---|---|---|---|---|---|---|
| F-00 | Foundation fixes, in the ranked order of [FOUNDATIONS.md](FOUNDATIONS.md#foundation-fixes-in-order) | - | - | per fix: 1 (done, no plan: one CI PR), 2 = F-02 (done), [3](plans/item-effects-server.md) (done), [4](plans/ids-into-data.md) (done), [5](plans/ui-router.md) (done), 6 (done, no plan: one PR per issue), [7](plans/hot-path-allocations.md) (done), 8 (done, no plan: one test-only PR per issue), 9 (done, no plan: doc lines plus a test) | - | Done |
| F-79 | Easy, safe changes: one written co-op pattern with CI checks (foundation 1), short agent docs (foundation 13), then the picked audit fixes (split the 350-line scripts, one co-op test side, model list from the registry) | - | - | [ready](plans/easy-changes.md) | L | Ready |
| F-01 | First-person arms on the guns | #102 | - | issue | S | Done (PR #136 fitted arms, sleeve fix) |
| F-02 | Co-op clients can use doors, wall-buys and machines | #138 | F-00 | [done](plans/coop-interactions.md) | M | Done (play-test: #191) |
| F-03 | Player footsteps and landing sounds | #103 | - | issue | S | Done |
| F-04 | Halcyon Labs ambience | #104 | - | issue | S | Done |
| F-05 | Rebind controls in Settings | #105 | - | [done](plans/control-rebinding.md) | M | Done |
| F-06 | Make the rounds 1-10 soak test a required CI check | #107 | - | issue | S | Done (branch rule: add `soak`) |
| F-07 | Balance pass rounds 1-10 for the slice guns | #106 | F-06 | issue | S | Todo |
| F-08 | Change log in the design doc | #110 | - | issue | S | Done |
| F-12 | Core loop gaps: round scaling, stuck zombies, swap, melee, slide, best round | - | - | [needed](plans/core-loop-gaps.md) | M | Done |
| F-13 | Finish Halcyon Labs: props, co-op spawn points, vent route, secret | - | - | [done](plans/halcyon-labs-finish.md) | M | Done (look follow-ups #297) |
| F-62 | Texture every surface in Halcyon Labs: textured sets, a floor per room, decals | - | - | [done](plans/halcyon-surfaces.md) | M | Done |
| F-14 | Zombie sounds and gore: steps, deaths, voice caps, blood, head pops | - | - | [done](plans/zombie-sounds-gore.md) | M | Done (play-test: #191) |
| F-15 | Halcyon Labs detail props: Blender models for every room prop, story clutter, barricades | - | - | [ready](plans/halcyon-labs-props.md) | M | Done |
| F-63 | Halcyon Labs door models: bulkheads, debris, shutters, vent grates, freezer door | - | - | [done](plans/halcyon-doors.md) | S | Done |
| F-64 | Halcyon Labs wall-buy racks (gun on the wall) and Specimen Vault model | - | - | [done](plans/halcyon-wall-buys-vault.md) | S | Done |
| F-68 | Halcyon Labs concept pass after the breakout: signage, Fenlight vines, wrecked rooms, ceilings, #297 look lines (stays dark) | #297 | - | [done](plans/halcyon-concept-pass.md) | L | Done |
| F-61 | Halcyon Labs atmosphere: dead and flickering lights, particles, fog, beacons, screens, sound spots, story decals | - | - | [ready](plans/halcyon-labs-atmosphere.md) | M | Done |
| F-16 | Game feel: camera punch, hitstop, downed and death screen | - | - | [ready](plans/game-feel-slice.md) | M | Done |
| F-65 | Client and server updates: clear version refusals, saves safe across channels, a launcher that installs and updates the game and a server, self-updating Docker servers (steps 1-5 before F-11) | - | - | [ready](plans/client-server-updates.md) | L | Building |
| F-09 | v0.1 performance check | #108 | F-01..F-07, F-12, F-13, F-16 | issue | S | Todo |
| F-10 | First play-test (the person plays) | #109 | F-09 | issue | S | Done (solo play-test 2026-11-19, fixes in F-84, F-85) |
| F-82 | Separate launcher program (like Steam or Battle.net): installs and updates the game, updates itself, news and patch notes, hosts a server; replaces the launcher built into the game (F-65 steps 5-6, 9) | - | F-65 step 4 | [ready](plans/separate-launcher.md) | L | Building |
| F-11 | Release v0.1.0 | #111 | F-10, F-65 steps 1-4, F-82 steps 1-4 | issue | S | Done (released 2026-11-22, first stable) |
| F-91 | Performance pass: one fps benchmark, baseline on the person's PC, fix only the measured hotspots (draw calls, AI frame-skip at the 66-zombie co-op cap), upscaler defaults, regression report in CI | - | - | [ready](plans/performance-pass.md) | M | Ready |
| F-40 | Round state and power-ups in co-op (rest of #126 after F-02) | #126 | F-02 | [done](plans/coop-round-state-power-ups.md) | M | Done |
| F-47 | A full co-op match: co-op soak, pause, squad cards, hub and deploy flow | #213 | F-40 | [plan](plans/coop-full-match.md) | L | Done |
| F-48 | Full settings screen: Graphics page with presets, then Accessibility and Comfort | - | F-05 | [done](plans/full-settings.md) | L | Done |
| F-49 | HUD feedback and loading: loading screen, damage numbers, level-up burst, drop feed | - | - | [done](plans/hud-feedback-loading.md) | M | Done |
| F-50 | First Lantern Post hub: town blockout, Deploy board and ready-up vote (first slice of F-45, pulled forward for the co-op week goal) | #131 | F-02, F-47 step 4 (#255), co-op #256 | [done](plans/lantern-post-hub.md) | M | Done |
| F-66 | Your own world, open to friends: Enter world into your own Lantern Post (listen server, UPnP), server browser with add by address and LAN discovery, no master server | - | F-02, F-50 | [ready](plans/join-any-game.md) | L | Done |
| F-67 | Character select before Enter world: pick a preset survivor with a bio and 3 traits (ui-hud screen 3, concept art 2026-11-17) | - | F-66 step 2 | needed | M | Todo |
| F-81 | Players set their own in-game name on the Character screen; teammates see it in co-op | - | F-66 | [done](plans/player-names.md) | S | Done |
| F-74 | Lantern Post to the concept art: ridge sky, timber lodges, market stalls, concrete Deploy gate, props | - | F-50 | [done](plans/lantern-post-concept.md) | L | Done |
| F-76 | Lantern Post vendors: the four stall keepers (Quartermaster, Gunsmith, Technician, Cordon liaison) as code-built NPCs with idle clips, head turn and talk lines; shop screens stay in F-45 | - | F-74 step 3 (#338), F-70 step 1 (#337) | [ready](plans/lantern-post-vendors.md) | L | Building |
| F-77 | Shared prop library for future maps: about 75 code-built props in eight families (barriers, military, industrial, rail, large pieces, hospital, outdoor, map hero pieces) plus a catalogue, so Act I maps and towns are assembly, not modelling | - | - | [ready](plans/prop-library.md) | L | Building |
| F-78 | Tripo model trial: one Tripo prop and one vendor through a new intake (decimate, bake our three maps, fit our 22-bone skeleton, existing clips), side by side with code-built, report so the person can pick how F-76 and F-77 are made | - | - | [ready](plans/tripo-trial.md) | M | Ready |
| F-80 | Props and vendors made in Tripo: Tripo API tool with manifests and image prompts, ADR for Tripo models, F-76 vendors and F-77 prop families built from Tripo instead of Blender scripts | - | F-78 | [ready](plans/tripo-models.md) | L | Building |
| F-83 | Halcyon Labs machine models (Med Dispenser, Reforger, power switch, exfil hatch) from Tripo, about 12 Tripo room props in the bare rooms, and small life (fan, drips, PA crackle) | - | F-80 step 2 | [ready](plans/halcyon-machines-fill.md) | L | Building |
| F-70 | Player and gear to the concept art: bearded survivor body, headgear, gloves, backpack and boots models in three tiers (field, plated, Oriel), plate carrier vests, eye implant and vest vial | - | - | [ready](plans/player-gear-concept.md) | L | Building |
| F-71 | Four new loot slots: headgear, gloves, backpack, boots (item bases, affix pools, drops, sets, save, inventory and character screen) | - | - | [done](plans/four-gear-slots.md) | M | Done |
| F-84 | Wear loot gear mid-run: Tab Pack overlay shows your character and gear slots, E wears a picked-up vest, charm or implant (solo play-test 2026-11-19) | - | - | [ready](plans/wear-gear-mid-run.md) | M | Building (all 3 steps merged; play-test left) |
| F-72 | The four starter guns to the concept art: worn black with tan and brass, Oriel marks, red dots, taped mags (rifle, Brenner, Kestrel, Talon) | - | - | [done](plans/guns-concept.md) | M | Done |
| F-73 | Weapon stats panel: five bars (damage, fire rate, accuracy, range, control) computed from WeaponData, on wall-buys, the Vault and the inventory (look: [guns_concept.jpg](design/images/guns_concept.jpg)) | - | F-72 | needed | M | Todo |
| F-75 | Baked texture maps for the four concept guns: high-detail bake (bevels, stipple, engraved marks, wear), 30,000-triangle gun budget, Forward+ lit previews, intake for handed-over .glb guns | - | F-72 step 2 (per gun: its F-72 step) | [ready](plans/baked-gun-textures.md) | L | Building (steps 1-2; 3-6 after the AR-17 look) |
| F-85 | Real reload animations: left hand swaps magazines, bolt catch on empty reloads, BR-12 loads shell by shell, sounds on each move (solo play-test 2026-11-19) | - | F-72 | [done](plans/reload-animations.md) | M | Done |
| F-87 | HUD to the FENLIGHT concept art: angled health/stamina and gun/ammo/frag panels, Serum slots with icons, compass, ROUND counter, pickup prompt on the object (concept art 2026-11-20) | - | - | [ready](plans/hud-concept.md) | M | Building (all 5 steps built; play-test left) |
| F-89 | Real sounds and music instead of the generated placeholders: free packs (Sonniss, Kenney, Freesound CC0) and Stable Audio music, intake tool, licence log, audition pages to pick by ear (play-test 2026-11-20) | - | - | [ready](plans/real-sounds-music.md) | L | Ready |

## Next: v0.2 Progression and loot

| Id | Feature | Issue | Needs | Plan | Size | Status |
|---|---|---|---|---|---|---|
| F-88 | Front-end screens to the concept art: FENLIGHT logo, brush-stroke menu, painted main menu and Loadout backdrops, Loadout tabs (concept art 2026-11-20) | - | - | [ready](plans/front-end-concept.md) | M | Building |
| F-20 | Skill effects (through the stat stack) | #113 | F-11 | [ready](plans/skill-effects.md) | M | Done |
| F-21 | Skill tree screen (look target: [research_concept.jpg](design/concepts/screens/research_concept.jpg)) | #112 | F-20 | [done](plans/skill-tree-screen.md) | M | Done |
| F-90 | More skill nodes: about 5 per branch so each holds about 30 points, keystone and capstone gates back to 15 and 25 (the person's pick 2026-11-20) | - | F-21 | needed | M | Todo |
| F-22 | Field abilities | #114 | F-20 | [ready](plans/field-abilities.md) | L | Done |
| F-23 | Levelling pace check | #115 | F-20, F-22 | issue | S | Todo |
| F-24 | Frag grenades | #119 | F-11 | [ready](plans/frag-grenades.md) | M | Building (all 4 steps merged; play-test left) |
| F-25 | Mantle | #120 | F-11 | [ready](plans/mantle.md) | M | Building |
| F-26 | More power-ups in the drop deck | #118 | F-11 | [needed](plans/more-power-ups.md) | M | Done |
| F-27 | Crawler | #121 | F-24 | needed | M | Todo |
| F-86 | Existing zombies (Shambler, Crawler, Bloater) to the person's Tripo models, same poses, hit zones and gore | - | F-28 step 1 | [done](plans/tripo-zombies.md) | M | Done |
| F-28 | Blackout rounds and Glowers | #122 | F-11 | [ready](plans/blackout-glowers.md) | M | Building |
| F-29 | Stalker | #123 | F-11, F-28 | [ready](plans/stalker.md) | L | Ready |
| F-30 | Brute | #124 | F-11, F-29 | [ready](plans/brute.md) | L | Ready |
| F-31 | Legendaries and traits | #116 | F-20 | [done](plans/legendaries-traits.md) | L | Done |
| F-32 | Item sets (needs set lore first); a set is the five armour pieces: headgear, vest, gloves, backpack, boots (F-71) | #117 | F-31, F-71 | needed | M | Todo |
| F-90 | More Legendaries: Furnace (needs burning), Overkill and Overclock (renames first, Overclock needs F-22), Gambler's Coin, Dead Man's Hand stagger, the 9 new-base traits from gun-roster.md | - | F-31 | needed | L | Todo |
| F-33 | Run length target: solo runs end between round 15 and 30 | #125 | F-27..F-30 | issue | S | Todo |

## Later: v0.9 Alpha

| Id | Feature | Issue | Needs | Plan | Size | Status |
|---|---|---|---|---|---|---|
| F-41 | Third-person walk, run and downed animations | #128 | F-11 | [needed](plans/teammate-animations.md) | L | Done |
| F-42 | Gear in first person | #129 | F-84 (F-11 waived 2026-11-20, see plan) | [done](plans/gear-first-person.md) | M | Done |
| F-43 | 4-player play-test to round 20 | #127 | F-47, F-41 | issue | S | Todo |
| F-44 | Finish the server package | #130 | F-43 | needed | L | Todo |
| F-45 | Town hub Lantern Post (split into features when it starts) | #131 | F-44 | needed | L | Todo |
| F-46 | Dyes | #132 | F-42 | needed | M | Todo |

## After v1.0: Growth (P10)

| Id | Feature | Issue | Needs | Plan | Size | Status |
|---|---|---|---|---|---|---|
| F-60 | Campaign: acts, descents and bosses (story in [lore.md](design/lore.md#the-long-campaign); split per act when it starts, first the Halcyon Labs Sublevel boss) | - | F-45, F-31 | needed | L | Todo |

## Notes

- v0.2 features after F-11 may run in parallel when their Needs are Done and
  they touch different systems.
- F-40 and F-47 were pulled into Now on 2026-11-17: the person set co-op as
  the goal for that week. They touch only co-op code, not the v0.1 rows.
- Loot and co-op were partly built before v0.1 shipped (see
  `docs/plans/` and `docs/MULTIPLAYER.md`). From here on, the order
  above is the order.
