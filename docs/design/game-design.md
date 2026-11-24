# Fenlight: Game Design Doc

Source: copy of the design doc as of Nov 14, 2026. Where this file and the code differ, the code and `docs/DECISIONS.md` win.

Every design change since that copy is listed in the [Change log](#change-log) at the end of this file.

## Pitch, pillars and core loop

Fenlight is a solo-first, round-based zombie survival FPS set in a Cold War bunker turned bio-lab in the Ardennes forest. You survive endless rounds, earn points from every hit and kill, and spend them to open the facility, buy guns, and power up.

**Four pillars.** Every feature must serve at least one.

1. **Gunplay first.** Shooting must feel tight and weighty, like a modern military shooter. If a feature makes shooting feel worse, it is cut.
2. **Readable escalation.** The player always knows the round, the threat, and why they died. New enemy types are telegraphed by sound and silhouette.
3. **Earn your space.** The map starts small. Points buy doors, and each new area adds risk, guns and tools.
4. **Built to grow.** Every weapon, enemy, perk, drop and round rule is a data file. Adding content means adding a file, not editing code.

A fifth pillar was added with the progression update: **every run counts.** Even a bad run gives XP and maybe a drop, so there is always a reason for one more.

**Core loop (one round, about 1 to 4 minutes).** Zombies spawn from barricaded windows and vents. You shoot, earn points, repair barricades between kills, and spend points at wall guns, doors and machines. Kill the last zombie and you get a 10 second breather before the next round.

**Session loop.** A good run lasts 30 to 90 minutes and reaches round 15 to 30. Death ends the run, but you keep your XP and the loot you picked up. Your best round and stats are saved per map.

**Between runs** you level up a persistent character, spend skill points, and manage the loot you brought home. In the online version, you do that in a shared town hub where other players walk around, then squad up and deploy. See Levels and skills, Loot, and Town hub below. Online play comes last in the build roadmap; the solo wave game is built and made fun first.

## Round scaling

Difficulty climbs on four dials: how many zombies, how tough they are, how fast they move, and how quickly they arrive. Rounds 1 to 9 grow gently so new players learn; from round 10 health grows by a percentage, which is what makes round 20+ a real test.

_(Diagram not copied: computed from the formulas below · rounds 1 to 30, solo.)_

**The rules in plain words (solo)**

- **Zombies per round:** rounds 1 to 4 are fixed at 6, 8, 13 and 18. From round 5: 0.09 x round squared + 0.6 x round + 15, rounded down.
- **Health:** 120 at round 1, plus 90 each round up to round 9 (840). From round 10, multiply the previous round by 1.09.
- **Spawn delay:** 2.0 s between spawns at round 1, multiplied by 0.95 each round, never below 0.3 s. Round 10 is about 1.3 s, round 20 about 0.75 s.
- **Max alive at once:** 24.
- **Breather:** 10 s between rounds.
- **Co-op (later):** zombie count x (1 + 0.5 per extra player), max alive +6 per extra player. Health stays the same.

**Speed mix.** Each zombie rolls a speed when it spawns. The mix shifts toward runners as rounds climb.

| Rounds | Shamble (1.2 m/s) | Jog (2.6 m/s) | Run (4.2 m/s) | Sprint (5.6 m/s) |
| --- | --- | --- | --- | --- |
| 1 to 3 | 100% | 0% | 0% | 0% |
| 4 to 6 | 60% | 40% | 0% | 0% |
| 7 to 9 | 30% | 50% | 20% | 0% |
| 10 to 14 | 10% | 40% | 50% | 0% |
| 15 to 19 | 0% | 25% | 65% | 10% |
| 20 and up | 0% | 10% | 60% | 30% |

Player sprint is 6.8 m/s, so even the fastest zombie can be outrun, but only while sprinting. That keeps "training" zombies in a loop possible but tense.

## Enemy types

Five enemy types plus one special round cover version 1. Each type has one clear job and one clear tell (a sound or shape you learn to react to). Health is a multiple of the round's base health from the scaling section.

| Enemy | First round | Health | Speed | Job | Tell and counter |
| --- | --- | --- | --- | --- | --- |
| Shambler | 1 | 1.0x | Round speed mix | The crowd. Melee swipe for 40 damage. | Groans. Headshots. |
| Crawler | Any | 0.6x | 1.0 m/s | Made when explosives take a Shambler's legs. Low target that slips past your aim. | Scrape sound. Aim low. |
| Bloater | 8 | 3.0x | 1.4 m/s | Slow tank. Bursts on death into a gas cloud for 6 s (10 damage/s, slows you 30%). | Gurgling, swollen glowing belly. Kill at range. |
| Stalker | 12 | 0.6x | 5.8 m/s | Climbs walls and ceilings, pounces from up to 8 m for 50 damage. | Rising shriek 1 s before a pounce. Shoot or slide out. |
| Brute | 15, then every 4 to 6 rounds | 12x | 2.2 m/s, charges at 7 m/s | Mini-boss. Head plate absorbs 75% damage until it breaks at 25% health lost. | Ground thud, charge wind-up of 1.2 s. Sidestep the charge. |

**Blackout round (special).** From round 6, every 5 to 7 rounds (random), the lights fail. Only Glowers spawn: weak (0.4x health), fast (5 m/s), glowing green, in packs of 4 to 6. Total count is 1.5x a normal round. Clearing it guarantees a Resupply drop. It breaks up the rhythm and tests your flashlight and aim.

**Zombie rules that apply to all types**

- Body part damage: head 2.5x, torso 1.0x, limbs 0.75x. Weapons can override the head multiplier.
- Zombies path to the player, but first break through a barricade if they spawned outside. One plank torn every 1.5 s.
- Max 24 zombies alive at once (performance cap). The rest wait in the spawn queue.
- A zombie that cannot reach the player for 20 s, or is more than 60 m away for 15 s, quietly respawns at the nearest valid spawn. No wasted time hunting the last zombie.

**Player health.** 100 HP. Regenerates at 25 HP/s after 4 s without damage. A Shambler kills an unperked player in 3 hits. When downed in solo with no self-revive, the run ends.

## Gunfeel and movement

The target feel is a modern military shooter: fast aim-down-sights, recoil you can learn and control, crisp reloads, and strong hit feedback. Zombies are the target, but the gun is the star.

**Movement**

| Action | Value | Notes |
| --- | --- | --- |
| Walk | 4.5 m/s | Weapons have a move speed multiplier: SMG 1.0, AR 0.95, LMG 0.85 |
| Sprint | 6.8 m/s | Unlimited for 4 s, then 3 s cooldown. Stride serum doubles it. |
| Crouch | 2.2 m/s | Tighter hip spread |
| Slide | 0.8 s, starts at 8 m/s | From sprint. Can shoot while sliding (hip spread). |
| Mantle | Up to 1.2 m high | Auto when you push into a low wall and jump |
| Jump | 1.0 m | No bunny-hopping: each jump in a row is 20% lower |

**Gun handling rules**

1. **Aim down sights (ADS).** 0.18 s for pistols and SMGs, 0.25 s for ARs and shotguns, 0.35 s for LMGs and snipers. Camera FOV zooms from 90 to 70 (snipers use a scope at 25). ADS moves you at 60% speed.
2. **Sprint-to-fire delay.** 0.15 s to 0.30 s by class. This is the main reason to pick an SMG.
3. **Recoil.** Each gun has a fixed vertical pattern plus small random sideways drift. The camera kicks and then recovers 80% on its own. A skilled player can learn and pull down against the pattern.
4. **Hip fire.** A spread cone that grows while moving and shooting. Shotguns and SMGs stay usable from the hip; ARs and snipers do not.
5. **Reloads.** Two lengths: tactical (round still in the chamber, faster) and empty (slower, extra bolt or slide animation). Reload can be cancelled by sprinting. Ammo in the magazine is kept.
6. **Weapon sway and inertia.** The viewmodel lags slightly behind camera turns and bobs with movement. Heavier guns lag more.
7. **Hit feedback.** White hitmarker for body, gold for head, red X for kill. A short, punchy hit sound. Blood puffs and limb loss on Shamblers. Small camera shake on kills with heavy guns.
8. **Melee.** Knife swipe, 150 damage, 0.6 s. Always one key away. Saves you when trapped.

**Game feel details.** Exact numbers for hit markers, kill feedback, view kick, screen shake, FOV punch, hitstop, muzzle flash, impacts, gore, player damage, low health and round transitions are in [Fenlight: Game Feel](game-feel.md). They live in a `FeelData` resource per weapon class, linked from each `WeaponData`.

The player carries 2 guns (3 with a later serum), 2 frag grenades that refill each round (hold G to cook, 3 s fuse; 1000 damage inside 1.5 m, falling to 0 at 7 m, stopped by walls; your own frag hurts you for up to 60, teammates take none), and one tactical slot (Lure Beacon, buyable). Weapon swap takes 0.4 s.

## Weapon list

The first 12 guns (version 1 grows to 22, see below): 5 bought from walls (always the same price and place) and 7 only from the Specimen Vault (the mystery weapon machine). All names are original. Damage is per bullet before body part multipliers.

| Weapon | Class | Damage | Fire rate (rpm) | Mag / reserve | Where | Cost |
| --- | --- | --- | --- | --- | --- | --- |
| Warden P9 | Pistol, semi | 40 | 400 | 12 / 60 | Start weapon | - |
| Brenner Trench | Pump shotgun | 8 x 35 | 70 | 6 / 36 | Wall | 750 |
| Kestrel SMG | SMG, auto | 45 | 850 | 30 / 180 | Wall | 1000 |
| Vanguard AR | Assault rifle, auto | 60 | 700 | 30 / 210 | Wall | 1200 |
| Talon DMR | Marksman, semi | 120 | 300 | 15 / 90 | Wall | 1500 |
| Hollis .44 | Revolver | 180 | 160 | 6 / 48 | Vault, common | - |
| Atlas Auto | Auto shotgun | 8 x 30 | 300 | 10 / 60 | Vault, uncommon | - |
| Mako PDW | SMG, burst | 55 | 1000 | 40 / 240 | Vault, uncommon | - |
| Halberd LMG | LMG, auto | 75 | 600 | 100 / 400 | Vault, rare | - |
| Corvid .338 | Bolt sniper | 600 (head x4) | 45 | 5 / 30 | Vault, rare | - |
| Cryo Lance | Prototype | Freezes, then shatters | 120 | 8 / 48 | Vault, prototype | - |
| Siphon | Prototype | Gravity well pulls and crushes up to 12 zombies | 40 | 3 / 15 | Vault, prototype | - |

**Ammo refill.** Ammo is bought at wall guns; drops are not made bigger (decided 2026-11-14). Buying a wall gun you already own refills its ammo for half the price: Brenner 375, Kestrel 500, Vanguard 600, Talon 750. A Reforged wall gun refills at its wall for 4000 (provisional). Vault and loot guns have no wall, so every loot gun rolls an ammo affix instead (see Ammo affixes under Loot), and otherwise refills through Resupply drops or a Reforger re-buy. The Warden P9 has no wall either, so players need a wall gun by about round 3. From the mid rounds ammo is a main point sink: in the balance model it takes about 20% of each round's points before the gun is Reforged, over half once it is (round 14 on), and about 85% by round 30.

**Balance rule of thumb.** A fresh wall gun should kill a Shambler in 3 body shots or 1 to 2 headshots at round 1, and still be usable to round 10 when upgraded once. Prototypes stay strong to round 30 and beyond but have small reserves, so you still need a normal gun.

**Full roster (2026-11-15):** version 1 grows to 22 base guns, all bullet-based (no crossbow or launchers). The 10 new guns, wall/loot sources, unlock levels and build order are in [gun-roster.md](gun-roster.md). Adding a gun is one weapon data file plus a model and sounds. A melee upgrade (machete) stays planned.

## Points economy and buyable areas

One currency, called points. You start with 500. Points reward hits, not just kills, so weaker guns still pay and players are pushed to "farm" with a pistol early, which adds a skill layer.

| Action | Points |
| --- | --- |
| Hit a zombie (any bullet that does damage) | 10 |
| Kill, body | 60 |
| Kill, headshot | 100 |
| Kill, melee | 130 |
| Repair one barricade plank | 10 (max 500 per round) |
| Revive a teammate (co-op later) | 50 |
| Payday power-up active | All of the above x2 |

**What things cost (map 1)**

| Purchase | Cost |
| --- | --- |
| Doors and debris | 2000 to 3750, rising as you go deeper (provisional, was 750 to 1500) |
| Wall guns | 750 to 1500 |
| Ammo refill at a wall | Half the gun price (375 to 750). Reforged gun 4000 (provisional) |
| Specimen Vault roll | 950 |
| Serums (perks) | 3750 to 7500 (provisional, was 1500 to 3000) |
| Reforger tiers | 12500 / 18750 / 25000 (provisional, was 5000 / 7500 / 10000) |
| Lure Beacon | 500 for 2 |

**Target earning rate.** An average player earns about 9,000 points by end of round 5, 30,000 by round 10, and 110,000 by round 20 (updated 2026-11-14 from the balance sheet; the old targets of 3,000 / 12,000 / 40,000 did not fit the zombie counts). With the provisional 2.5x prices and wall ammo, a typical player opens the main loop by round 7, owns 2 serums by round 11, gets Reforger Tier I around round 13 and Tier III around round 27, and has little left in the bank. We tune by changing the cost files, not the point values. If Tier I feels too late in play-tests, lower the price rise to 2x.

**Doors and debris.** A buyable is a door, a pile of debris, or a gate. Each has a cost, an interaction prompt, and a list of spawn zones it unlocks. Opening an area adds that area's spawners to the active pool, so the map breathes as it grows. Some areas need power first (shown as a dead keypad until power is on).

## Power-ups, serums, Reforger and Specimen Vault

Four systems give the player things to chase between rounds. All four are original in name and in how they work.

### Power-up drops

A killed zombie has a 2.5% chance to drop a power-up, max 4 drops per round. Drops come from a shuffled deck: every type comes out once before any repeats. A drop floats for 25 s, blinks for the last 5 s, then vanishes.

| Drop | Effect |
| --- | --- |
| Resupply | Full ammo for all guns, grenades refilled |
| Payday | Double points for 30 s |
| Overkill | Every hit kills for 30 s (Brutes take 20% of max health per hit) |
| Purge | Kills every zombie alive now, +400 points |
| Scrap Kit | Rebuilds every barricade, +200 points |
| Stasis | Freezes all zombies in place for 8 s |
| Supply Crate (rare, 1 in 3 decks) | One free Specimen Vault roll, delivered on the spot |

### Serums (perks)

Serums are bought from Med Dispensers placed around the map. You hold up to 4. When you go down you lose all of them (Second Wind's self-revive uses up Second Wind itself instead).

| Serum | Effect | Cost (provisional, 2.5x) |
| --- | --- | --- |
| Ironhide | Max health 100 to 250 | 6250 |
| Quickhands | Reload and weapon swap 40% faster | 5000 |
| Overclock | Fire rate +30% | 5000 |
| Second Wind | Solo: self-revive, 3 charges, then the dispenser is gone. Co-op: revive 2x faster | 3750 |
| Stride | Double sprint length, slide 25% further, faster ADS out of sprint | 5000 |
| Deadeye | Headshot damage +50%, ADS 20% faster | 3750 |
| Scavenger | Kills sometimes drop small ammo packs, +1 grenade | 3750 |
| Mule | Carry a third gun. Does not count against the 4 serum limit | 7500 |

### The Reforger (weapon upgrade station)

A machine in the Labs that needs power and three overloaded junction boxes (a short map task). You put a gun in and wait 5 s. Three tiers, each a choice point:

1. **Tier I, 12500:** damage x2, magazine +50%, reserve doubled, new name and glowing skin.
2. **Tier II, 18750:** pick one ammo mod. Incendiary (burn 3 s), Cryo (slow 50%, shatter at low health), Shock (chain to 3 nearby), or Leech (heal 1 HP per hit).
3. **Tier III, 25000:** damage x1.5 more, ammo mod gets stronger, full ammo.

Re-buying a tier you already own costs 6250 and refills all ammo. Besides Resupply drops, this and the ammo affixes are the only refill for Vault and loot guns. All Reforger prices are provisional (2.5x rise, 2026-11-14). The choice of ammo mod gives players a build decision instead of one fixed upgrade.

### Specimen Vault (mystery weapon machine)

A reinforced specimen locker with a robotic sorting arm. Pay 950, the arm shuffles sample cases for 4 s, then presents a gun. You have 12 s to take it. You cannot roll a gun you already hold.

- **Rarity odds:** now uses the loot rarity table (see the Vault line under Loot).
- **Pity rule:** if your last 9 rolls had no rare or prototype, the 10th is guaranteed rare or better.
- **Relocation:** after 6 uses at one spot, each roll has a 15% chance (+5% per roll after that) to trigger a containment alarm. You get the gun anyway, the vault seals and moves to one of 5 other spots, shown by a green beacon of light. This keeps players moving around the map.
- **Supply Crate drop** gives one free roll at the player's location.

## First map: Halcyon Labs

Halcyon Labs is a Cold War bunker in the Ardennes, rebuilt in secret as a bio-research site. A night-time spill turned the staff. You arrive at the loading dock as the last supply truck burns. The map is compact: walking the full loop takes about 90 seconds.

_(Diagram not copied: map 1 layout · 7 areas, 8 connections.)_

The map opens in two rings. The first ring (Dock, Guard Post, Mess Hall, Main Corridor) forms a loop by round 6 to 8. The second ring is power-gated and holds the big upgrades.

- **Training spot:** the Mess Hall is a large room with tables you can circle. It is the intended place to herd zombies into a group and mow them down.
- **Power:** the switch is in the Generator Hall. Turning it on lights the facility, opens the power-gated doors, and starts the Reforger task.
- **Reforger task:** three junction boxes (Mess Hall, Generator Hall, Containment Wing) must each be shot with any explosive or Shock ammo after the power is on.
- **Specimen Vault spots:** Mess Hall (always first), Guard Post, Main Corridor, Generator Hall, Labs, Containment Wing.
- **Barricaded windows:** 4 in the Dock, 2 per indoor area, plus ceiling vents in the Labs and Containment Wing where Stalkers enter.
- **Later expansion:** a freight elevator in the Containment Wing leads to a Sublevel with the map boss. Built after version 1.

### The first four maps

Full designs, layouts and the build plan are in [Fenlight: First Four Maps](maps.md). In short:

| Map | How it plays | Signature event |
| --- | --- | --- |
| Halcyon Labs (refined) | Compact indoor learning map. Adds a Coolant Tunnel ring after power and an exfil hatch | Junction-box Reforger task, radio secret |
| Kessel Dam | Vertical, 3 heights, long sightlines, zipline | Spillway flood that wipes zombies in the channel |
| Marrow Junction | Open rail yard built for 4 players, shrinks for solo | Ride the shunting loco around the yard |
| Grauwald Sanatorium | Dark hub-and-spoke hospital, Blackout-heavy | Lockdown shuffle closes fire doors every 4 rounds |

All maps share the same machines (8 Serums, Reforger, Vault with 6 spots, power, exfil) and are built from a `layout.json` greybox, first to the style-guide preview look, then improved with asset packs.

## Levels and skills

The game now has two layers. The **run layer** (points, wall guns, Serums, Reforger tiers) resets every match, as before. The **character layer** (level, skill points, field abilities, loot) stays between runs and is what you build up over weeks. Level gives skill points, not raw stats, so a high level never makes the game trivial on its own.

### XP and the level curve

Max level is 50. XP comes from the run: 10 per kill, +5 for a headshot kill, and 50 x the round number each time you clear a round. A typical run to round 15 gives about 10,000 XP.

XP needed for the next level = 500 x level to the power 1.25, rounded to 50.

| Reach level | XP for that level | Total XP | Typical runs to reach it |
| --- | --- | --- | --- |
| 5 | 2,850 | 6,500 | 1 |
| 10 | 7,800 | 35,200 | 3 to 4 |
| 20 | 19,850 | 177,550 | about 18 |
| 30 | 33,650 | 450,650 | about 45 |
| 50 | 64,800 | 1,444,150 | about 145 |

The first levels come fast so new players unlock their first skill and ability in the first session. Better players reach later rounds and level faster, because round-clear XP grows with the round.

### Skill tree

One skill point per level from level 2, plus a bonus point at levels 10, 20, 30, 40 and 50. That is 54 points. The tree has 3 branches of about 30 points each, so a maxed character can fill a bit less than two branches. That forces a build choice. Respec is free in the town for the first 3 times, then costs Scrap.

| Branch | Focus | Example nodes | Keystone (8 points in branch for now, 15 after F-90) | Capstone (11 points in branch for now, 25 after F-90) |
| --- | --- | --- | --- | --- |
| Marksman | Gun handling and headshots | Steady Hands: recoil -5% per rank (3). Quick Draw: ADS +5% per rank (3). Weak Spot: headshot damage +5% per rank (3). Fast Hands: reload +5% per rank (3). Deep Pockets: reserve ammo +10% per rank (2). | Dead Center: headshot kills refund 1 bullet to the magazine | Execution Line: any hit on a zombie under 15% health kills it (Brutes under 5%) |
| Survivor | Health, movement, staying alive | Thick Skin: +10 max health per rank (3). Second Breath: regen starts 0.3 s sooner per rank (3). Light Feet: sprint speed +5% per rank (2). Sturdy: own explosive damage -25% per rank (2). | Last Stand: once per round, a killing blow leaves you at 1 health with 2 s of immunity | Undying: +1 self-revive charge per run (co-op: revive teammates 50% faster) |
| Tinkerer | Points, power-ups, gadgets, loot | Scrounger: +5% points per rank (3). Lucky Find: loot luck +5% per rank (3). Overtime: power-up duration +3 s per rank (2). Gadgeteer: field ability cooldown -8% per rank (3). Carpenter: barricades repair 30% faster (2). | Bargain Hunter: Vault rolls cost 750 instead of 950 | Chain Supply: each power-up has a 25% chance to drop a second, different one |

### Field abilities

One active ability on a key, on a cooldown. Each kill shortens the cooldown by 0.5 s. New abilities unlock with level; you pick one to bring into a run.

| Ability | Unlocks at | Effect | Cooldown |
| --- | --- | --- | --- |
| Shock Pulse | Level 3 | Knocks back and stuns every zombie within 6 m for 2 s | 60 s |
| Med Burst | Level 8 | Heals you fully and nearby teammates for 50 | 75 s |
| Watchdog | Level 15 | Deploys a turret for 20 s that targets heads | 120 s |
| Adrenal Rush | Level 22 | +30% move speed and fire rate for 8 s | 90 s |
| Decoy Siren | Level 30 | Pulls all zombies within 20 m to a point for 6 s | 90 s |

### How this fits with Serums

Serums stay as the in-run purchase layer. Skills, gear and Serums all add to the same stat modifiers, with hard caps so stacking never breaks the game: reload speed +60%, recoil reduction 50%, flat max health +100 (Ironhide multiplies on top), points bonus +50%, loot luck +100%. Overlaps are kept on purpose but weaker on the character side: Ironhide gives +150 health, the Thick Skin skill only +30.

## Loot

Zombies drop guns and gear with a rarity and random bonus stats (affixes). What you pick up in a run, you keep. This is the main reason to play "one more run".

### What you carry

- **Loadout:** 1 sidearm (pistol class) and 1 primary from your stash, plus 3 gear slots: Vest, Charm and Implant.
- **Start of a run:** you spawn with your loadout sidearm instead of the Warden P9. Your loadout primary waits in a Drop Locker at spawn that opens at round 5. This keeps the early point-farming rounds intact.
- **Pack:** 6 slots for loot picked up during the run. Guns you pick up can be equipped right away, like a wall gun. Gear (vest, charm, implant) can be worn right away from the Pack too: the piece you take off goes into that Pack slot, and the swap never heals you.
- **End of a run:** dying keeps everything equipped and in your Pack. From round 10, an **Exfil** option appears every 5 rounds: hold the exfil point for 60 s, then leave with +50% XP for the whole run, bonus Scrap (100 x the round number), and an exfil cache with 2 items: Rare or better, Epic or better from round 20. It is a bonus, not a requirement: you keep your loot either way.

### Rarity

| Rarity | Colour | Affixes | Base drop share |
| --- | --- | --- | --- |
| Common | White | 0 | 55% |
| Uncommon | Teal | 1 | 28% |
| Rare | Blue | 2 | 12% |
| Epic | Purple | 3 | 4% |
| Legendary | Orange | 3 + a legendary trait | 0.9% |
| Prototype | Bio-green | Fixed traits (Cryo Lance, Siphon and future ones) | 0.1% |

**Item level** = the round it dropped in, capped at 50. A gun's damage is base x (1 + 0.02 per item level above 1), so a round 30 drop hits 58% harder than a round 1 drop. Affix values also roll higher at higher item levels and reach their top range at item level 30.

**Luck** shifts the odds away from Common toward higher rarities. Sources: Lucky Find skill, gear affixes, and +2% per round after round 10. Capped at +100%.

### Drop rules

| Source | Chance | Notes |
| --- | --- | --- |
| Shambler, Crawler, Glower | 1.5% + 0.1% per round, max 5% | Rolls the normal rarity table |
| Bloater, Stalker | 5% | Normal table |
| Brute | 100% | Rare or better |
| Supply Cache | Every 5 rounds, appears in a random opened area | 1 item, Uncommon or better |
| Specimen Vault | Every roll | See below |
| Exfil cache | On successful exfil | 2 items, Rare or better (Epic or better from round 20) |

Loot is personal: in co-op every player sees and gets only their own drops. Nobody can steal loot, and there is no trading in version 1.

### Affixes

Each affix rolls a value within its range. Weapon and gear have separate pools.

| Affix | On | Range |
| --- | --- | --- |
| Damage | Weapon | +5% to +15% |
| Headshot damage | Weapon | +10% to +30% |
| Fire rate | Weapon | +4% to +10% |
| Reload speed | Weapon | +8% to +20% |
| Magazine size | Weapon | +10% to +30% |
| ADS speed | Weapon | +8% to +20% |
| Points per hit | Weapon | +1 to +3 |
| Incendiary chance | Weapon | 5% to 15% |
| Chain shock chance | Weapon | 5% to 12% |
| Leech | Weapon | 1 to 3 health per hit |
| Max health | Gear | +10 to +40 |
| Regen delay | Gear | -0.3 s to -1.0 s |
| Move speed | Gear | +3% to +8% |
| Power-up duration | Gear | +2 s to +5 s |
| Loot luck | Gear | +5% to +20% |
| Ability cooldown | Gear | -5% to -15% |
| Grenade damage | Gear | +15% to +40% |

**Ammo affixes (provisional, 2026-11-14).** Vault and loot guns have no wall to buy ammo from. So every loot gun, from Common up, rolls one implicit ammo affix on top of its normal affixes. Higher rarities roll bigger values and lean toward Fabricator, the sustain option. Prototypes keep their fixed traits and always get Fabricator at 9%.

| Ammo affix | Effect | Common | Uncommon | Rare | Epic | Legendary |
| --- | --- | --- | --- | --- | --- | --- |
| Deep Reserve | Reserve ammo +% | 30-50% (weight 60) | 50-75% (50) | 75-100% (40) | 100-150% (30) | 150-200% (25) |
| Reclaimer | Kills return % of the bullets that hit that zombie | 15-20% (30) | 20-30% (35) | 30-40% (35) | 40-50% (35) | 50-60% (35) |
| Fabricator | Regenerates % of full ammo every 10 s | 2-3% (10) | 3-4% (15) | 4-5% (25) | 5-7% (35) | 7-9% (40) |

Each cell is the value range, with the roll weight in brackets. What it does in the balance model, for a Reforged Rare Mako PDW: with no affix one load lasts about 3.6 rounds at round 10 and 0.7 at round 20. Fabricator keeps it running on its own up to about round 10. Deep Reserve doubles how long a load lasts in the mid rounds (1.5 rounds at round 20). Reclaimer sits in between. From round 25 every loot gun also needs Resupply drops or Reforger re-buys, the same pressure wall guns get. Tuning lives in the balance sheet, Loot ammo tab.

**Legendary traits (examples).** Chain Reaction: headshot kills explode for 30% of weapon damage. Bottomless: every 15th kill refills the magazine. Overpressure: the first shotgun blast after a reload fires double pellets. Cold Snap: reloading an empty magazine freezes zombies within 4 m. Each legendary gun has one fixed trait plus 3 random affixes.

### How loot changes the existing systems

- **Wall guns** stay, always Common and item level 1. They are your safety net and point farm, never the endgame.
- **Specimen Vault** now rolls a loot item at the current round's item level, with better odds than a zombie drop: Common 40%, Uncommon 30%, Rare 18%, Epic 9%, Legendary 2.5%, Prototype 0.5%. You keep what you take. The pity rule still applies.
- **Reforger** works on any gun, including loot, but its tiers reset at the end of the run. Permanent upgrades happen at the town Workbench.
- **Serums** are unchanged and stay run-only.
- **Points** stay run-only. The persistent currency is **Scrap**, earned by salvaging items and from exfil caches.

## Town hub: Lantern Post

Lantern Post is a walled survivor outpost in a ruined Ardennes village, a short drive from Halcyon Labs. It is the safe place between runs: no zombies, no combat. Each server is self-hosted by a player (for example on a home server) and holds up to 8 players. Everyone on the server shares the town, sees each other walk around, and forms squads of up to 4 to deploy together.

### What the town offers

| Place | What you do there |
| --- | --- |
| Stash | Store loot. 60 slots to start, more slots bought with Scrap |
| Workbench | Salvage items into Scrap. Reroll one affix on an item (Scrap cost rises each reroll). Raise an item's level by 5, up to your character level |
| Quartermaster | Buy Common and Uncommon basics for Scrap. One rotating Rare offer per day. Cosmetics |
| Trainer | Respec your skill tree. Free 3 times, then costs Scrap |
| Contract Board | 3 daily and 3 weekly contracts, such as "Kill 40 Stalkers" or "Exfil from round 20". Rewards XP, Scrap and caches |
| Firing Range | Test any gun from your stash on dummies with damage numbers and a recoil trace |
| Deploy Gate | Pick a map, go solo or with your squad, or join a public match |
| Hall of Records | Leaderboards: best round per map, weekly and all-time |

Market row signs (plan F-74): the four stalls on the main street carry the concept-art names, each fronting a town job. MISSIONS = Contract Board, TRADER "Buy / Sell" = Quartermaster, GUNSMITH "Upgrades / Mods" = Workbench, TECHNICIAN "Serums / Gear" = serum and gear seller (a new town job, not yet in the table; never called "Perks"). The stall jobs themselves come with F-45.

Social basics: see other players' equipped gear (rarity glows on guns and vests), inspect a player, invite to squad, emotes and text chat. No trading in version 1, which keeps loot fair and avoids scams and bots.

### How multiplayer works (design view)

This matches the architecture doc ([Technical Architecture](https://claude.ai/artifact/XNJ12WAbMJAy2mRNPd5PCx)).

- **Godot can do this.** Godot 4 exports a headless dedicated server build (no window, no graphics) from the same project, and its built-in multiplayer (ENet over UDP) handles 8 players easily. No separate server language or engine is needed.
- **One server for town and matches.** One server process holds the town plus up to 2 matches running side by side. Solo play runs the same server code as a private local server in the background, so there is only one code path to build and test. A "host and play" button lets a player host from their own game too.
- **Hosting:** the server ships as a Docker image (with an Unraid template) and as Windows and Linux downloads. The owner sets server.cfg: server name, password, max players (up to 8) and admins. Friends connect by address and port (UDP port forwarding needed on the host's router).
- **Matches:** when a squad (1 to 4 players) uses the Deploy Gate, the same server starts the match. Players who stay in town keep playing there. The server runs at most 2 matches at a time, so all 8 players can be in action at once.
- **Characters:** saved on your own PC, together with your stash, and you take them to any server. The server runs the gameplay and rolls the loot, then tells your game what you earned. No accounts and no server database.
- **Cheating:** no anti-cheat for now. Servers are for friends, and the server is still the one that runs zombies and rolls loot, so most cheats would need the host's help. Anti-cheat can be added later if public servers become a thing.

**Honest cost.** Self-hosted servers with 8 players and no accounts or anti-cheat is far cheaper than a public online game. It is still the hardest part of the project: syncing guns, zombies and loot across players without lag takes real work. That is why it comes after the solo game, with the code made ready for it from P2.

## UI and HUD

The HUD stays small and at the screen edges so the middle is free for aiming. Every element is its own scene so it can be moved or swapped without touching the rest.

| Screen spot | Element | Behaviour |
| --- | --- | --- |
| Top left | Round number | Large, blood-red numeral. Pulses and plays a sting on round change. |
| Bottom left | Serums held | Up to 4 small icons in a row |
| Bottom right | Ammo | Magazine big, reserve small. Turns orange at 25% mag, red when empty. Grenade and tactical counts below. |
| Above ammo | Points | Total, with floating +10 / +100 numbers that stack and fade |
| Bottom centre | Power-up timers | Icon with a shrinking ring for timed drops |
| Centre, below crosshair | Interaction prompt | "Hold F to buy Kestrel SMG (1000)". Grey and shows "Need 1000" when you can't afford it. |
| Centre | Crosshair and hitmarkers | Small dynamic crosshair that opens with spread. Hidden in ADS. |
| Screen edges | Damage | Red arc pointing to the attacker, red vignette under 40 HP |

**Menus.** Main menu, map select, pause, settings, and an end screen with round reached, kills, headshots, points earned and time.

**Accessibility settings from day one.** Field of view (70 to 110), mouse and ADS sensitivity, aim assist for controller, colour-blind modes for hitmarker and drop colours, subtitles for key audio tells ("Stalker shriek, left"), screen shake slider, and a clear UI font. Use Atkinson Hyperlegible Next (free under the Open Font License), which is easier to read for dyslexic players. Text size slider for the HUD.

## Audio and art direction

### Audio

Sound does half the gunfeel and most of the enemy tells, so it gets priority over visuals in early milestones.

**Full design in [Fenlight: Sound Design](sound.md)**, which replaces the notes below where they differ. In short: danger tells always cut through the mix; guns use 4 layers plus a far layer and room tails from reverb zones; 4 music stems fade in with round intensity; one drop sound per loot rarity; a pooled sound manager capped at 48 voices, with only the 8 nearest zombies vocalising and a horde loop for the rest; packs plus scripted synth sounds, every file logged in `docs/CREDITS.md`.

- **Guns:** three layers per shot. A close mechanical crack, a body thump, and a room tail (short in corridors, long and echoing outside). Separate sounds for the mag out, mag in and bolt or slide, timed to the reload animation. The last 5 rounds in a mag get a slightly higher, thinner click to warn you.
- **Zombies:** each type has its own idle, attack and death sounds. Tells (Stalker shriek, Brute thud, Bloater gurgle) are louder than everything else and use 3D position so you can locate them.
- **Round flow:** a low drum and metal sting when a round starts, a short choir-like swell when it ends. Ambient: generator hum, dripping, distant alarms.
- **Music:** dark synth and industrial percussion. Quiet during rounds, a short track during the breather, an intense track for Blackout rounds and Brute spawns.
- **Sources:** Freesound (filter to CC0), the yearly free Sonniss GDC sound bundles (royalty-free), and Kenney audio packs. Every asset's licence is logged in a credits file.

### Art

**Look:** grounded, gritty realism with one strong accent colour. Think wet concrete, rust, cold teal fluorescent light, warm sodium lamps outside, and a sickly bio-green glow wherever the experiment leaked. The green is the game's signature: power-ups, the Vault beacon, Glowers and the Reforger all use it.

**Chosen direction: A, Cold Containment** (picked 2026-11-14). Cold teal-white fluorescents inside, warm sodium outside, bio-green #8DFF3A reserved for the experiment only. Palette, Godot WorldEnvironment settings for the 120 fps budget, zombie and weapon rules, HUD colours and loot rarity hex values live in the [Visual Style Guide](look-rules.md). Rarity colours: Common #D9D9D2, Uncommon #3FE0C8, Rare #3D7DFF, Epic #A64DFF, Legendary #FF8A1C, Prototype #8DFF3A.

- **Rendering:** Godot 4 Forward+ renderer, baked lightmaps for static rooms plus a few real-time lights for flicker and muzzle flashes. Volumetric fog in every area. AgX tonemapping, light film grain, subtle vignette.
- **Textures:** Godot noise shaders first (concrete, rust, wet floor, grime). After v0.1, Poly Haven and ambientCG textures (both CC0) where plain surfaces show up close.
- **Models:** Stage A, up to v0.1: built in code to match the style-guide previews. Godot grey box first, then Blender Python scripts in tools/assets/ that export .glb: a modular room kit, props, guns built from parts (moving parts separate for reloads) and zombie bodies. Stage B, after v0.1: CC0 or CC-BY packs (Quaternius, Kenney, Poly Haven props) or better custom models where it shows, each logged in docs/CREDITS.md. No non-commercial or no-AI licences.
- **Animation:** code-driven first (lurch, foot placement, hit reactions, gun kick and sway) with physics ragdolls on death. Stage B: Mixamo clips (free to use in games) for zombie walks, attacks and deaths, retargeted in Godot, and keyframed reloads.
- **Effects:** muzzle flash, smoke, shell casings, blood puffs, decals, gas cloud and freeze shatter as GPU particles.
- **Rule:** gameplay readability beats realism. Zombie heads must stand out against the background, drops must be visible from 30 m, and every enemy type has a unique silhouette.

## Built to scale: content as data

Every number in this doc lives in a Godot Resource file (.tres), not in code. Code reads the files. To add or tune content you add or edit a file, and the game picks it up. The architecture thread owns the technical detail; this is the design contract it must support.

| Content | Data file | Key fields | To add one |
| --- | --- | --- | --- |
| Weapon | WeaponData | class, damage, head multiplier, fire rate, mag, reserve, ADS time, recoil pattern, sounds, model, vault rarity | New file + model + sounds |
| Enemy | EnemyData | health multiplier, speed, first round, attack damage, special ability scene, sounds | New file + model; ability as a small reusable scene |
| Round rules | WaveRules | count formula, health formula, speed mix, spawn interval, special round rules | Edit numbers |
| Power-up | PowerUpData | effect script, duration, icon, deck weight | New file + small effect script |
| Serum | SerumData | stat changes, cost, icon, jingle | New file (most are pure stat changes) |
| Ammo mod | AmmoModData | on-hit effect, tier 2 and 3 values | New file + effect scene |
| Buyable | BuyableData | cost, prompt text, needs power, unlocks zones | Placed in the map with a file attached |
| Map | MapData | areas, spawn zones, vault spots, wall guns, starting points | New scene + file |

**Design rules that keep it scalable**

1. Stats change through one shared modifier system (serums, ammo mods and power-ups all add modifiers), so new effects never need special cases.
2. Any number a designer might tune is in a data file, with a comment saying what it does.
3. Balance is checked with a debug panel: jump to any round, give points, spawn any enemy, toggle god mode.
4. Every new content type gets one example file and a short how-to in the repo.

**Added for levels and loot:** SkillNodeData (branch, ranks, modifiers), AbilityData (effect scene, cooldown, unlock level), ItemBaseData and RarityData, AffixData (pool, range, scaling), LootTableData (source, chance, rarity floor), and ContractData for the town board. A dropped item is saved as plain data: unique id, base, rarity, item level and its rolled affixes.

## Build roadmap

Build in three stages, in this order: a fun solo wave game, then progression and loot offline, then multiplayer and the town. Each stage ends in something you can play and show. The phase numbers are shared with the [Technical Architecture](https://claude.ai/artifact/XNJ12WAbMJAy2mRNPd5PCx) doc, so both docs talk about the same steps.

_(Diagram not copied: build roadmap · 11 phases in 3 stages.)_

Why this order: shooting and the wave loop are the core and must be fun before anything is added on top. Loot and levels only matter once runs are fun. Online is the most expensive part, so it comes last, but the code is made ready for it from P2 so it never needs a rewrite.

| Phase | Goal | Key features | Done when | Needs | Size |
| --- | --- | --- | --- | --- | --- |
| P0 Foundation | A clean project to build on | Project settings, folder layout, core services, data file loader, debug console, tests, CI | An empty level runs from a fresh clone and the debug panel opens | - | S |
| P1 Gun feel | Shooting feels great | Player controller, camera, ADS, recoil, reloads, sprint, slide, mantle, hit feedback, test range with dummies | Shooting feels tight to you, and every timing is tuned in data files only | P0 | M |
| P2 Wave loop | First real playable | Zombies with pathfinding, rounds and scaling, spawner, points, HUD, game over. Network-ready seams: input as InputFrame data, game state changed only by the authority, session-owned random numbers for loot, a ProgressionService interface, items saved as plain data | Survive rounds 1 to 10 in a gray box map and die | P1 | M |
| P3 Map systems | Everything a round-based map needs | Doors, barricades, wall guns, Specimen Vault, Serums, power switch, Reforger, power-ups, grenades | Every system in this doc works in the gray box, driven by data files | P2 | L |
| P4 Map 1 and look | Release v0.1, solo | Halcyon Labs built and lit, all 5 enemy types, Blackout rounds, audio and music, settings, performance pass | Three solo runs end between round 15 and 30, no unfair deaths, 60 fps (120 fps on an RTX 4080 Super at 1440p High is a later polish gate) | P3 | L |
| P5 Levels and skills | Each run builds your character | XP, levels 1 to 50, skill tree, field abilities, local save profile, end-of-run results screen | A new character reaches level 10 in about 4 runs and feels stronger | P2 (plays best after P4) | M |
| P6 Loot | Release v0.2, offline | Item rarity and affixes, drops, Pack and exfil, loadout, stash, Workbench and Quartermaster as menus | Loot drops feel exciting, and an Epic gun changes how you play | P3, P5 | L |
| P7 Co-op matches | Play with friends | Squads of 2 to 4 players, synced guns, zombies, drops and revives. First tested with one player hosting, using the same server code | Four players finish a run to round 20 with no desync | P4, P6 | L |
| P8 Server package | Anyone can host a server for friends | Docker image, Unraid template, Windows and Linux server downloads, server.cfg (name, password, up to 8 players), admin commands, version check | A friend installs the server from the download, you join it with your own character, and you keep the loot you earn there | P7 | L |
| P9 Town hub | Release v1.0, online | Lantern Post: shared hub for up to 8 players per server, stash, Workbench, Quartermaster, Trainer, Contract Board, Firing Range, Deploy Gate, leaderboards | You and friends meet in town, squad up, deploy, and return with loot | P8 | L |
| P10 Growth | Keep adding content | Sublevel and boss, new maps, more guns and enemies, seasons, maybe trading | Each addition is mostly new data files and scenes, no core rewrite | P9 | Ongoing |

**Sizes** are relative: S is a few evenings, M a couple of weeks, L a month or more of hobby time. Stage 3 alone is about as big as stages 1 and 2 together.

**Open questions for you**

- [ ] Decided: keep the setting (Cold War bunker bio-lab and a village outpost in the Ardennes).
- [ ] Decided: code-built guns in the style-guide look up to v0.1, then upgrade with a pack or better models where it shows.
- [ ] Decided: dying keeps all your loot, like Diablo. Exfil stays only as an optional bonus (more XP and a cache).

## Change log

Design changes since the Nov 14, 2026 copy, newest first. Add one row in the same PR that changes the design: the date, the area, one line on what changed, and where the detail lives. Bug fixes that bring the game back in line with this doc go here only when a number players feel changed.

| Date | Area | Change | Detail |
| --- | --- | --- | --- |
| 2026-11-23 | Run rewards | Pack pickups reserve stash space, and the player chooses any exchange. The grenade-damage implant increases frag damage against enemies. | [Run decisions](../DECISIONS.md) |
| 2026-11-21 | Field abilities | The Sentry is named Watchdog (provisional); its turret shoots heads for 0.4 of max health every 0.6 s within 25 m, so three shots kill anything. The picked ability is chosen under the Research tree. | [field-abilities.md](../plans/field-abilities.md) |
| 2026-11-20 | Loot | Headgear, gloves, backpack and boots now drop (Salvager Cap, Gloves, Pack, Boots), each as often as a vest; guns fall to about 39% of drops. Each rolls 2 prefixes and 2 suffixes from its own pool, with three new lines (Steady aim, Recoil grip, Quick hands). Flat max health from gear and skills is capped at +100. Sets become the five armour pieces. | [affixes.md](affixes.md#gear-affixes), [four-gear-slots plan](../plans/four-gear-slots.md) |
| 2026-11-20 | Town | The stall keepers come alive (provisional look): each has their own idle (Odile leans on her counter, Teun files a part at his vice, Lien types and checks her monitors, Raes stands arms crossed by the board), turns their head to you within 4 m, and greets you with a nod and a raised hand when you talk. The line shows only for you. | [lore.md](lore.md#the-stall-keepers), plan lantern-post-vendors steps 3-4, PRs #393 #394 |
| 2026-11-20 | Skills | The hard caps on the shared stat stack hold skills plus gear; Serums stack on top of them, so Quickhands keeps its full reload boost. | [skill-effects plan](../plans/skill-effects.md), PR #409 |
| 2026-11-20 | Weapons | Frag grenades: hold G to cook (3 s fuse), 1000 damage inside 1.5 m falling to 0 at 7 m, blocked by walls, own frag hurts up to 60, no friendly fire, explosives burst Bloaters. Fixed damage is the person's pick; the rest is provisional. | [frag-grenades.md](../plans/frag-grenades.md) |
| 2026-11-19 | Weapons | BR-12 (Brenner Trench) loads shell by shell, as the balance sheet already says: 0.5 s per shell, the first shell from empty 1.1 s (it also racks the pump), full empty reload still 3.6 s. Reforged keeps the same shell times (9 shells: 5.1 s from empty). Firing mid-reload keeps loaded shells. | [weapons.csv](balance/weapons.csv) Brenner row, plan reload-animations step 2 |
| 2026-11-19 | Loot | Gear from drops can be worn mid-run from the Tab Pack overlay; the old piece swaps into the Pack slot, no heal on a swap. | [wear-gear-mid-run.md](../plans/wear-gear-mid-run.md), F-84 step 1 |
| 2026-11-18 | Story | Story links: every kind of content now has a story reason (zombie types, where guns come from, power-ups, gear, town services, rooms and props). Fixed lore gaps: Fenlight grows outside bodies, the Cordon was the evacuation army before Day 9, where Lantern Post, its tunnel, emblem and green Deploy lights come from. New rule: plans carry a Lore link line (checked by CI). | [lore.md](lore.md#story-links-for-game-content), [lore audit](reviews/lore-audit-2026-11-18.md) |
| 2026-11-18 | Town | Lantern Post camp props and light pass: burning fire barrels (flames, flickering light) with benches round them, snowy supply crates and ammo cases, two FENLIGHT SAMPLES crates of glowing green jars by the Technician, hanging and table lanterns, string lights across the street, split-rail fences, firewood stacks, snow drifts and snowy pines. Stall, board and floodlight bulbs now really glow. | [lantern-post-assets.md](lantern-post-assets.md), plan lantern-post-concept step 5 |
| 2026-11-18 | Town | Lantern Post Deploy gate: the timber palisade gate becomes a concrete wall with a DEPLOY tunnel (green strip lights, hazard pillars, closed blast door 12 m in; players can walk 3 m in), maroon outpost banners, floodlights, a sweeping watchtower spotlight and a lattice radio mast on the ridge. The Deploy board and ready-up vote are unchanged. | [lantern-post-assets.md](lantern-post-assets.md), plan lantern-post-concept step 4 |
| 2026-11-18 | Town | The four stall keepers (provisional): Odile Brandt at TRADER, Teun Maes at GUNSMITH, Dr. Lien Corvelyn at TECHNICIAN, Lieutenant Raes at MISSIONS. Talking gives a short line; shop screens come with F-45. | [lore.md](lore.md#the-stall-keepers), plan lantern-post-vendors |
| 2026-11-18 | Town | Lantern Post market row: four stalls between the lodges named MISSIONS, TRADER "Buy / Sell", GUNSMITH "Upgrades / Mods" and TECHNICIAN "Serums / Gear", mapped to the Contract Board, Quartermaster, Workbench and serum and gear jobs. East side gets log cabins, a watchtower by the gate and lean-to sheds. | [Town hub](#town-hub-lantern-post), [lantern-post-assets.md](lantern-post-assets.md), plan lantern-post-concept step 3 |
| 2026-11-17 | Co-op | Every game is joinable: Enter world opens your own Lantern Post to friends (router port opened automatically), alone it plays like solo; Play solo and Host and play are gone. Joining is only through the Servers screen: saved, recent and LAN servers, add by address, no master server. | [MULTIPLAYER.md](../MULTIPLAYER.md) Worlds and the browser, [ADR 0013](../adr/0013-every-game-joinable.md), PRs #306 #311 #312 #315 #319 |
| 2026-11-17 | UI | Screens follow the person's concept art: the one main action button per screen is bio-green (Enter World, Join Server, Select Character); main menu gets Enter World, Servers, Character, Loadout, Progression, Settings, Exit, a profile card and a news card. | [ui-hud.md](ui-hud.md) UI style, screens 1 and 2 |
| 2026-11-17 | Characters | Character select picks a preset survivor (name, role, bio, 3 small traits) instead of making your own; progress is per survivor (provisional). | [ui-hud.md](ui-hud.md) screen 3, roadmap F-67 |
| 2026-11-17 | HUD | Match HUD gets an always-on health panel (number and bar), an objective list top right, the area name under the round, and grenade and tactical slots by the ammo. No minimap, armour or medkits. | [ui-hud.md](ui-hud.md) screen 10 |
| 2026-11-17 | Gore | Full gore is stronger, picked from renders: blood bursts have 24 flecks (was 12) and each death lays a 1.6x pool plus 2 small splats. Head pops on headshot kills; Gore setting Full / Reduced / Off on the Graphics page. | [game-feel.md](game-feel.md) Blood and gore, plan zombie-sounds-gore step 4 |
| 2026-11-17 | Campaign | Long campaign: maps come in acts of four (Act I = the first four maps), each map has a boss reached through a mid-run Sublevel descent, Lantern Post grows per act, and endgame hooks are named. | [lore.md](lore.md), PR #201, roadmap F-60 |
| 2026-11-16 | Process | Plan first: a feature whose roadmap row says "needed" gets an approved plan in `docs/plans/` before any code. `docs/ROADMAP.md` is the build order. | [PROCESS.md](../PROCESS.md), PR #172 |
| 2026-11-15 | Loot | Zombie loot is personal: each player only sees and picks up their own drops. Every run exit, including death and co-op disconnects, banks the Pack into the stash. | [ADR 0010](../adr/0010-personal-loot-kept-on-death.md), PR #135 |
| 2026-11-15 | Co-op | Co-op uses a trusted client: clients ask, the host or server decides shared state. Host and direct join are on the main menu. | [MULTIPLAYER.md](../MULTIPLAYER.md), [ADR 0003](../adr/0003-trusted-client-co-op.md), PRs #73, #96 |
| 2026-11-15 | Weapons | Kestrel SMG and Talon DMR damage now match the balance sheet (25.65 and 68.4 per bullet); they were about 43% too low. | [weapons.csv](balance/weapons.csv), PR #76 |
| 2026-11-15 | Weapons | Version 1 roster grows from 12 to 22 base guns, all bullet-based. The crossbow and launchers are dropped. | [gun-roster.md](gun-roster.md), PR #67 |
| 2026-11-20 | Audio | Real sounds and music replace the generated placeholders, from free sources only (Sonniss, Kenney, Freesound CC0, Stable Audio on the GPU). No paid packs. | [real-sounds-music.md](../plans/real-sounds-music.md), [sound.md](sound.md#packs-to-evaluate) |
| 2026-11-20 | Skills | Keystone and capstone gates drop from 15/25 to 8/11 points in a branch, because the branches hold only 10 to 14 points today. F-90 adds about 5 skills per branch and puts the gates back to 15/25. | [skill-tree-screen.md](../plans/skill-tree-screen.md), PR #464 |
