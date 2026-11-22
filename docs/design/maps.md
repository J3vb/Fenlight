# Fenlight: First Four Maps

Source: copy of the design doc as of Nov 14, 2026. Where this file and the code differ, the code and `docs/DECISIONS.md` win.

## The four maps at a glance

Four maps, each with its own way to play: a tight indoor lab, a vertical dam, a wide open rail yard, and a dark hospital whose routes change. All four sit in the same Ardennes valley as Lantern Post and use the Cold Containment look: teal light inside, warm sodium lamps outside, bio-green only where the experiment leaks.

| Map | Setting | How it plays | Size | Doors to open all | Signature event |
| --- | --- | --- | --- | --- | --- |
| Halcyon Labs | Bunker bio-lab | Compact, indoor, the learning map | 70 x 60 m, 8 areas, 90 s loop | 7,000 | Coolant Tunnel opens with power |
| Kessel Dam | Hydro dam in a gorge | Vertical, 3 heights, long sightlines | 160 x 90 m, 45 m tall, 8 areas | 7,250 | Spillway flood |
| Marrow Junction | Rail yard with a stalled hospital train | Open outdoor, wide loops, best with 4 | 220 x 160 m, 8 areas | 8,250 | Shunting loco ride |
| Grauwald Sanatorium | Snowbound hilltop hospital | Dark, Blackout-heavy, routes shift | 120 x 100 m, 4 floors, 9 areas | 9,750 | Lockdown shuffle |

**Unlock order (decided).** Halcyon Labs is open from the start. Each next map unlocks when you reach round 15 on the previous one, or at character level 8, 18 and 28. Players who just want to play with friends can still join a squad on any map the host has unlocked.

### Rules every map follows

- **Same machines everywhere.** All 8 Serums, 1 Reforger (needs power), 1 power switch, 1 Specimen Vault with 6 spots, 4 to 5 wall guns, 1 exfil point. Only placement and the Reforger unlock task change per map.
- **Start zone.** Warden P9 plus at least one wall gun inside the start area, first door costs 750.
- **Door costs** rise from 750 near the start to 1500 at the far end. Every area is opened by one purchase; some areas have two doors and either one opens it.
- **Two training loops.** An early one that costs 2,000 points or less to reach, and a late one wide enough for 4 players to kite in.
- **Zombie spawns** come only from fixed entry points (windows, vents, grates, gaps). A point is active only if its area is open and a player is within 40 m of walking distance. A point never fires if a player can see it from under 12 m. Each map has 21 to 28 points, plus 4 to 6 co-op-only points.
- **Exfil** (from round 10, every 5 rounds, hold 60 s) sits far from the start, in a space with 3 approaches, so holding it is a real fight.
- **One secret per map.** Doable solo, never needed to win, reward is a run boost or a guaranteed item plus a town cosmetic.
- **Scaling for 1 to 4 players** uses the design doc rule: zombie count x (1 + 0.5 per extra player), max alive 24 + 6 per extra player, health unchanged. On top of that, each map turns on its co-op-only spawn points at 3 or 4 players and changes one map rule (listed per map).

## Map 1: Halcyon Labs (refined)

Halcyon Labs stays the learning map: small, indoor, every room readable in one glance. Three changes from the first concept: a Coolant Tunnel that opens with power and creates the late training loop, an exfil hatch in the Containment Wing, and co-op spawn points.

**Setting and mood.** A Cold War bunker under a pine ridge, rebuilt in secret as a bio-lab. You arrive at the Loading Dock at night as the last supply truck burns: sodium light and fire outside, flickering teal tubes once you step in. Before power the inside is dim emergency red-orange; after power it snaps to clean cold teal, with green glow from the specimen tanks in the Labs.

_(Diagram not copied: Halcyon Labs layout · 8 areas, schematic.)_

The front half (Dock, Guard Post, Mess Hall, Corridor) is a small square you can open with early points; power adds the Coolant Tunnel and turns the back half into one ring.

| # | Area | Opens with | What is here | Spawn points |
| --- | --- | --- | --- | --- |
| 1 | Loading Dock (start) | - | Brenner Trench 750 wall gun, burning truck, crates to circle | 4 windows, +2 co-op (truck gaps) |
| 2 | Guard Post | Door 750 | Kestrel SMG 1000, Quickhands | 2 windows |
| 3 | Mess Hall | Debris 1000 | Vanguard AR 1200, Vault (first spot), Second Wind, table loop | 2 windows, +1 co-op |
| 4 | Main Corridor | Door 1000 from Guard Post or Mess Hall | Ironhide | 2 windows |
| 5 | Generator Hall | Door 1250 | Power switch, Talon DMR 1500, Scavenger | 2 windows |
| 6 | Labs (power) | Debris 1500 | Reforger, Deadeye | 2 windows, 2 ceiling vents |
| 7 | Containment Wing (power) | Door 1500 | Overclock, Stride, Mule, Brute arena, exfil hatch | 2 windows, 2 vents, +1 co-op |
| 8 | Coolant Tunnel | Opens free when power is on | Links Generator Hall and Labs | 1 floor grate |

**Flow.** Rounds 1 to 3 in the Dock. Most players buy the Mess Hall first (best gun, first Vault), then the Corridor, then Generator Hall for power around round 7 to 9. Power opens the Coolant Tunnel and the Labs, so the back half becomes one big ring.

**Training loops.** Early: around the long tables in the Mess Hall (reached for 1,000). Late: the ring Main Corridor, Generator Hall, Coolant Tunnel, Labs, back to the Corridor. It is about 110 m around, wide enough for 4 players.

**Chokepoints.** The Main Corridor (4 m wide, 30 m long) is the classic hold spot for rounds 5 to 12. The Coolant Tunnel is narrow and has a grate spawn in the middle, so it is a route, not a camping spot.

**Specimen Vault spots.** Mess Hall (first), Guard Post, Main Corridor, Generator Hall, Labs, Containment Wing.

**Reforger task.** Unchanged: after power, shoot the three junction boxes (Mess Hall, Generator Hall, Containment Wing) with an explosive or Shock ammo.

**Exfil.** The emergency hatch in the Containment Wing. You hold the Brute arena for 60 s while a rope ladder drops. The arena has 3 approaches: the Labs door, and the two vents.

**Secret: Signal in the Static.** After power, three wall radios (Guard Post, Generator Hall, Labs) each play a short tone. Interact with them from lowest to highest tone. The Cold Room behind the Mess Hall freezer opens with a free Cryo Lance on a rack (once per run) and the Halcyon Pin cosmetic for town.

**Scaling for 1 to 4 players.** Solo and duo: the Dock truck gaps stay blocked by burning wreckage. At 3 to 4 players the fire burns out and those gaps plus the Mess Hall and Containment co-op points open. With 3 or more players, the one-way vent drop from the Containment Wing to the Mess Hall also works in reverse as a climb, giving a second way out of the far end.

**Blockout.** One floor, 70 x 60 m, the Containment Wing 3 m lower down a ramp. Ceilings 3.5 m in rooms, 6 m in the Mess Hall and Generator Hall so Stalkers have room to climb.

## Map 2: Kessel Dam

Kessel Dam is the vertical map: three heights stacked inside one concrete wall, long sightlines for the Talon DMR, and a flood you can trigger to wipe a crowd. You start on top and fight your way down to the river.

**Setting and mood.** A 1960s hydro dam closing a forested gorge, at night in steady rain. The crest road is lit by warm sodium lamps and a stalled army convoy. Inside the wall it is cold teal and wet, with dripping service galleries. A crack in the spillway glows bio-green where the lab's waste was dumped into the reservoir.

**Key shot.** [Kessel Dam key shot](concepts/act1/keyshots/kessel_dam.jpg), looking along the Crest Road at night.

![Kessel Dam key shot](concepts/act1/keyshots/kessel_dam.jpg)

What the build takes from it:
- **Mood:** heavy rain, a moonlit cloud gap, wet asphalt that mirrors every lamp, mist rising from the gorge.
- **Key props:** the stalled convoy (canvas-top trucks, one armoured car, ammo crates, a body under a tarp), yellow-black concrete barriers and a yellow rail along the parapet, a thick pipe running along the outer face, steel stairs and landings bolted to the wall, a tall control building at the far end of the crest with radio masts and red tip lights.
- **Lighting:** sodium street lamps along the crest are the only warm light up top, small lamps on the dam face mark the stairs and landings, the Turbine Hall below shows lit windows and four outflow pipes. Treat this as the outside, so warm is right here; inside the Turbine Hall the look rules still say cold teal.

Where the art differs from this doc:
- **Two waterfalls.** Water pours through the middle of the dam face, and a second, natural waterfall falls down the cliff on the right. The doc has no second waterfall; it can stay as backdrop only, not a play area. The centre falls can be the Spillway, but in the doc the Spillway is a sloped area you walk down, so the build needs a dry channel next to the water.
- **Turbine Hall is outside.** The art shows the Turbine Hall as its own building at the foot of the dam. The doc puts it at river level, which fits, but the build has to link it to the dam stairs and the Tailrace Dock.
- **No bio-green crack.** The glowing spillway crack from the doc is not in the shot. Keep it: it is the map's one bio-green accent.
- **Bright red blood.** The look rules say gore is dark red-brown, never bright red. Follow the look rules.
- **No zipline** is visible. Keep it from the doc.

_(Diagram not copied: Kessel Dam side view · 3 heights, 8 areas, schematic.)_

The map reads top to bottom: the crest is the start, the Valve Gallery is the mid-game hold, and the river level forms the late-game ring. The zipline is the fast way back down.

| # | Area | Height | Opens with | What is here | Spawn points |
| --- | --- | --- | --- | --- | --- |
| 1 | Crest Road (start) | +40 m | - | Brenner Trench 750, stalled convoy to circle, zipline head | 4 (road barricades, parapet climbs), +2 co-op |
| 2 | Gatehouse | +40 m | Door 750 | Kestrel SMG 1000, Quickhands | 2 |
| 3 | West Stair Tower | +40 to +20 m | Door 1000 | Second Wind, 3 switchback flights | 2 |
| 4 | Valve Gallery | +20 m | Open from the stair | Vanguard AR 1200, Vault (first spot), Ironhide | 3 (2 are Stalker ducts) |
| 5 | Control Room | +20 m | Debris 1250 | Power switch, Talon DMR 1500, Deadeye, flood lever, windows over the Turbine Hall | 2 |
| 6 | Turbine Hall | River level | Door 1250 (east stair) | Reforger, Overclock, 4 turbine housings to circle | 4, +2 co-op |
| 7 | Spillway (power) | Sloped, +40 m to river | Debris 1500 | Stride, Scavenger | 3 |
| 8 | Tailrace Dock | River level | Door 1500 | Mule, exfil boat | 3, +1 co-op (river edge) |

**Flow.** Rounds 1 to 3 on the Crest Road. Buy the Gatehouse and the stair, then hold the Valve Gallery while you save for the Control Room and power (round 8 to 10). The east stair drops you into the Turbine Hall, the late-game home. Spillway and Tailrace close a big outer loop at river level.

**Training loops.** Early: around the four convoy trucks on the Crest Road, free from round 1. Late: a figure-eight around the four turbine housings in the Turbine Hall (40 x 25 m). For a long run, the river-level ring Turbine Hall, Spillway, outflow channel, Tailrace Dock, back to the Turbine Hall.

**Chokepoints.** The Valve Gallery is a 120 m concrete tube, 3.5 m wide, with two ceiling ducts where Stalkers drop in. Great for lining zombies up with the Vanguard, dangerous from round 12. The east stair is the one way down, so it is the second chokepoint.

**Specimen Vault spots.** Valve Gallery (first), Gatehouse, Control Room, Turbine Hall, Spillway, Tailrace Dock.

**Reforger task.** After power, open three sluice valves (Valve Gallery, Turbine Hall, Spillway). Each valve wheel takes a 5 s hold, during which zombies target you first. Solo: any order, any time. Co-op: all three within 30 s, so the squad has to split up.

**Exfil.** The boat at the Tailrace Dock. Hold the dock for 60 s. Zombies come from three directions: the Turbine Hall door, the spillway outflow, and climbing out of the river.

**Event: Spillway flood.** The flood lever in the Control Room (needs power, costs 500, can be used once every 3 rounds) opens the sluices for 20 s. Water rushes down the Spillway and across the Tailrace: every zombie in it dies except Brutes, which are slowed by 50%. A player caught in it is knocked down the channel and takes 50 damage. A siren gives 4 s of warning.

**Zipline.** After power, the zipline from the Crest Road to the Tailrace Dock is a free one-way fast route down (8 s ride, you can shoot pistols while riding).

**Secret: Drowned Samples.** Three green specimen jars hang under the dam along the zipline route. Shoot all three during one ride. A flooded maintenance cell in the Spillway drains and opens: an item cache with one item of Rare or better (item level = the round), once per run, plus the Kessel Gauge cosmetic.

**Scaling for 1 to 4 players.** Co-op points open at 3 to 4 players (parapet climbers on the Crest, two turbine pits, the river edge). The valve task needs coordination in co-op (see above). Solo players get a third Crest Road barricade that stays boarded, so the start is less exposed.

**Blockout.** Dam crest 160 m long; the playable footprint is 160 x 90 m and 45 m tall. Build the three heights as separate floors linked by stairs: the thick dam wall between them is a natural occluder, which helps the frame rate a lot.

## Map 3: Marrow Junction

Marrow Junction is the open map built for a full squad: a foggy rail yard with wide lanes between container stacks, a roundhouse to circle, and a shunting locomotive you can ride around the whole yard. Solo it is the hardest map to survive, because there is nowhere small to hide.

**Setting and mood.** A freight junction that became a quarantine checkpoint. A hospital train carrying the first patients out of Halcyon stalled here and never left. Thick ground fog, tall sodium floodlight masts, red signal lamps. Inside the train cars it is cold teal, with green-lit specimen cases in the last car.

**Key shot.** [Marrow Junction key shot](concepts/act1/keyshots/marrow_junction.jpg), the checkpoint beside the stalled hospital train.

![Marrow Junction key shot](concepts/act1/keyshots/marrow_junction.jpg)

What the build takes from it:
- **Mood:** thick low fog, wet ground with puddles and dead leaves, razor-wire fences, a moon behind cloud. Grauwald sits on the hill behind the yard with red-lit masts, so the next map is always in view.
- **Key props:** the hospital train (white cars, red stripe and the Cordon medical mark, no red cross, rust, red tail lamps, steps up to each door), the last car glowing bio-green with a zombie shape inside, a steel signal gantry across the tracks with red signal lamps, a raised watch tower on the gantry, floodlight masts, a striped boom barrier, yellow-black concrete barriers, an army field tent with a biohazard tarp, laptops and a lamp, yellow hard cases and loose cables.
- **Lighting:** red signal lamps are the zone's accent, the green last car is the only bio-green, warm light only from the tent lamp and the car windows.

Where the art differs from this doc:
- **The train sits beside a checkpoint gate.** The art puts a boom barrier and a guarded checkpoint right next to the train. In the doc the Quarantine Gate (exfil) is on the road out, far from the train, and the train sits between Platform 1 and the Roundhouse. Build it as the doc says; use the boom barrier, tent and cases as dressing at the Quarantine Gate, and a smaller checkpoint by the train if it fits.
- **The watch tower on the gantry** reads like the Signal Box. In the doc the Signal Box is a raised building at +6 m. A gantry tower is a fine shape for it if the DMR perch still covers the Freight Yard.
- **White floodlights.** The doc says sodium floodlight masts, the art shows cold white beams. Pick one when the map is built; sodium keeps "outside warm" from the look rules.
- **No container stacks, loco or roundhouse** in view. The shot only shows one corner; the doc layout stands.

_(Diagram not copied: Marrow Junction top-down · 8 areas, schematic.)_

The Freight Yard sits in the middle and touches four areas, so it is the crossroads of every run. The loco track wraps the whole map and is the fastest way across once the power is on.

| # | Area | Opens with | What is here | Spawn points |
| --- | --- | --- | --- | --- |
| 1 | Platform 1 (start) | - | Brenner Trench 750, Kestrel SMG 1000, Quickhands, station building | 3 |
| 2 | Signal Box | Door 750 | Talon DMR 1500, Deadeye, raised perch over the yard | 2 |
| 3 | Freight Yard | Debris 1000 | Vanguard AR 1200, Vault (first spot), Second Wind, container lanes | 5, +3 co-op |
| 4 | Hospital Train | Door 1000 | Ironhide, 6 linked cars | 4 (one under every second car) |
| 5 | Roundhouse | Door 1250 from the Freight Yard or the far end of the train | Reforger, Overclock, turntable pit | 4, +2 co-op |
| 6 | Substation | Debris 1250 | Power switch, Scavenger | 2 |
| 7 | Engine Shed (power) | Door 1500 | Shunting loco, Stride | 3 |
| 8 | Quarantine Gate | Door 1500 | Mule, exfil truck | 3, +1 co-op |

**Flow.** Rounds 1 to 3 on the platform. The Freight Yard is the big early buy: lots of room and the first Vault. The Signal Box is a strong spot for a DMR player covering the team. Power is in the Substation, out on the west edge, so the squad has to cross open ground to get it. The late game lives in the Roundhouse.

**Training loops.** Early: the container lanes in the Freight Yard, about 160 m around. Late: around the turntable pit in the Roundhouse (30 m across), which is the safest loop on any of the four maps. A long ring also runs Platform 1, Hospital Train, Roundhouse, Freight Yard.

**Chokepoints.** The Hospital Train: 6 cars, 2.8 m wide, one door at each end of every car. It is a deadly corridor to hold and a fast shortcut to run. Zombies crawl out from under the cars, so it is never fully safe.

**Specimen Vault spots.** Freight Yard (first), Platform 1, Hospital Train, Roundhouse, Substation, Engine Shed.

**Reforger task.** After power, throw the three track switches (Signal Box, Freight Yard, Engine Shed) to route the loco to the Roundhouse. Its first run delivers the Reforger core.

**Event: the shunting loco.** In the Engine Shed, start the loco for 1,000 points (once every 2 rounds). It runs one 45 s lap of the yard on the loop track and stops at every area. Players can ride the flatbed and shoot from it. Zombies on the track are killed; zombies near it try to climb aboard. Good for escaping a bad spot or moving the squad across the map in one go.

**Exfil.** The Quarantine Gate on the road out. Hold the gate yard for 60 s while an army truck drives up. Three approach lanes (the Substation road, the Engine Shed yard, the fence line) make it the most open exfil of the four maps.

**Secret: Lost Property.** Four luggage tags appear at random among 10 spots across the map each run. Bring all four to the lost-property hatch on Platform 1. The back room opens: a free Siphon prototype (once per run) and the Junction Lamp cosmetic.

**Scaling for 1 to 4 players.** This map changes shape with the squad size. For 1 to 2 players, two container stacks block the outer lanes of the Freight Yard, making it smaller and safer. At 3 to 4 players those lanes are open and the co-op spawn points switch on. The loco costs 500 instead of 1,000 when playing solo.

**Blockout.** 220 x 160 m, mostly one height with the Signal Box at +6 m and the Roundhouse roof as a no-go zone. Fog limits the view to about 120 m, which hides the map edges and keeps the draw distance under control.

## Map 4: Grauwald Sanatorium

Grauwald Sanatorium is the dark, late-game map: a hub-and-spoke hospital where fire doors close and reopen every few rounds, so the safe route you learned can be gone next round. Blackout rounds come twice as often here, so a flashlight and sound matter more than anywhere else.

**Setting and mood.** A 1910s tuberculosis sanatorium on a snowy hilltop above the valley, later used by Halcyon as its patient intake site. Moonlight on snow outside, a frozen fountain in the courtyard. Inside: long tiled wards under failing teal tubes, a three-floor rotunda with balconies, and steam from the basement boilers. The chapel and hydrotherapy baths are where the bio-green glow is strongest.

**Key shot.** [Grauwald Sanatorium key shot](concepts/act1/keyshots/grauwald_sanatorium.jpg), the snowy courtyard seen through the iron gates.

![Grauwald Sanatorium key shot](concepts/act1/keyshots/grauwald_sanatorium.jpg)

What the build takes from it:
- **Mood:** full moon, light snow falling, dead trees, low mist over the ground, icy wet paving that reflects the lamps.
- **Key props:** the frozen tiered fountain with icicles, iron benches, tall iron gates on stone posts with lanterns, a grand stone front with columns, a balcony, wide stairs, arched windows and a small cupola on the roof, ivy and cracked plaster, a tall chimney (the Boiler Room), a radio mast with red lights on the hill.
- **Lighting:** warm lanterns at the gates and doors outside, moonlight on snow, every window dark except one cold teal window on the upper floor. That single window is the one accent: it tells the player the inside is cold and something is still on in there.

Where the art differs from this doc:
- **The courtyard is a front forecourt.** The art shows an open forecourt in front of the main entrance, behind gates. In the doc the Courtyard is enclosed between the two wards and opened by debris from either ward, and the start is the Entrance Hall. Keep the doc layout: put the fountain courtyard behind the building with this look, and use the gates and front steps as the backdrop seen from the Entrance Hall.
- **Cupola, not a glass roof.** The roof has a small domed cupola. The doc's Roof Solarium is a glass roof big enough for exfil. The cupola can sit on top of the Rotunda, with the solarium on a flat roof beside it.
- **No bio-green** is visible from outside. That fits the doc: the green belongs to the Chapel and Hydrotherapy inside.

_(Diagram not copied: Grauwald Sanatorium layout · 9 areas, schematic.)_

The Rotunda, both wards and the Courtyard form one ring, and only that ring has fire doors. Every other room is a dead end off the ring, which is why the lockdown can never trap anyone.

| # | Area | Opens with | What is here | Spawn points |
| --- | --- | --- | --- | --- |
| 1 | Entrance Hall (start) | - | Brenner Trench 750, Kestrel SMG 1000, Quickhands | 3 |
| 2 | Rotunda | Door 750 | Vault (first spot), Second Wind, 3-floor atrium, the hub | 4 (balconies) |
| 3 | East Ward | Door 1000 | Vanguard AR 1200, Ironhide | 3 |
| 4 | West Ward | Door 1000 | Talon DMR 1500, Deadeye, 60 m straight corridor | 3 |
| 5 | Courtyard | Debris 1250 from either ward | Scavenger, frozen fountain to circle | 4, +2 co-op |
| 6 | Boiler Room | Door 1250 (stairs down from the Rotunda) | Power switch, Overclock | 2 |
| 7 | Chapel (power) | Door 1500 | Reforger, Stride | 3 |
| 8 | Hydrotherapy (power) | Door 1500 | Mule, specimen canisters | 3, +1 co-op |
| 9 | Roof Solarium (power) | Door 1500 (Rotunda top floor) | Exfil helicopter, glass roof | 3, +1 co-op |

**Flow.** Rounds 1 to 3 in the Entrance Hall, then the Rotunda as the early base. Pick one ward first (East for the AR, West for the DMR), then the Boiler Room for power. Power opens the three far rooms: Chapel, Hydrotherapy and the Roof.

**Training loops.** Early: the Rotunda ground floor around the central reception desk. Late: around the frozen fountain in the Courtyard (25 m across), or the big ring Rotunda, West Ward, Courtyard, East Ward, back to the Rotunda.

**Chokepoints.** The West Ward is a 60 m straight tiled corridor: perfect for the DMR, but Stalkers use the ceiling. The stairs down to the Boiler Room are a dead end, so do not get caught there late.

**Specimen Vault spots.** Rotunda (first), East Ward, West Ward, Courtyard, Chapel, Hydrotherapy.

**Reforger task.** After power, carry three specimen canisters from Hydrotherapy to the Chapel altar. While carrying one you can only use your pistol and you move at 80% speed. In co-op this is a natural escort job.

**Event: Lockdown shuffle.** From round 8, every 4 rounds, the security system closes fire doors on the central ring (Rotunda to West Ward, Rotunda to East Ward, West Ward to Courtyard, East Ward to Courtyard). A siren and green lights on the doors give 15 s of warning. Doors to dead-end rooms are never fire doors, so nobody gets trapped. Any closed fire door can be overridden for 500 points (3 s hack). A door you bought stays bought; the lockdown only seals it for those rounds.

**Exfil.** The Roof Solarium. Hold the glass rooftop for 60 s while a helicopter comes in. Stalkers come through the glass roof, the rest up the Rotunda stairs.

**Secret: Ward Zero.** During Blackout rounds, five numbers glow green on walls around the map (one per area: Entrance Hall, East Ward, West Ward, Courtyard, Chapel). Enter them in that order on the old lift panel in the Rotunda. The lift takes you to the sealed Ward Zero: one item of Epic or better (item level = the round), once per run, plus the Grauwald Lantern cosmetic.

**Scaling for 1 to 4 players.** Solo and duo: the lockdown closes 1 fire door. At 3 to 4 players it closes 2, which can split the squad for a few rounds until someone pays the override. Co-op spawn points open in the Courtyard, Hydrotherapy and on the Roof.

**Blockout.** 120 x 100 m over 4 levels: basement, ground, first floor and roof. The Rotunda atrium is open through all three upper floors (12 m tall), which is the one place where many lights stack, so it gets its own light budget.

## How to build them

Every map is built from text files and code, in two art passes: first to the look of the [Visual Style Guide](look-rules.md) previews, then improved with asset packs and better models once the map plays well.

### Map files

- `levels/<map_id>/layout.json`: the greybox as plain data. Rooms are boxes (position, size, floor height), openings are door or window cuts, stairs and ramps are lines. Easy for Claude or Codex to read and change, and easy to diff.
- `tools/blockout_builder.gd`: an editor script that turns `layout.json` into `blockout.tscn` (floors, walls, ceilings, door frames, collision, navmesh source, occluders). Run it again after any layout change.
- `levels/<map_id>/map.tscn`: instances the blockout and holds the gameplay nodes, which are placed by hand or by script: `MapArea`, `Door` (cost, area it opens, needs power), `WallBuy`, `SerumMachine`, `VaultSpot`, `Reforger`, `PowerSwitch`, `ExfilPoint`, `ZombieSpawnPoint` (area, type: window, vent, grate or ground, co-op only yes/no), and one `MapEvent` script for the map's event.
- `content/maps/<map_id>.tres`: the `MapDefinition` resource (name, unlock rule, areas, Look Profile per area, music, secret and event scripts). Adding a fifth map means a new folder and a new resource, nothing else.

### Pass 1: the style-guide look

The previews were built from simple shapes, good materials and strong lighting. Pass 1 copies that exactly, all made in code:

- **Geometry** from the builder plus a small prop kit generated in code: crates, barrels, pipes, railings, tables, lockers, light fittings, train cars and containers as boxes, cylinders and bevelled shapes (CSG baked to meshes, or `ArrayMesh` from script).
- **Materials** from a shared set of about 12 `StandardMaterial3D` resources (painted concrete, wet concrete, tiles, steel, rust, glass, rubber, emissive teal, emissive sodium, emissive bio-green), using procedural noise textures where needed.
- **Lighting** carries the look: one `LookProfile` per area (fog colour and density, ambient, exposure), baked LightmapGI, volumetric fog, and at most 6 shadowed real-time lights in view.
- Dev colours during greybox: grey walls, orange buyable doors, blue spawn points, green machine spots. These go away when the materials go on.

### Pass 2: improve

Once a map plays well, replace kit pieces one by one with better models: asset packs (check that each licence allows use in a released game and list it in `ASSET_SOURCES.md`) or Blender models made by script. Because gameplay nodes live in `map.tscn` and not in the meshes, swapping art never breaks a map.

### Automatic checks per map

A GUT test loads each map headless and fails if any of these is false:

- Every area can be reached from the start by buying doors, and every door opens exactly one area.
- All 8 Serums, 1 Reforger, 1 power switch, 1 exfil point and 6 Vault spots are placed.
- Every spawn point has a navmesh path to the start area.
- Every area has at least 2 spawn points, and no spawn point is within 12 m line of sight of a player start.
- The total door cost matches the table in this doc.

### Performance budget

Target 120 fps at 1440p High on an RTX 4080 Super. Per map: Halcyon and Grauwald use walls as occluders (`OccluderInstance3D`); Kessel Dam uses the dam wall between heights; Marrow Junction relies on fog (about 120 m view), visibility ranges on props, and lower-detail meshes for far container stacks. Each map gets a perf capture at the 3 worst camera spots before it counts as done.

### Build order

1. **Halcyon Labs** in phase P4, as planned: the first full map and the test case for the builder and the checks.
2. **Kessel Dam** next: it adds vertical play, the zipline and a water event, but no new big systems.
3. **Marrow Junction** after co-op (P7), because it is designed for 4 players and needs the moving loco to be network-synced.
4. **Grauwald Sanatorium** last: it needs the Lockdown shuffle system and the most lighting work.

Each map goes through the same steps: layout.json greybox, play it with bots, place gameplay nodes, run the checks, Pass 1 art and lighting, perf capture.

### Open questions

- [ ] Decided: unlock at round 15 on the previous map or character level 8, 18, 28.
- [ ] Decided: secrets give their item reward every run (cosmetic once per character).
