# Plan: Shared prop library for future maps

Status: Review
Roadmap: F-77
Phase: art track ahead of the Act I maps (Kessel Dam is next in the maps.md build order)
Size: L
Approved by: first version: the person on a decision card (2026-11-18, scope: kit plus map hero pieces); plan review on PR #342. This Tripo rewrite: waiting for review and the person's card.
Lore link: docs/design/lore.md "Maps, rooms and props": shared library props are generic kit whose story comes from where a map places them (Day 3 evacuation convoy, evacuation train, 1950s sanatorium stock); marks use lore names (Oriel, the Cordon).

## Goal

A ready-made library of props, so building Kessel Dam, Marrow Junction,
Grauwald Sanatorium and later towns is placing models in `layout.json`, not
modelling first. Props are generic kit pieces that fit more than one map
(barriers, vehicles, pipes, rail pieces, hospital furniture, trees and rocks)
and look like the Act I key shots. Serves "The pressure always builds"
(readable cover and lanes) and keeps map building fast and cheap.

Measurable: 48 Tripo models and 9 code-built models land in families 1-8,
each family board approved by the person, for about 3,000 Tripo credits.

### What changed in this rewrite (2026-11-20)

The person moved library props to Tripo on 2026-11-18 ("Everything to
Tripo", plan [tripo-models.md](tripo-models.md) step 4, ADR 0017). Steps 1
(catalogue, lineup tool, `props_large`) and 2 (11 code-built barriers,
#349) were built from the first version. Steps 3-9 were paused. This
rewrite fixes the blockers from the plan review
(`/mnt/project-files/egm-review/plans/prop-library-review.md`):

- Each piece is now marked **Tripo** or **code-built** (table below).
  Snap-together pieces with exact sizes, thin open frames and walk-through
  shells stay code-built (ADR 0017: "code-built models stay where Tripo is
  weak").
- Glowing parts get small lamp overlays in the intake (a second, shared
  `Beacon` or `Bulb` surface), because the intake bakes no emission.
- A `dressing` intake kind (1,000 tris) for small clutter.
- A credit budget, a credit cap per family and a retry cap.
- Rebuild sources: the approved input image is committed next to its
  manifest row (the 45-50 MB Tripo source `.glb` is too big for git).
- Duplicates dropped (wheelchair, pine tree, snow drift, park bench reuse
  existing models).

## Scope

In:

- 48 Tripo models in eight families, each made from a manifest row in
  `tools/assets/tripo/<family>.json` with `tools/assets/tripo_make.py`:
  image first (Tripo text to image), the person approves the family's image
  sheet, then models, intake, catalogue rows and a lineup board the person
  approves.
- 9 new code-built models where Tripo is weak, in
  `tools/assets/library_<family>.py` like `library_barriers.py`.
- Remaking 7 of the 11 code-built barriers from #349 in Tripo (the chunky
  ones); the 4 thin or lamp-carrying ones stay code-built.
- Intake and tool changes in step 1 (below): `dressing` kind, lamp overlays,
  input image copied into the repo, credit cap and retry cap.
- The catalogue (`docs/design/prop-library.md`) and its check stay as built
  in step 1 of the first version; every new model gets a row with slots
  `Baked (Tripo)` or its shared slots.

Families. **T** = Tripo, **C** = code-built, **R** = reuse an existing model
(the catalogue row gets the family added, nothing is built).

| Family | Tripo (T) | Code-built (C) and reuse (R) | Suits |
|---|---|---|---|
| 1 Barriers and checkpoint | jersey_barrier, concrete_block, sandbag_wall, sandbag_corner, hard_case, pallet_stack, jerrycan_pair (dressing) | C (keep #349): boom_barrier, chain_link_fence, chain_link_gate, razor_wire_fence. R: props/barricade, props/military_cases | Kessel crest, Marrow gate, towns, Halcyon dock |
| 2 Military camp and vehicles | army_truck (props_large), armoured_car (props_large), field_tent, field_table, portable_generator, floodlight_tripod (lamp), body_tarp | R: props/crate_stack, props/military_cases, props/fuel_drum, props/supply_truck | Kessel crest, Marrow gate, towns |
| 3 Industrial | pipe_elbow_valve, electrical_cabinet, transformer, cable_reel, sodium_street_lamp (lamp), control_desk | C: guard_rail_3, guard_rail_6, wall_ladder. R: dressing/pipe_run_3, pipe_run_6 | Kessel, Marrow substation, Grauwald boiler room |
| 4 Rail | buffer_stop, signal_post (lamps), container_closed, container_open, flatbed_wagon (props_large), platform_bench, station_sign, luggage_pile (dressing) | C: track_section | Marrow, later rail maps |
| 5 Large pieces | container_stack (props_large) | C: hospital_train_car, last_car_glow, signal_gantry | Marrow, towns |
| 6 Hospital and sanatorium | hospital_bed, iv_stand, medical_trolley, privacy_screen, glass_cabinet, bathtub, reception_desk, chapel_pew, wall_radiator | R: props/wheelchair (F-83 Tripo), props/covered_gurney | Grauwald, Halcyon med rooms, town clinic |
| 7 Outdoor and clutter | dead_tree, rock_cluster, iron_gate (lamps), trash_bags (dressing), cardboard_boxes (dressing) | C: iron_fence, leaf_litter (dressing). R: town/pine_tree, town/bench, town/snow_drift_a, town/snow_drift_b | Grauwald, Kessel, Marrow, towns |
| 8 Map hero pieces | frozen_fountain, turbine_housing, dam_control_building (lamps), sanatorium_front, sanatorium_cupola (all props_large) | none | Grauwald courtyard and backdrop, Kessel Turbine Hall and crest |

Why each code-built piece is code-built (one line each):

- guard_rail_3/6, track_section, iron_fence: snap end to end on a fixed grid
  (1 m grid, 1.435 m gauge, 6 m track, 3 m fence); Tripo scales by one
  dimension and does not give clean, matching ends.
- chain_link_fence, chain_link_gate, razor_wire_fence, wall_ladder,
  signal_gantry: thin open frames; Tripo closes the gaps into solid blobs
  and the 2,000-tri decimation eats thin bars.
- hospital_train_car, last_car_glow: hollow walk-through shells (Marrow's
  train chokepoint); Tripo gives a closed mesh. The green glow is the
  bio-green experiment (look rule 2), on the shared slot.
- boom_barrier: its red tip lamp already uses the `Beacon` slot and the
  board was approved (2026-11-18).
- leaf_litter: a flat dressing patch, a few quads; Tripo adds nothing.

Not in (non-goals, and where each one goes instead):

- Map hero pieces beyond the five in family 8 (each map's build adds its own
  if it needs more).
- Placing props in any map, or new map layouts (each map's own F-row).
- Snow or rain on props as variants: props stay clean; snowy maps add the
  existing `town/snow_drift_a/b` dressing.
- Animated or moving props (the boom barrier that opens, the shunting loco):
  built with their map event.
- Text and marks from Tripo: never (ADR 0017). Signs and marks are our own
  `Label3D` or decal placed by the map. Models that need one: station_sign
  (blank board), army_truck and armoured_car (Cordon mark), hospital_train_car
  (see Open decisions).
- LODs, atlases and visibility ranges: only when a map's perf capture asks
  for them (`docs/design/maps.md#performance-budget`).
- Moving the Halcyon Labs props, kit or doors to Tripo.

## Ready to build

```
### Ready to build
- Foundations touched: 11 Asset pipeline (solid: tripo_make.py, tripo_intake.py,
  build_models.py, check_models.py, glTF validator, turnarounds), 9 Tests and CI (solid).
- Decision records: 0017 Tripo models (this plan follows it; step 1 adds one line to its
  Consequences for lamp overlays and the committed input image), 0008 for the code-built
  pieces. Goes against one: no.
- Co-op:
  - Who decides: nobody; props are static scenery in each map's blockout, identical on every peer.
  - How a client triggers it: n.a. (no interaction).
  - What other players see: the same scene; nothing is sent.
  - Works on a dedicated server with no local player: yes (meshes load, colliders as boxes).
- Data: no Resource type. Model names live in layout.json per map, in the catalogue and in the
  manifests. Code compares against a specific id: no.
- Save: no change. Renames or removes a saved id: no.
- Events and UI: none.
- Input through InputFrame, gameplay in _physics_process, session RNG: n.a. (no runtime code).
- Tests: test_tripo_intake.py and test_tripo_make.py (step 1), check_models.py budgets,
  test_prop_catalogue.py, test_prop_models.gd, test_library_barriers.gd, turnarounds.
- Logging: none (offline tools print a credit summary).
- Performance: nothing created at run time. Budgets and texture cost below.
- Out of scope: as listed under "Not in".
```

## Design references

- `docs/design/maps.md`: Kessel Dam, Marrow Junction and Grauwald Sanatorium
  "Key props" lists, "Performance budget".
- Key shots: `docs/design/concepts/act1/keyshots/kessel_dam.jpg`,
  `marrow_junction.jpg`, `grauwald_sanatorium.jpg`.
- `docs/design/look-rules.md`: palette, rules 2-5 (bio-green only on the
  experiment, red only on lamps).
- `docs/design/tripo-prompts.md`: style line and one prompt per model.
- `docs/design/reviews/tripo-trial/README.md`: what Tripo does well and badly.
- `docs/plans/tripo-models.md` step 4, `docs/plans/halcyon-machines-fill.md`
  (credit costs measured: text to image 5 credits, image to model with
  detailed texture 40 credits).
- `docs/adr/0017-tripo-models.md`, `docs/adr/0008-code-built-assets-first.md`.
- Budgets from `tools/assets/check_models.py`: props 2,000 tris / 4
  materials, dressing 1,000 / 4, props_large 12,000 / 6.

## Systems touched

| Folder or file | New / changed | What changes |
|---|---|---|
| tools/assets/tripo_intake.py | changed (step 1) | `dressing` kind; `lamps` overlay surfaces |
| tools/assets/tripo_make.py | changed (step 1) | copies the input image into the repo; `--max-credits`; at most 2 model tries per row |
| tools/assets/tests/test_tripo_intake.py, test_tripo_make.py | changed (step 1) | tests for the above |
| tools/assets/tripo/images/<family>/*.jpg | new | approved input images (about 120 KB each) |
| tools/assets/tripo/<family>.json | new / changed | one manifest per family (military.json exists, rows get prompts) |
| tools/assets/library_barriers.py | changed (step 2) | the 7 remade builders deleted, 4 stay |
| tools/assets/library_industrial.py, library_rail.py, library_large.py, library_outdoor.py | new | code-built pieces |
| tools/assets/build_models.py | changed | merges each new library's `MODELS` |
| tools/assets/prop_import.gd | changed (step 1) | unused `Tile`, `Enamel`, `Ice` slots deleted (the `.tres` stay where floors use them) |
| tools/turnarounds.py | changed (step 1) | `props_large` reference image |
| tests/content/test_prop_models.gd | changed (step 3) | a Tripo prop may add one shared lamp slot |
| tests/content/test_library_barriers.gd | changed (step 2) | 7 rows expect `Baked` |
| assets/models/props/, dressing/, props_large/ | new files | `.glb`, `.glb.import`, 3 map `.jpg` + `.import` per Tripo model |
| docs/design/turnarounds/ | new files | approved turnarounds |
| docs/design/prop-library.md | changed | catalogue rows |
| docs/design/prop-library/*.jpg | new | one lineup board per family |
| docs/design/tripo-prompts.md | changed | code-built rows removed, names match the files |
| docs/adr/0017-tripo-models.md | changed (step 1) | one Consequences line: lamp overlays, committed input image |

Autoloads, managers or base classes added: none. A shared `library_parts.py`
only once a third code-built family needs the same helper (Keep it simple
rule 2).

## Data

- No Resource types, no save fields, no network messages.
- Manifest row (JSON, tools only), as today plus two optional keys:
  `{"name", "folder", "kind", "height" | "length", "yaw", "prompt",
  "image", "task_id", "source", "made", "tries", "lamps"}`.
  `lamps` is a list of `{"at": [x, y, z], "size": m, "slot": "Beacon" | "Bulb"}`
  in model space after intake; `tries` counts paid model attempts.
- Rebuild sources, in order: the source `.glb` in
  `/mnt/project-files/tripo/sources/<family>/`; else Tripo again by
  `task_id` (no new credits while Tripo keeps the task); else a new model
  from the committed image in `tools/assets/tripo/images/<family>/` (40
  credits, close but not identical).
- `layout.json` props and dressing: unchanged (`"model": "props_large/<name>"`
  already works from step 1).
- Save format change: none.
- Content checks: the existing `tests/content/test_prop_models.gd` loads every
  model in props/, dressing/ and props_large/.

## Co-op behaviour

- Who owns the state: nobody; static scenery.
- What clients send, what the server sends back: nothing.
- What a client sees that the host sees too: the same models, built into each
  map's blockout scene.
- Late joiner: nothing to receive; the scene is loaded with the map.
- Dedicated server: meshes load headless; colliders are the layout boxes.

## Performance

Nothing runs per frame. Each Tripo model is one mesh with its own `Baked`
material (plus at most one shared lamp surface), so it is one draw call per
placed copy and does not batch with other props. Texture cost per model:
props and dressing 3 maps at 1024 (about 4 MB video memory with mipmaps),
props_large 3 maps at 2048 (about 16 MB). A map that places 30 different
Tripo props and 5 large pieces uses about 200 MB of video memory for them;
the map's own perf capture decides on atlases or LODs if fps drops.

Repo size: about 1.4 MB per prop and 6 MB per large piece on disk, so the 48
models add about 110 MB to git (no LFS). Input images add about 6 MB.

## Credit budget

Tripo costs (measured in F-83): text to image 5 credits, image to model with
detailed texture 40 credits. Balance on 2026-11-20: 175 credits.

| Step | Family | Tripo models | Planned credits (45 each) | Cap (1.5x) |
|---|---|---|---|---|
| 2 | Barriers | 7 | 315 | 470 |
| 3 | Military | 7 | 315 | 470 |
| 4 | Industrial | 6 | 270 | 405 |
| 5 | Rail | 8 | 360 | 540 |
| 6 | Large | 1 | 45 | 70 |
| 7 | Hospital | 9 | 405 | 610 |
| 8 | Heroes | 5 | 225 | 340 |
| 9 | Outdoor | 5 | 225 | 340 |
| | **Total** | **48** | **2,160** | |

Rules every family thread follows:

- Images first, all at once (`tripo_make.py --images`, 5 credits each), then
  the image sheet goes to the person on a card. No model is paid for before
  its image is approved.
- At most 2 paid model tries per row (`tries` in the row, the tool refuses a
  third). After 2 bad tries the piece is code-built or dropped; the board
  card says which.
- `--max-credits <cap>` per run: the tool stops before a task that would pass
  the family cap. Going over the cap needs a new card.
- The PR lists credits spent per model (the tool prints them).

Planned total 2,160 plus retries and image redos: buy about 3,000 credits
(about $30 at $1 = 100 credits). Open decision below.

## Steps

One step = one PR, built in its own thread. Every Tripo family step:
manifest rows with prompts, image sheet card, models, `.import` files,
turnarounds approved, catalogue rows, lineup board, board card. The next
family may start its images while the last board waits.

How to add one Tripo model (every family step):

1. Row in `tools/assets/tripo/<family>.json` with `prompt` (from
   `tripo-prompts.md`), size, `folder`, `kind`, no `image`.
2. `python tools/assets/tripo_make.py tools/assets/tripo/<family>.json --images`;
   sheet to the person.
3. `python tools/assets/tripo_make.py tools/assets/tripo/<family>.json --max-credits <cap>`
   (downloads, runs the intake into `assets/models/<folder>/`, copies the
   image to `tools/assets/tripo/images/<family>/`).
4. `.glb.import`: copy `[params]` from `assets/models/props/lab_cart.glb.import`
   (light_baking=2, `prop_import.gd`), then `godot --headless --path . --import`
   and commit the generated map `.import` files.
5. `python tools/render_turnarounds.py --approve <names>`, catalogue row,
   `xvfb-run ... godot --path . -s res://tools/prop_lineup.gd -- <Family>`
   (prefix `VK_ICD_FILENAMES=/opt/lavapipe/lvp_icd.json`).

### Step 1: Tripo library tools (no models)

- Build: `tripo_intake.py` kind `dressing` (1,000 tris, 512 maps) and
  `lamps` (each lamp adds a small disc surface named after its shared slot,
  so `prop_import.gd` gives it `beacon_red.tres` or `sodium_lamp.tres`);
  `tripo_make.py` passes `lamps` to the intake, copies the approved input
  image to `tools/assets/tripo/images/<family>/<name>.jpg` (back-fill the
  rows already made in `halcyon.json`, `town.json`, `vendors.json` whose
  image is in the project files), `--max-credits`, and `tries` with a limit
  of 2; `props_large` entry in `tools/turnarounds.py` REFERENCES
  (`lantern_post_concept.jpg`, the outdoor reference `town_large` uses);
  delete the `Tile`, `Enamel` and `Ice` slot entries from `prop_import.gd`
  if no model uses them; ADR 0017 Consequences line;
  `tripo-prompts.md` drops the code-built rows and uses the file names
  (`chain_link_fence`, not `chainlink_fence`).
- Tests: `test_tripo_intake.py`: a dressing intake stays under 1,000 tris;
  a row with one lamp gives a second surface named `Beacon` at the given
  spot. `test_tripo_make.py` (faked API): the image lands in
  `tools/assets/tripo/images/`; a run stops before a task that would pass
  `--max-credits`; a row with `tries: 2` is refused. A `tools/ci` test that
  every folder in `check_models.BUDGETS` that holds a model has a
  turnarounds reference. All fail without the step.
- Done when: CI green.

### Step 2: Barriers remake

- Build: 7 Tripo rows in `tools/assets/tripo/barriers.json` with the same
  names as the #349 files, so layouts and catalogue rows keep working;
  their builders deleted from `library_barriers.py` (Keep it simple
  rule 11); the 4 code-built barriers stay. Turnarounds re-approved.
- Tests: `test_library_barriers.gd`: the 7 rows expect one `Baked` material
  and their catalogue size (within 0.1 m); the 4 code-built rows unchanged.
  The catalogue check and Assets CI cover the rest.
- Done when: CI green, image sheet and board approved by the person.

### Step 3: Military camp and vehicles

- Build: `military.json` rows get prompts and lose the image paths that do
  not exist; 7 models; floodlight_tripod gets two `Bulb` lamps. Trucks in
  `props_large/` (12,000 tris).
- Tests: catalogue rows (the catalogue check fails without them); Assets CI;
  `test_prop_models.gd` lets a Tripo prop carry `Baked` plus one shared lamp
  slot and checks floodlight_tripod has it.
- Done when: board approved.

### Step 4: Industrial

- Build: 6 Tripo rows (sodium_street_lamp gets a `Bulb` lamp);
  `library_industrial.py` with guard_rail_3, guard_rail_6 (3 m and 6 m to
  match `pipe_run_3/6`, 1 m grid) and wall_ladder.
- Tests: catalogue rows; Assets CI; `test_prop_models.gd` loads them; a
  size check that guard_rail_3/6 are 3.0 and 6.0 m long.
- Done when: board approved.

### Step 5: Rail

- Build: 8 Tripo rows (signal_post gets two `Beacon` lamps, station_sign a
  blank board); `library_rail.py` with track_section (1.435 m gauge, 6 m
  long so sections line up).
- Tests: catalogue rows; Assets CI; track size check (6.0 m, gauge 1.435 m).
- Done when: board approved.

### Step 6: Large pieces

- Build: container_stack from Tripo; `library_large.py` with
  hospital_train_car and last_car_glow as hollow shells (body, roof,
  windows, doors open, steps), placed as dressing over a `layout.json` room
  so the map's walls give collision and navmesh, and signal_gantry as a
  prop with box colliders. Red tail lamps on `Beacon`, the last car's glow
  on a bio-green glow slot (reuse an existing one, or add one shared
  slot). The hospital car carries
  our own Cordon medical mark, never a red cross.
- Tests: catalogue rows; Assets CI in `props_large/`; a check that the train
  car has an open door gap at least 1.2 m wide (player capsule fits).
- Done when: board approved.

### Step 7: Hospital and sanatorium

- Build: 9 Tripo rows. Wheelchair and covered gurney reuse existing models
  (catalogue family column only).
- Tests: catalogue rows; Assets CI.
- Done when: board approved.

### Step 8: Map hero pieces

- Build: 5 Tripo rows in `props_large/`. Sizes from `docs/design/maps.md`:
  the fountain fits inside the 25 m Courtyard loop with a 1.5 m clear ring;
  four turbine housings fit the 40 x 25 m Turbine Hall; the control building
  and sanatorium front are backdrop pieces (Tripo gives a closed mesh; the
  map places them so their back is never seen). dam_control_building gets
  `Beacon` lamps on its masts.
- Tests: catalogue rows; Assets CI in `props_large/`.
- Done when: board approved.

### Step 9: Outdoor and clutter, close-out

- Build: 5 Tripo rows (iron_gate gets two `Bulb` lantern lamps);
  `library_outdoor.py` with iron_fence (3 m, snaps end to end, `Iron` and
  `Stone` slots) and leaf_litter (dressing); reuse rows for pine tree, bench
  and snow drifts; catalogue complete; ROADMAP Done; finish-feature check.
- Tests: catalogue rows; Assets CI; iron_fence size check (3.0 m).
- Done when: all boards approved, every acceptance line ticked.

## Acceptance

- [ ] Every model in families 1-8 builds from its manifest row or script and
  passes `check_models.py` and the glTF validator (Assets CI).
- [ ] Every model has an approved turnaround and a catalogue row; the
  catalogue check is green.
- [ ] Every Tripo model has its input image committed in
  `tools/assets/tripo/images/` and a `task_id` in its row.
- [ ] Every library model loads in Godot with light_baking 2
  (`test_prop_models.gd`).
- [ ] Credits spent per family are in each PR and stay under the family cap.
- [ ] The person approved each family's image sheet and lineup board.

## Risks

- Credits run out mid-family: the family cap stops the tool; the thread
  sends a card before spending more.
- Bad generations (wrong shape, baked text, fused parts): image sheet first,
  2 tries per row, then code-built or dropped.
- Look drifts across 48 generations and 8 threads: the same style line on
  every prompt, the same lineup tool and light, and each family board next to
  its key shot before the next family's models.
- Code-built pieces (train cars, fences, track) look plainer than Tripo props
  next to them: the board shows both together; a later plan can move a piece
  to Tripo if the person asks.
- Lost source `.glb` (project files only): rebuild from `task_id` or the
  committed image (Data). The person may also copy
  `/mnt/project-files/tripo/sources/` to their own storage.
- Repo grows by about 110 MB: no LFS (AGENTS rule 8); large pieces keep 2048
  maps only where they need them.
- Hero backdrops at 2048 maps over 30 m look soft up close: they are
  backdrops; the map keeps players at distance.
- Tripo CI: GitHub CI cannot reach `api.tripo3d.ai`; tests fake the API and
  real runs happen in the family thread.
- Main moves fast: each step only adds new files plus list edits.

## Open decisions

- [ ] Approve this Tripo plan and buy about 3,000 Tripo credits (about $30)
  for the 48 models? Answer (person, 2026-11-20): hold for now; no credits
  spent, steps 3-9 stay paused.
- [x] Hospital train mark: the design says "red cross"; the Red Cross emblem
  is protected and its owners ask games not to use it. Answer (person,
  2026-11-20): use our own Cordon medical mark (white cars, red stripe).
