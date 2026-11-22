## Seeded personal rolls and ENet owner-only delivery/pickup in one process.
extends GutTest

const PLAYER: PackedScene = preload("res://systems/player/player.tscn")
const WALKER: EnemyData = preload("res://content/enemies/zombie_walker.tres")
const BLOATER: EnemyData = preload("res://content/enemies/zombie_bloater.tres")

var session: GameSession
var service: LootService
var _port: int
var _sides: Array[GameSession] = []
var _loot_before: Dictionary


func before_each() -> void:
	_port = TwoPeers.next_port()
	_loot_before = Content._by_type[&"loot"].duplicate()
	Content._by_type[&"loot"][&"test_loot_luck"] = "res://tests/fixtures/loot/test_loot_luck.tres"
	session = GameSession.new()
	autofree(session)
	session.director = WaveDirector.new()
	autofree(session.director)
	session.director.round_number = 17
	session.rng.seed = 73
	service = LootService.new()
	service.session = session
	autofree(service)


func after_each() -> void:
	_sides.reverse()
	for side: GameSession in _sides:
		CoopSide.close(side)
	_sides.clear()
	Content._by_type[&"loot"] = _loot_before


func test_fixed_seed_repeats_the_complete_drop_stream() -> void:
	service.drop_chance_override = 1.0
	var expected: Array[Dictionary] = []
	for index: int in 100:
		expected.append(service.roll_drop(WALKER, 50, 0.2))
	session.rng.seed = 73
	for index: int in expected.size():
		assert_eq(service.roll_drop(WALKER, 50, 0.2), expected[index])


func test_unlock_level_gates_weapon_and_gear_pool() -> void:
	var bastion: WeaponData = Content.weapon(&"bastion_lmg")
	assert_false(LootService.eligible_bases(19, &"rare").has(bastion))
	assert_true(LootService.eligible_bases(20, &"rare").has(bastion))
	assert_false(LootService.eligible_bases(50, &"common").has(bastion), "rarity floor still applies")
	var gear: GearBaseData = Content.get_item(&"loot", &"vest_light") as GearBaseData
	var original: int = gear.unlock_level
	gear.unlock_level = 12
	var locked: bool = LootService.eligible_bases(11, &"rare").has(gear)
	var unlocked: bool = LootService.eligible_bases(12, &"rare").has(gear)
	gear.unlock_level = original
	assert_false(locked)
	assert_true(unlocked)
	for base: Resource in LootService.eligible_bases(50, &"rare"):
		if base is WeaponData:
			assert_false(String((base as WeaponData).id).ends_with("_reforged"))


func test_new_gear_slots_each_drop_as_often_as_vests_and_guns_fall_to_two_fifths() -> void:
	var weights: Dictionary[StringName, float] = {}
	var total: float = 0.0
	for base: Resource in LootService.eligible_bases(30, &"rare"):
		var slot: StringName = &"gun" if base is WeaponData else StringName((base as GearBaseData).slot)
		weights[slot] = weights.get(slot, 0.0) + LootService._weight(base)
		total += LootService._weight(base)
	assert_almost_eq(weights[&"gun"] / total, 0.39, 0.02, "guns")
	for slot: StringName in [&"headgear", &"gloves", &"backpack", &"boots"]:
		assert_almost_eq(weights.get(slot, 0.0) / total, 0.07, 0.01, String(slot))
		assert_eq(weights.get(slot, 0.0), weights[&"vest"], String(slot) + " drops as often as a vest")


func test_round_sets_item_level_and_caps_at_fifty() -> void:
	service.drop_chance_override = 1.0
	for round_number: int in [1, 17, 50, 83]:
		session.director.round_number = round_number
		for index: int in 20:
			assert_eq(service.roll_drop(WALKER, 1).get("ilvl"), mini(round_number, 50))


func test_source_chances_follow_enemy_data() -> void:
	for round_number: int in [6, 10, 40]:
		var curve: float = minf(0.015 + round_number * 0.001, 0.05)
		assert_almost_eq(LootService.drop_chance(WALKER, round_number), curve, 0.0001, "walker round curve")
	for round_number: int in [1, 3, 5]:
		assert_eq(LootService.drop_chance(WALKER, round_number), LootService.EARLY_CHANCE, "early-run boost")
	assert_almost_eq(LootService.drop_chance(WALKER, 6), 0.021, 0.0001)
	assert_almost_eq(LootService.drop_chance(WALKER, 100), 0.05, 0.0001)
	assert_eq(LootService.drop_chance(BLOATER, 1), 0.05)
	assert_eq(LootService.drop_chance(BLOATER, 40), 0.05)


## Bug: a solo run to round 5 often found no gear (about 0.8 expected drops); the boost makes several likely.
func test_a_solo_run_finds_several_items_by_round_5() -> void:
	var rules: WaveRules = load("res://content/waves/default_waves.tres") as WaveRules
	var expected: float = 0.0
	for round_number: int in range(1, 6):
		expected += rules.get_enemy_count(round_number) * LootService.drop_chance(WALKER, round_number)
	assert_gt(expected, 3.0, "expected loot drops in rounds 1-5")


func test_enemy_with_unknown_id_uses_its_own_chance_and_rarity_floor() -> void:
	var boss: EnemyData = EnemyData.new()
	boss.id = &"test_boss"
	boss.loot_drop_chance = 1.0
	boss.loot_min_rarity = &"rare"
	assert_eq(LootService.drop_chance(boss, 1), 1.0)
	for index: int in 100:
		var drop: Dictionary = service.roll_drop(boss, 50)
		assert_false(drop.is_empty(), "always drops")
		assert_gte(ItemRoller.RARITIES.find(StringName(drop.get("rar", ""))), ItemRoller.RARITIES.find(&"rare"))


func test_prototypes_are_fixed_and_only_in_their_rarity_pool() -> void:
	var pool: Array[Resource] = LootService.eligible_bases(50, &"prototype")
	assert_gt(pool.size(), 0)
	for base: Resource in pool:
		assert_true(base is WeaponData)
		assert_true((base as WeaponData).loot_tags.has(&"prototype"))
	var item: Dictionary = service._prototype(pool[0] as WeaponData)
	assert_eq(item.aff, [])
	assert_eq(item.imp, ["fabricator", 1.0])
	assert_eq(item.rar, "prototype")


func _make_side(side_name: String) -> LootService:
	var side: GameSession = CoopSide.make(self, side_name, [&"loot"])
	_sides.append(side)
	return side.loot


func _add_player(loot: LootService, owner_id: int) -> Player:
	var owner_player: Player = PLAYER.instantiate() as Player
	owner_player.name = str(owner_id)
	owner_player.set_multiplayer_authority(owner_id)
	owner_player.get_node("PoseSync").free()
	loot.session.level.add_child(owner_player)
	owner_player.set_physics_process(false)
	return owner_player


func test_drop_reaches_only_its_owner_and_pickup_only_changes_their_pack() -> void:
	var server: LootService = _make_side("LootHost")
	var client: LootService = _make_side("LootClient")
	assert_eq(TwoPeers.host(server, _port, 2), OK)
	assert_eq(TwoPeers.join(client, _port), OK)
	await wait_until(func() -> bool: return server.multiplayer.get_peers().size() == 1, 5.0, "connected")
	var client_id: int = client.multiplayer.get_unique_id()
	var host_player: Player = _add_player(server, 1)
	_add_player(server, client_id)
	_add_player(client, 1)
	var client_player: Player = _add_player(client, client_id)
	server.player = host_player
	client.player = client_player
	client_player.loadout_sync.gear = [{"v": 1, "uid": "charm", "base": "charm", "aff": [["test_loot_luck", 1, 1.0]]}]
	client_player.loadout_sync.send_loadout()
	var server_copy: Player = server.session.players.find_player(client_id)
	await wait_until(
		func() -> bool: return LootService.player_luck(server_copy, 1) == 0.2, 3.0, "charm luck counts on the server"
	)

	service.drop_chance_override = 1.0
	var item: Dictionary = service.roll_drop(WALKER, 1)
	watch_signals(Events)
	server.send_drop(client_player.get_multiplayer_authority(), item, Vector3.ZERO)
	await wait_until(func() -> bool: return client.get_child_count() == 1, 3.0, "owner received drop")
	assert_eq(server.get_child_count(), 0, "host cannot see the client's drop")
	assert_signal_emit_count(Events, "loot_dropped", 1, "only the owner announces the drop")
	assert_eq(get_signal_parameters(Events, "loot_dropped"), [client_player, item])
	var drop: LootDrop = client.get_child(0) as LootDrop
	drop.interact(host_player)
	assert_true(client.pack.items.is_empty(), "other owner cannot take the item")
	assert_true(drop.is_local(), "the owning client picks it up itself, no server request")
	drop.interact(client_player)
	assert_eq(client.pack.items, [item])
	assert_true(server.pack.items.is_empty())
	await wait_process_frames(2)
	assert_false(is_instance_valid(drop))
	server.send_drop(1, item, Vector3.ZERO)
	assert_eq(server.get_child_count(), 1, "host uses the same local receiver")
	assert_eq(client.get_child_count(), 0, "host drop is private too")
	server._banked = true
	server.send_drop(1, item, Vector3.ZERO)
	assert_signal_emit_count(Events, "loot_dropped", 2, "no drop and no feed row after banking")


func test_luck_combines_gear_and_rounds_and_caps_at_one() -> void:
	var owner_player: Player = Player.new()
	autofree(owner_player)
	owner_player.stats.add_modifier(&"loot_luck", "increased", 0.2, &"charm")
	assert_eq(LootService.player_luck(owner_player, 1), 0.2)
	assert_almost_eq(LootService.player_luck(owner_player, 20), 0.4, 0.0001)
	assert_eq(LootService.player_luck(owner_player, 100), 1.0)


func test_server_loads_every_loot_base_before_the_first_drop() -> void:
	Content.reload()
	add_child(service)
	for type: StringName in [&"weapons", &"loot"]:
		for id: StringName in Content.ids(type):
			assert_true(Content._loaded.has(Content._by_type[type][id]), "%s %s loaded at start" % [type, id])


func test_legendary_pool_keeps_only_bases_with_a_legendary() -> void:
	var pool: Array[Resource] = LootService.eligible_bases(50, &"legendary")
	assert_true(pool.has(Content.weapon(&"rifle_ar")), "Tidewater's base stays")
	assert_true(pool.has(Content.get_item(&"loot", &"implant_relay")), "Twin Pin's base stays")
	assert_false(pool.has(Content.weapon(&"sentry_br3")), "a base with no Legendary is left out")
	assert_true(LootService.eligible_bases(50, &"epic").has(Content.weapon(&"sentry_br3")), "other rarities keep it")
	for base: Resource in pool:
		var id: StringName = (base as WeaponData).id if base is WeaponData else (base as GearBaseData).id
		assert_false(ItemRoller.legendaries_for(id).is_empty(), String(id))


func test_legendary_drops_are_named_and_carry_a_trait() -> void:
	var boss: EnemyData = EnemyData.new()
	boss.id = &"test_legend_boss"
	boss.loot_drop_chance = 1.0
	boss.loot_min_rarity = &"legendary"
	var seen: int = 0
	for index: int in 80:
		var drop: Dictionary = service.roll_drop(boss, 50)
		if drop.get("rar") != "legendary":
			continue
		seen += 1
		var named: LegendaryData = ItemInstance.legendary_of(drop)
		assert_not_null(named, "every Legendary drop has a trait")
		if named:
			assert_eq(named.base_id, StringName(drop.get("base", "")))
	assert_gt(seen, 0, "the floor rolls some Legendaries")
