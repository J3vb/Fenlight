# Decisions

Three short lists: where the game differs from `docs/design/` on purpose, what
is simplified on purpose, and agent picks the person may change. One line per
entry, at most 300 characters (CI rule `decisions-short`); the linked plan, ADR
or doc has the detail. What is built: `docs/ROADMAP.md` and `docs/plans/`.
Read the entries for the systems you touch, not the whole file.

## Differs from the design on purpose

These win over the design docs (see `docs/design/README.md`).

- **v0.2 before the v0.1.0 tag:** the person played v0.1 solo (2026-11-19) and asked to start v0.2 on 2026-11-20, so roadmap rows that need F-11 may start once F-10 is Done. Game stage is Early Alpha. [ROADMAP](ROADMAP.md)
- **Gun damage:** every gun deals balance-sheet damage x 0.57 (AR 60 -> 34), the prototype's scale, until a balance pass resets the TTK targets. [gun-roster](design/gun-roster.md)
- **Prices:** doors and Serums use the design doc's base prices, not the balance sheet's provisional x2.5. Reforger 5000, refill 2500, Reforged wall ammo 4000 (sheet).
- **Look reference:** AgX instead of ACES; ambient energy 0.2 instead of 0.35 (baked bounce fills shadows); fog albedo light teal-grey, because Godot's fog albedo is the scatter colour. [look-rules](design/look-rules.md)
- **Co-op gear looks:** each client builds its own look and `LookSync` relays it (trusted cosmetics), replacing the server-built appearance model in gear-visuals.md. [ADR 0003](adr/0003-trusted-client-co-op.md)
- **Gear budgets:** vests light 3,000-4,500, medium 4,000-5,500, heavy 4,500-6,000 tris; charms 600-1,300; implants 1,000-1,800; first-person arms up to 10,000. Replaces gear-visuals.md's 3,000 / 300 / 500 estimates.
- **Screens folder:** screen data lives in `content/screens/`, not ui-hud.md's `content/ui/screens/`, because `Content` treats each top folder as one type. [ui-router](plans/ui-router.md)
- **Legendary data:** TraitData is merged into `LegendaryData` (one file per Legendary); a trait is one flat stat line with its own stat name, read by the code that runs it; an unknown trait shows no line, not "Inactive bonus". [legendaries-traits](plans/legendaries-traits.md)
- **Last Rites in solo:** works in co-op only; solo has no downed state with a pistol, so a solo player with it still dies (unless Second Wind or Undying). Fix when: a solo downed state. [legendaries-traits](plans/legendaries-traits.md)
- **Legendary tuning:** Twin Pin children 0.4 s fuse, half radius, clients see only blasts; Lantern Fall 4 m; Cold Snap holds without shatter; Dead Man's Hand has no stagger; Iron Lung streak = kills unhurt; no Choir Mark visual. Provisional. [legendaries-traits](plans/legendaries-traits.md)
- **Knife:** lives in `content/melee/`, not `content/weapons/`, so gun-only code (Vault, loot, grips, viewmodels) never sees it. [core-loop-gaps](plans/core-loop-gaps.md)
- **Synapse:** 50% damage to up to 3 other zombies within 6 m, replacing the roster's 60% chain; its repeated-target ramp is deferred. Cryo Lance: 3 hits freeze 2 s, the next bullet shatters for 50% within 3 m.
- **Ironwood .50:** loot only, overriding the roster's "every base is in the Vault" rule.
- **Double barrels and belts:** Reforged Coachman and Grubber keep two shells and Bastion keeps a fixed belt, overriding the +50% magazine rule; magazine affixes skip them.
- **Alt fire:** `InputFrame.ALT_FIRE` on middle mouse and R3; the planned ping and controller melee bindings are unbound. [controls](design/controls.md)
- **Wren MP:** the Long shot affix stays eligible; the roster's machine-pistol exclusion is deferred because shared affix data stays unchanged.
- **Regen delay affix:** 0.01 s step instead of the design's 0.1 s, so the equal 0.14 s tier boundaries hold.
- **Text size:** 80 to 150%, not 200%, until layouts are checked at that size. Font options (Lexend, OpenDyslexic) wait. [full-settings](plans/full-settings.md)
- **Shotgun hitstop:** the "< 4 m" condition is dropped (`hit_confirmed` has no distance); the "shake from your gun" slider at 0 also turns hitstop off. [game-feel-slice](plans/game-feel-slice.md)
- **Log autoload:** `Log` is an autoload although the architecture doc's table does not list it. [LOGGING](LOGGING.md)
- **Stat caps:** the design's caps (reload +60%, recoil -50%, points +50%, luck +100%) hold skills plus gear; Serum multipliers stack on top (the person's pick). [skill-effects](plans/skill-effects.md)
- **Max health cap (F-71):** flat max health from gear and skills stops at +100 (was 400 in total); Thick Skin sharing it is provisional. Ironhide multiplies the base outside the cap (100 base: 200, with Ironhide 350). [four-gear-slots](plans/four-gear-slots.md)
- **Second Wind:** solo only; "solo" means alone in the world (`Net.is_coop()` false), so a lone listen server plays as solo. [join-any-game](plans/join-any-game.md)
- **Sets (F-71, the person's pick):** a set is exactly five armour pieces: headgear, vest, gloves, backpack, boots. Guns, charm and implant are never set pieces; bonuses stay at 2/3/5. Replaces affixes.md's gun-and-vest set. F-32 builds it. [four-gear-slots](plans/four-gear-slots.md)
- **Gear drop share (F-71, the person's pick):** each new slot's one base weighs 300, as much as the three vests together, so at level 30 Rare guns are about 39% of drops (was 56%) and each new slot about 7%. Weights are data. [four-gear-slots](plans/four-gear-slots.md)

## Simplified on purpose

Each says when to fix it.

- **Navmesh** bakes at load from the blocks. Fix when: the Halcyon layout settles (switch to a baked `.tres`).
- **Specimen Vault:** a fixed per-map `pool` weighted by `crate_weight`, no rarity, affixes or unlock levels; no navmesh rebake when it moves. Fix when: loot reaches the Vault.
- **Zombie AI tiers:** only the re-path interval is tiered. Fix when: the performance pass adds frame-skip and off-screen checks.
- **No Pool autoload:** impacts reuse a 48-node ring; zombies are freed after the corpse fades. Fix when: a stutter is measured. [hot-path-allocations](plans/hot-path-allocations.md)
- **Viewmodel** is a normal mesh at near plane 0.03, not a depth shader, so it can poke into walls. Fix when: wall clipping is reported in play-tests.
- **Procedural animation** for zombies and first-person guns (bob, sway, kick, reload dip). Fix when: real clips are made.
- **Range falloff** uses start and end distances, not a Curve. Fix when: a gun needs a curve.
- **Head hit zone** follows a bone posed in `_process`. Fine for trusted-client hits. Fix when: server-side hit checks or rewind need it on the physics tick.
- **Crawler** is not spawned: by design it is made when explosives take a Shambler's legs. Fix when: grenades exist (F-24, F-27).
- **Whole-tube reloads:** Brenner, Hollis and Atlas reload in one timed action. Fix when: real reload animations exist.
- **Reforger** has Tier I only and swaps instantly. Fix when: Tiers II (ammo mods) and III get a roadmap row.
- **Frag numbers** (3 s fuse, 15 m/s throw, 7 m blast with full damage inside 1.5 m, own damage up to 60, no friendly fire) are provisional picks; the 1000 centre damage is the person's. Fix when: the frag play-test. [frag-grenades](plans/frag-grenades.md)
- **Frag blast** is code-built (flash, fireball, smoke; no .tscn, like HeadPop) on the Weapons bus; the frag in the hand has no throwing-arm swing, only a left-hand hold and flick. Fix when: the frag play-test asks for more. [frag-grenades](plans/frag-grenades.md)
- **Power-ups:** Scavenger's +1 grenade waits; no voice line, tint or drop arpeggio on pickup. Fix when: F-24 grenades, F-04 audio follow-up.
- **Window barriers:** no slot timeout (move to another barrier after 4 s), no real sill. Fix when: co-op crowding at a window needs it.
- **Emergency lighting:** dimmed red ceiling lights only, no separate fixtures or sound. Fix when: the sound world step.
- **Stuck zombies:** relocate replaces the AI doc's repath sidestep and navmesh snap; no louder groan for the last zombies (voice is local). Fix when: relocates show in soak logs.
- **Slide** keeps the normal 0.18 s sprint-out block before hip fire. weapon.gd is split now (F-79 step 7), so this is a feel call. Fix when: the feel play-test asks for firing straight out of a slide. [game-feel-slice](plans/game-feel-slice.md)
- **Co-op hit bounds** use Content weapon data, not the held inventory (weapon switching is local). Fix when: a server checks loadouts (P8).
- **Loadout trust:** the server does not check that a client owns the gear it sends (friends-only servers). Fix when: public servers (P8). [item-effects-server](plans/item-effects-server.md)
- **All-guns gear stats (F-71 step 1):** non-item guns get gear damage, recoil and reserve through F-20's `ItemInstance.fit_player_gun` and `ItemLoadout.refit_guns`, not a new `Weapon.refit`; swap time also reads the raised gun's own handling line. [four-gear-slots](plans/four-gear-slots.md)
- **New slots not drawn yet (F-71):** headgear, gloves, backpack and boots drop, roll and give stats but have no GearVisual until F-70; their stash icons are flat placeholders from `tools/assets/placeholder_gear_icons.py`. Fix when: F-70 steps 2-3. [four-gear-slots](plans/four-gear-slots.md)
- **Six dormant gear lines:** Explosion guard, Grab escape, Fast revive, Grenade damage, Extra grenade and Scrap find still roll on vest, charm or implant with no reader; they stay off the new slots. Fix when: grabs, revive tuning, grenades, scrap. [four-gear-slots](plans/four-gear-slots.md)
- **Skill rules (provisional):** Execution Line checks health before the hit; Dead Center refunds a round to the gun in hand on any headshot kill; Undying works only without Second Wind and costs every Serum; Scrounger skips the revive reward. [skill-effects](plans/skill-effects.md)
- **Skills waiting on their feature:** Sturdy only adds its stat; Execution Line has no Brute rule. Overtime lengthens timed power-ups by the collector's seconds (team-wide timer). Gadgeteer shortens field ability cooldowns (F-22). Fix when: F-24, F-30. [skill-effects](plans/skill-effects.md)
- **Field abilities (provisional):** key X (F is interact); the Research row picks one (saved at once, not by Confirm), else the highest unlocked; Shock Pulse pushes at 6 m/s and only holds rising or window zombies. Fix when: play-tests. [field-abilities](plans/field-abilities.md)
- **Decoy Siren canister (provisional):** a grey-box can with a blinking alarm light, no Tripo model yet; lured zombies at a window keep tearing planks. Fix when: the canister model's own PR. [field-abilities](plans/field-abilities.md)
- **Watchdog turret (provisional):** grey-box post and gun, no Tripo model yet; each client's turret picks its own target and shows its own shots from synced zombies (no show_turret_shot message). Fix when: the turret model's PR. [field-abilities](plans/field-abilities.md)
- **Hold-to-buy** stays a tap. Fix when: accidental buys show in play-tests.
- **Loot extras:** no supply or exfil caches, no gun comparison in the pickup prompt, no trading; sets and `proc` lines save but do not run. Fix when: their loot batches. [legendaries-traits](plans/legendaries-traits.md)
- **Run loadout:** the equipped Primary is not given at spawn (the round-5 Drop Locker is not built). Fix when: the Drop Locker.
- **Skill tree:** Research opens from the main menu only (no K key or Trainer), Reset all is free, gates are 8/11 not 15/25, and the server checks only the 54-point total, not level or gates. Fix when: F-45 (Trainer, Scrap), F-90 (nodes). [skill-tree-screen](plans/skill-tree-screen.md)
- **Teammate animations:** one two-handed rifle pose and one reload clip for every gun; a remote muzzle flash plays at the owner's first-person muzzle. Fix when: F-41 follow-ups.
- **First-person hands:** fingers are fixed curls, no trigger-pull or magazine clips; the Corvid bolt only kicks back. Fix when: real clips.
- **Player body:** some cloth clipping in motion, a soft face, a ragged beard bit near the ear. Fix when: F-70 step 6. [ADR 0015](adr/0015-baked-player-body.md)
- **Gear looks:** set counts, crests, dyes content and effects are not built; zombies have no dye or rarity. Fix when: their gear steps. [player-gear-concept](plans/player-gear-concept.md)
- **Music:** one generated bed and drive, no stems, stingers, ducking or `music_config.tres`. Fix when: the music step.
- **Sound:** remote players' footsteps are silent; no Foley or Tells bus, horde loop or occlusion; clients do not hear plank tears. Fix when: the sound foundation step.
- **Ambience** sends to SFX, so the Effects slider covers it; no separate Ambience slider and no power-off or Blackout bed swaps. Fix when: the audio settings pass.
- **Gore:** no stump cap, limb loss or wound decals; blood pools are quads, not Decals (Compatibility renderer). Fix when: a gore follow-up.
- **Settings:** controller rebinding, presets and action contexts wait; one key, one action everywhere; a plain Esc cancels a rebind. Fix when: controller support. [control-rebinding](plans/control-rebinding.md)
- **Settings Revert** puts back the values from when the screen opened, but not key bindings; each action keeps its own Reset. Fix when: players expect Revert to undo a rebind. [full-settings](plans/full-settings.md)
- **Hub:** one place per server, one Deploy board per map, the whole server is one squad, a listen host decides when to return. Fix when: a second map. [coop-full-match](plans/coop-full-match.md)
- **Server browser:** no Map, Players or search filters, no map picture, no password; a server goes into Recent when a join starts. Fix when: P8 servers. [join-any-game](plans/join-any-game.md)
- **Launcher:** no Windows-runner check, no drain file, no install-size readout. Fix when: F-65 step 8. [client-server-updates](plans/client-server-updates.md)
- **Game feel:** the gun in hand when a kill confirm arrives picks the hitstop class; the killed zombie's pose does not freeze; viewmodel kick stays in WeaponData. Fix when: F-42.
- **Character screen:** no drag and drop, junk marking or extra tabs. Fix when: the stash UI pass.
- **Debug console:** no god mode. Fix when: a public damage-immunity API exists.
- **Halcyon surfaces:** one planar projection instead of triplanar. Fix when: a surface shows stretching. [halcyon-surfaces](plans/halcyon-surfaces.md)
- **Lightmaps:** Halcyon Labs at texel scale 1.5 (not 2), F-68 bake 19.3 MiB, test budget 20 MiB (the person's call); 197-439 avg fps at 1440p High, 24 zombies. Lantern Post first bake 17.9 MiB. Fix when: Git LFS or the GPU bake step. [plan](plans/halcyon-concept-pass.md)
- **Lantern Post to the concept art:** bake ambient is the look colour, not the sky; avg fps 302-468 baked High. Street view 2,639 draw calls, not 600: each player's flashlight keeps its shadow (person's pick 2026-11-19, fps is 2.5x target). [plan](plans/lantern-post-concept.md)
- **Lantern Post stalls:** Technician, Gunsmith and Trader are Tripo models with our own sign boards; Missions keeps the code-built frame until a Tripo version exists; the Deploy gate stays code-built (person's pick 2026-11-19). [tripo-models](plans/tripo-models.md)
- **Lantern Post walls:** the whole town wall is the concrete Deploy gate wall (gate_wall sections), not the palisade of the concept; the sky mountains are three peaked ranges (person's pick 2026-11-19). [hub plan](plans/lantern-post-hub.md)
- **Wall guns:** BR-12 keeps its stock wrist (no pistol grip); VX-9, BR-12 and MR-28 still use the shared surface shader (AR-17 is baked). Fix when: F-75 bakes them. [guns-concept](plans/guns-concept.md)
- **Damage numbers:** Siphon shows none (damage is server-side); a host can show overkill from later pellets. Fix when: a player asks for them.
- **No Git LFS:** binaries in plain git; the lines to switch it on are in `.gitattributes`. Fix when: asset packs arrive.

## Provisional picks

Agent picks the person may change.

- **Early drops:** zombies drop loot at 5% in rounds 1-5 (then the 1.5% + 0.1%/round curve) and power-ups at 5% a kill, not 2.5%, so a solo run sees ~3 items and ~3 power-ups through round 5. Provisional, needs a play-test. [game-design](design/game-design.md)
- **EGM plugin:** vendored at `.agents/plugins/egm/` and enabled per machine by the session hook (local settings, no machine path committed). The Codex repo marketplace source path is an agent pick, not yet tried in Codex. [CREDITS](CREDITS.md)
- **Gun feel:** falloff ranges, spread, recoil and empty reloads not in `roster.csv` (Kestrel, Talon, vault batch A1, Bastion, batch B rifles, Wren, Siphon, Cryo Lance, Synapse). Talon head x3.0 and Atlas Auto's strong DPS wait for play-tests.
- **Siphon:** 10 m/s orb, 3 s well, at most 12 zombies, 6 m pull, two live wells per player, Vault weight 0.05.
- **Wearing gear mid-run:** the piece you take off goes into the same Pack slot; swaps never heal; vest icons show the rest-pose shoulder pads ([plan](plans/wear-gear-mid-run.md)).
- **FOV:** horizontal degrees at 16:9, 70-120, default 110 (about 78 vertical); ADS FOV stays vertical.
- **Serums:** every Med Dispenser needs power; no limit on Serums held. Scavenger ammo pack chance 5% (10% gave too much ammo in the first play-test).
- **Exfil and sprint:** the 60 s exfil hold pauses, not resets, when nobody is in range; sprint refills over 3 s after stopping early.
- **Mantle:** reach 0.45 m, 0.22 s + 0.18 s per metre (longest under 0.6 s), 0.3 s window after a jump press, 60% of it rising, leaves at half walk speed. [mantle](plans/mantle.md)
- **Crouch** stays a toggle by default; aim and sprint default to hold.
- **Gear bases:** names (Lantern Rig ... Pell Relay), all unlocked at level 1 with drop weight 100. Skill tree rows and columns are provisional too.
- **Signal in the Static:** pitches 0.75 / 1.0 / 1.3, an 8 s hum gap, no hint text.
- **Halcyon atmosphere:** spark gaps 3-9 s and a 30 s Containment klaxon. Emergency lights at 30% red-orange, back on in a 0.6 s ragged wave.
- **Footsteps:** one step per 0.5 s walking, 0.34 s sprinting, 0.72 s crouched; landings silent under 3 m/s.
- **HUD:** XP bar placement, the 90 px / 0.6 s level-up ring, a 3-row drop feed; "Crits only" damage numbers show headshots until a crit stat exists.
- **HUD vitals (provisional):** 5 health segments of max/5 each, no health number or portrait (the 2026-11-20 concept has none). [hud-concept](plans/hud-concept.md)
- **HUD gun icons (provisional):** one silhouette per gun class (pistol, smg, rifle, shotgun, lmg, sniper, special, knife), not per gun; Reforged copies share it. [hud-concept](plans/hud-concept.md)
- **HUD round counter and compass (provisional):** "ROUND n" top right at 40 px (ui-hud token says 72, the concept is smaller); compass north = world -Z on every map; both hidden until the first round. [hud-concept](plans/hud-concept.md)
- **Halcyon concept pass (F-68):** kitchen fires as the Mess Hall's warm accent, the existing hazard orange (not yellow) on the tank railings, the catwalk office not walkable, pods at leak-glow strength, one steel material on the ceiling models. Look signed off 2026-11-19.
- **Glower (F-28):** 1.7 m tall; veins glow bio-green at strength 2 where the baked albedo is green; chitter, swipe and death sounds generated in `zombie_sfx.py` (no free pack download from the cloud). [blackout-glowers](plans/blackout-glowers.md)
- **Blackout darkness (F-28):** a Blackout takes the LightmapGI data off (works in Forward+ and Compatibility) and drops ambient light to 25%; ceiling and emergency lights go fully dark; Fenlight leaks, fire, signs and flashlights stay. [blackout-glowers](plans/blackout-glowers.md)
- **Blackout schedule (F-28):** first Blackout exactly round 6; the next pack waits spawn interval x pack size; the Resupply drops at the end of a scheduled Blackout round only (debug `blackout on|off` never changes that). [blackout-glowers](plans/blackout-glowers.md)
- **Model looks:** skinned zombies, gear finishes, vest frames, first-person arms, teammate clips and the launcher screen are agent looks until the person sees them.
- **Tripo settings:** `tripo_make.py` asks for model v3.1, PBR, detailed texture, standard geometry (a 0.9 m prop: 40 credits); `body_tarp` goes in `props/`, not `dressing/` (intake prop budget 2,000). [tripo-models](plans/tripo-models.md)
- **Supply Crate:** a plain box with a teal strip, not a model; anyone opens it, only the opener takes the gun; it rolls the level Vault's pool for free and vanishes 25 s after landing unless opened. [more-power-ups](plans/more-power-ups.md)
- **Power-up timers:** team-wide, a re-pickup resets to full time; Payday doubles hit and kill points only (not repairs or the round bonus); only kills by a player roll drops. [more-power-ups](plans/more-power-ups.md)
- **Overkill and Stasis:** Overkill raises a hit to the zombie's health after Synapse and Cryo (their splash stays normal); Stasis freezes only zombies alive at pickup, hits on them do normal damage and never Cryo-freeze or shatter. [more-power-ups](plans/more-power-ups.md)
- **Purge and Scrap Kit:** Purge kills have no attacker (no kill points, XP, loot or drop rolls; the round still counts them); team points go to every player and are not doubled by Payday; Purge glows Rare blue #3D7DFF since bio-green is Resupply's. [more-power-ups](plans/more-power-ups.md)
- **Hold to repair:** one plank every 0.6 s while interact is held, tap still works; the 0.3 s hold-to-buy in `controls.md` is not built.
- **Player names:** up to 16 Latin letters, digits, spaces and - _ . ' ; default "Survivor"; duplicates allowed; set on the Character screen before joining. See [player-names](plans/player-names.md).
- **Halcyon machines (F-83):** one Med Dispenser model for all 8 Serums with one teal glow (no per-Serum colour); exfil hatch model squashed to 14 cm over the old thin floor box so players walk over it; Reforger glow is a thin front strip. [plan](plans/halcyon-machines-fill.md)
- **Halcyon small life (F-83 step 4):** drips already existed (F-61), so only fan, PA and papers are new; PA crackles on a fixed 29 s timer, not a random 20-40 s; fan turns with an AnimationPlayer like the beacons, not _process. [plan](plans/halcyon-machines-fill.md)
- **Stall keeper heights (provisional):** Odile 1.66 m, Teun 1.80 m, Lien 1.68 m, Raes 1.73 m (`height` in [vendors.json](../tools/assets/tripo/vendors.json)); the code-built Quartermaster and `town_npcs/` builder are gone. [tripo-models](plans/tripo-models.md)
- **Stall keeper clips (F-76):** keepers carry only the five keeper clips (`clips: keeper`), not the 12 player clips; hand spots scale with arm length, counter hands palm down. Look is an agent pick until the person sees the GIFs. [lantern-post-vendors](plans/lantern-post-vendors.md)
- **Keeper spots (F-76, provisional):** the Tripo stalls are packed to chest height, so each keeper stands inside the stall on a hidden 0.2-0.3 m step (Missions on the floor); the talk area reaches 0.25 m past the stall collider. Card asked. [lantern-post-vendors](plans/lantern-post-vendors.md)
- **Reload motion (F-85):** empty reloads press the bolt catch above the well for every gun (no charging-handle pull: crossing the receiver flipped the elbow); the tactical swap shows the same magazine low in frame. Feel signed off 2026-11-20. [reload-animations](plans/reload-animations.md)
- **BR-12 Reforged reload (F-85):** keeps the base shell times like every Reforged gun keeps its reload, so its 9 shells take 5.1 s from empty (was 3.6 s for a full reload). [reload-animations](plans/reload-animations.md)
- **Launcher game folder (F-82):** the game lives in the launcher's own app data folder (`%LOCALAPPDATA%\com.experimentundead.launcher\game\`), not `Fenlight\`, so Tauri's uninstaller "delete app data" box removes it with no custom NSIS code. [separate-launcher](plans/separate-launcher.md)
- **First-person charm:** hangs from a `CharmMount` on the left rail just in front of the support hand, out of the ADS sight line; hidden while a sidearm is in hand; a spring swing, no physics. [gear-first-person](plans/gear-first-person.md)
- Content fingerprint skips Texture2D fields (HUD icons): the dedicated server export strips textures, so their paths differ and joins were refused. Textures are client art only ([F-87](plans/hud-concept.md)).
- **Rename to Fenlight:** players see Fenlight; game exe/pck names, the launcher app id and data folder, and the `experiment-undead-server` image keep the old name so installs and servers keep working. Saves copy over once. [RELEASING](RELEASING.md)
- **Menu brush colour (F-88):** the concept art's orange brush on the selected menu row is burnt orange #D9662B, not Legendary #FF8A1C, and the restyled menus drop the one-green-main-button rule. Provisional. [front-end-concept](plans/front-end-concept.md)
- **Server drain (F-65 step 8, F-82 step 4b):** the game side (drain file, `SERVER_UPDATING`, exit code 3) is built with the launcher's hosted-server updates; the Docker entrypoint's auto-update half of step 8 is still to build. [client-server-updates](plans/client-server-updates.md)
- **New slot pools (F-71):** Headgear = head and aim, Gloves = handling, Backpack = carrying, Boots = moving, 2 prefixes and 2 suffixes each; Steady aim and Recoil grip are gear prefixes; names Salvager Cap, Gloves, Pack and Boots. [four-gear-slots](plans/four-gear-slots.md)
- **Loadout tabs (F-88):** tabs filter only the stash; all nine slots stay on the figure. FIELD GEAR lists every stash item that is not a gun, so items with a missing base still show. [front-end-concept](plans/front-end-concept.md)
- **Launcher look (F-82 step 5, provisional):** news is `launcher/news/news.json` read from `main` (built-in copy offline); the backdrop is the Grauwald keyshot (Halcyon has no outside render yet); Host a server is its own sidebar page. [separate-launcher](plans/separate-launcher.md)
- **Tripo Shamblers, Bloater (F-86, provisional):** Walkers show the lab tech or guard look from `hash(net_id)`; all Tripo zombies share the vein glow; Bloater pods swell 5 cm on a hit (shader, no Belly mesh). [tripo-zombies](plans/tripo-zombies.md)
- **Tripo Crawler (F-86, provisional):** lab tech Shambler cut at mid-thigh, capped, laid prone (`tripo_intake.py --crawler`); 5,000-9,000 tris; 1.16 m long (old one over 1.2), so its test asks > 1.1 m. [tripo-zombies](plans/tripo-zombies.md)
- **Launcher install folder (F-82 step 6, provisional):** the game goes into a `Fenlight` folder inside the picked one; Install needs 2.5x the zip free; the folder is picked only before the first install; updates still install on their own. [separate-launcher](plans/separate-launcher.md)
- **Launcher channels (provisional):** Stable plays only stable installs, so Test back to Stable installs the stable build; an install never prunes the version it just installed. [separate-launcher](plans/separate-launcher.md)
- **Pre-merge review:** a fresh subagent in the author's own session (no API cost), not the paid Claude review workflow, which stays manual. CI only checks that a ready PR has a filled `Review:` line; it cannot prove the review ran. [skill](../.agents/skills/pre-merge-review/SKILL.md)
- **Level props:** the Missions Board uses a printed survey atlas. Intact tanks use translucent fluid. The Halcyon generator uses a painted and worn metal atlas for both its Blender preview and its Godot material. [Look rules](design/look-rules.md)
