## Real match saves preserve character XP and inventory across banking and scene restarts.
extends GutTest

const SESSION: PackedScene = preload("res://tests/integration/character_save_session.tscn")
const ID: StringName = &"test_character_session"
const START_XP: int = 450
const EMPTY_LOADOUT: Dictionary = {
	"primary": {},
	"sidearm": {},
	"vest": {},
	"charm": {},
	"implant": {},
	"headgear": {},
	"gloves": {},
	"backpack": {},
	"boots": {},
}

var session: GameSession
var player: Player
var _path: String = CharacterProfile.directory() + "test_character_session.json"


func before_each() -> void:
	_remove_files()
	var profile: CharacterProfile = CharacterProfile.load_or_create(ID)
	profile.total_xp = START_XP
	assert_eq(profile.save(), OK)
	session = SESSION.instantiate() as GameSession
	add_child_autofree(session)
	await wait_until(func() -> bool: return session.level.is_navigation_ready, 10.0, "navmesh ready")
	session.director.stop()
	session.loot.drop_chance_override = 0.0
	player = session.get_players()[0]


func after_each() -> void:
	get_tree().paused = false
	_remove_files()


func _remove_files() -> void:
	for path: String in [_path, _path + ".tmp"]:
		if FileAccess.file_exists(path):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(path))


func test_kill_and_round_xp_survive_game_over_and_next_session() -> void:
	assert_eq(session.progression.get_level(player), 1)
	var zombie: Zombie = session.spawner.spawn(Content.enemy(&"zombie_walker"), 1, session.wave_rules)
	assert_not_null(zombie)
	session.director.round_number = 1
	session.director.phase = WaveDirector.Phase.CLEARING
	watch_signals(Events)
	zombie.health.take_damage(DamageInfo.create(10000.0, player))
	await wait_for_signal(Events.round_ended, 2.0)
	var run_xp: int = zombie.data.xp_reward + session.progression.rules.round_clear_xp_per_round
	assert_eq(session.progression.get_xp(player), run_xp)
	player.take_damage(DamageInfo.create(10000.0, null))
	assert_true(session.is_over)
	await wait_for_signal(Events.game_over, 2.0)
	var stats: Dictionary = get_signal_parameters(Events, "game_over")[0]
	assert_eq(stats["start_total_xp"], START_XP)
	assert_eq(stats["total_xp"], START_XP + run_xp)
	assert_eq(int(SaveFile.read(_path)["total_xp"]), START_XP + run_xp)
	session.match_end.bank_run_xp()
	assert_eq(int(SaveFile.read(_path)["total_xp"]), START_XP + run_xp)
	session.free()
	session = SESSION.instantiate() as GameSession
	add_child_autofree(session)
	player = session.get_players()[0]
	assert_eq(session.progression.get_xp(player), 0)
	assert_eq(session.progression.get_total_xp(player), START_XP + run_xp)
	assert_eq(session.progression.get_level(player), 2)


func test_recap_excludes_starting_points_spending_and_refunds() -> void:
	for index: int in 25:
		session.economy._on_enemy_damaged(null, DamageInfo.create(1.0, player))
	assert_true(session.economy.try_spend(player, 750))
	assert_eq(player.wallet.points, 0)
	player.wallet.add(100)  # A refund or grant is not an earning.
	session.director.round_number = 1
	player.take_damage(DamageInfo.create(10000, null))
	await wait_until(func() -> bool: return UI.top() == &"results", 2.0, "results shown")
	assert_eq(_results().points_label.text, "250")
	assert_eq(_results().round_label.text, "1  New best")


func test_exfil_banks_after_bonus_once() -> void:
	session.progression.add_xp(player, 101)
	session.match_end.finish_exfil()
	session.match_end.finish_exfil()
	session.match_end.bank_run_xp()
	assert_eq(session.progression.get_xp(player), 151)
	assert_eq(int(SaveFile.read(_path)["total_xp"]), START_XP + 151)
	await wait_seconds(0.05)


func test_inventory_and_unknown_item_keys_survive_match_save_and_load() -> void:
	session.free()
	var profile: CharacterProfile = CharacterProfile.load_or_create(ID)
	var item: Dictionary = {
		"v": 1,
		"uid": "stashed",
		"base": "rifle_ar",
		"rar": "rare",
		"ilvl": 12,
		"aff": [["removed_affix", 2, 0.25]],
		"imp": ["reclaimer", 0.5],
		"trait": null,
		"set": null,
		"craft": {"future_lock": true},
		"future": [1, null, {"kept": true}],
	}
	profile.stash[17] = item
	profile.loadout["primary"] = item.duplicate(true)
	profile.loadout["primary"]["uid"] = "equipped"
	assert_eq(profile.save(), OK)
	var expected: Dictionary = SaveFile.read(_path)
	session = SESSION.instantiate() as GameSession
	add_child_autofree(session)
	player = session.get_players()[0]
	session.progression.add_xp(player, 75)
	session.match_end.bank_run_xp()
	var loaded: CharacterProfile = CharacterProfile.load_or_create(ID)
	assert_eq(loaded.total_xp, START_XP + 75)
	assert_eq(loaded.stash, expected["stash"])
	assert_eq(loaded.loadout, expected["loadout"])
	assert_eq(loaded.stash.size(), 60)
	assert_eq(loaded.stash[17]["future"], expected["stash"][17]["future"])
	assert_eq(loaded.loadout["primary"]["uid"], "equipped")
	assert_eq(loaded.loadout["primary"]["craft"], expected["loadout"]["primary"]["craft"])


func test_old_v1_save_banks_xp_with_empty_inventory() -> void:
	session.free()
	assert_eq(SaveFile.write(_path, {"id": String(ID), "total_xp": START_XP}), OK)
	session = SESSION.instantiate() as GameSession
	add_child_autofree(session)
	player = session.get_players()[0]
	session.progression.add_xp(player, 75)
	session.match_end.bank_run_xp()
	var loaded: CharacterProfile = CharacterProfile.load_or_create(ID)
	assert_eq(loaded.total_xp, START_XP + 75)
	assert_eq(loaded.stash.size(), 60)
	for item: Dictionary in loaded.stash:
		assert_eq(item, {})
	assert_eq(loaded.loadout, EMPTY_LOADOUT)
	assert_eq(int(SaveFile.read(_path)["save_version"]), SaveFile.CURRENT_VERSION)


func test_restart_mid_run_banks_once() -> void:
	# A root scene lets reload_current_scene exercise the real restart path while GUT stays alive.
	var runner_scene: Node = get_tree().current_scene
	remove_child(session)
	get_tree().root.add_child(session)
	get_tree().current_scene = session
	session.progression.add_xp(player, 75)
	session.restart()
	session.match_end.bank_run_xp()
	assert_eq(int(SaveFile.read(_path)["total_xp"]), START_XP + 75)
	await wait_process_frames(2)
	session = get_tree().current_scene as GameSession
	get_tree().current_scene = runner_scene
	assert_not_null(session)
	if session == null:
		return
	player = session.get_players()[0]
	assert_eq(session.progression.get_total_xp(player), START_XP + 75)
	assert_eq(session.progression.get_level(player), 2)
	session.match_end.bank_run_xp()
	session.match_end.bank_run_xp()
	assert_eq(int(SaveFile.read(_path)["total_xp"]), START_XP + 75)
	session.free()


func test_empty_profile_id_does_not_load_or_save() -> void:
	session.free()
	session = SESSION.instantiate() as GameSession
	session.profile_id = &""
	add_child_autofree(session)
	player = session.get_players()[0]
	assert_eq(session.progression.get_total_xp(player), 0)
	session.progression.add_xp(player, 100)
	session.match_end.bank_run_xp()
	assert_eq(int(SaveFile.read(_path)["total_xp"]), START_XP)


func test_window_close_banks_once() -> void:
	session.progression.add_xp(player, 75)
	session.notification(Node.NOTIFICATION_WM_CLOSE_REQUEST)
	session.notification(Node.NOTIFICATION_WM_CLOSE_REQUEST)
	session.match_end.bank_run_xp()
	assert_eq(int(SaveFile.read(_path)["total_xp"]), START_XP + 75)


func test_pause_main_menu_banks_before_leaving() -> void:
	var runner_scene: Node = get_tree().current_scene
	remove_child(session)
	get_tree().root.add_child(session)
	get_tree().current_scene = session
	session.progression.add_xp(player, 75)
	session.loot.pack.add({"uid": "menu-exit", "base": "vest_light", "rar": "common"})
	var pause: InputEventAction = InputEventAction.new()
	pause.action = &"pause"
	pause.pressed = true
	session._unhandled_input(pause)
	(UI._stack.back()["layer"].get_child(0) as PauseScreen).main_menu_button.pressed.emit()
	assert_eq(int(SaveFile.read(_path)["total_xp"]), START_XP + 75)
	await wait_process_frames(2)
	assert_eq(CharacterProfile.load_or_create(ID).stash[0].get("uid"), "menu-exit")
	var menu: Node = get_tree().current_scene
	get_tree().current_scene = runner_scene
	assert_false(get_tree().paused)
	assert_eq(menu.scene_file_path, "res://systems/ui/main_menu.tscn")
	menu.free()


func test_pack_is_saved_on_death_and_banking_is_idempotent() -> void:
	var item: Dictionary = {"uid": "kept-on-death", "base": "vest_light", "rar": "rare", "ilvl": 17}
	assert_true(session.loot.pack.add(item))
	player.take_damage(DamageInfo.create(10000.0, null))
	await wait_until(func() -> bool: return UI.top() == &"results", 2.0, "death results shown")
	session.match_end.bank_run_xp()
	var saved: CharacterProfile = CharacterProfile.load_or_create(ID)
	assert_eq(saved.stash[0].uid, "kept-on-death")
	assert_eq(saved.stash[1], {})
	assert_eq(session.loot.results(), {"loot": [item], "loot_lost": 0})
	assert_true(session.loot.pack.items.is_empty())
	assert_eq(_results().loot_items.get_child_count(), 1)


func test_stash_full_keeps_what_fits_saves_and_reports_overflow() -> void:
	for slot: int in CharacterProfile.STASH_SIZE - 1:
		session.profile.stash[slot] = {"uid": "old-%d" % slot}
	for index: int in 3:
		session.loot.pack.add({"uid": "new-%d" % index, "base": "vest_light", "rar": "common"})
	var lost_before: int = Log.event_counts.get("loot.stash_item_lost", 0)
	session.match_end.finish_exfil()
	await wait_until(func() -> bool: return UI.top() == &"results", 2.0, "results shown")
	var saved: CharacterProfile = CharacterProfile.load_or_create(ID)
	assert_eq(saved.stash[59].uid, "new-0")
	assert_eq(saved.stash[58].uid, "old-58")
	assert_eq(session.loot.lost, 2)
	assert_eq(Log.event_counts.get("loot.stash_item_lost", 0) - lost_before, 2)
	assert_eq(_results().loot_status.text, "Stash full · 1 kept, 2 items lost")
	session.match_end.bank_run_xp()
	assert_eq(session.loot.lost, 2)


func test_game_over_records_best_round_even_after_xp_was_banked_first() -> void:
	session.director.round_number = 4
	watch_signals(Events)
	session.match_end.bank_run_xp()
	player.take_damage(DamageInfo.create(10000.0, null))
	await wait_for_signal(Events.game_over, 3.0)
	var stats: Dictionary = get_signal_parameters(Events, "game_over")[0]
	assert_true(stats.get("new_best", false), "first run on the map is a best")
	assert_eq(int(SaveFile.read(_path)["best_runs"]["halcyon_labs"]["round"]), 4)


func _results() -> ResultsScreen:
	return UI._stack.back()["layer"].get_child(0) as ResultsScreen


func test_player_can_choose_the_reward_for_the_last_stash_space() -> void:
	for slot: int in CharacterProfile.STASH_SIZE - 1:
		session.profile.stash[slot] = {"uid": str(slot), "base": "vest_light", "rar": "common"}
	var common: Dictionary = {"uid": "common", "base": "vest_light", "rar": "common"}
	var rare: Dictionary = {"uid": "prized", "base": "vest_light", "rar": "rare"}
	session.loot.send_drop(1, common, player.global_position)
	(session.loot.get_child(0) as LootDrop).interact(player)
	await wait_physics_frames(2)
	session.loot.send_drop(1, rare, player.global_position)
	var drop: LootDrop = session.loot.get_child(0) as LootDrop
	drop.interact(player)
	var dialog: StashExchange = drop.get_node("StashExchange") as StashExchange
	assert_true(dialog.get_ok_button().disabled, "explicit choice is required")
	dialog.canceled.emit()
	await wait_physics_frames(2)
	assert_eq(session.loot.pack.items, [common], "cancelling keeps both choices available")
	drop.interact(player)
	dialog = drop.get_node("StashExchange") as StashExchange
	dialog._choices.select(1)
	dialog._choices.item_selected.emit(1)
	assert_false(dialog.get_ok_button().disabled)
	dialog.confirmed.emit()
	assert_eq(session.loot.pack.items, [rare])
	session.match_end.bank_run_xp()
	assert_eq(CharacterProfile.load_or_create(ID).stash[59].uid, "prized")
	assert_eq(session.loot.lost, 0)


func test_full_stash_exchange_discards_only_the_selected_stored_item() -> void:
	for slot: int in CharacterProfile.STASH_SIZE:
		session.profile.stash[slot] = {"uid": str(slot), "base": "vest_light", "rar": "common"}
	session.profile.stash[1].aff = [["grenade_damage", 1, 1.0]]
	var prize: Dictionary = {"uid": "new", "base": "vest_light", "rar": "rare"}
	session.loot.send_drop(1, prize, player.global_position)
	var drop: LootDrop = session.loot.get_child(0) as LootDrop
	drop.interact(player)
	var dialog: StashExchange = drop.get_node("StashExchange") as StashExchange
	dialog._choices.select(2)
	dialog._choices.item_selected.emit(2)
	assert_string_contains(dialog._detail.text, "Permanently discard")
	assert_string_contains(dialog._detail.text, "20%")
	dialog.confirmed.emit()
	session.match_end.bank_run_xp()
	var saved: CharacterProfile = CharacterProfile.load_or_create(ID)
	assert_eq(saved.stash[0].uid, "0")
	assert_eq(saved.stash[1].uid, "new")
	assert_eq(saved.free_stash_slots(), 0)


func test_run_exit_while_an_exchange_is_open_keeps_the_stored_item() -> void:
	for slot: int in CharacterProfile.STASH_SIZE:
		session.profile.stash[slot] = {"uid": str(slot), "base": "vest_light", "rar": "common"}
	session.loot.send_drop(1, {"uid": "new", "base": "vest_light", "rar": "rare"}, player.global_position)
	var drop: LootDrop = session.loot.get_child(0) as LootDrop
	drop.interact(player)
	var dialog: StashExchange = drop.get_node("StashExchange") as StashExchange
	dialog._choices.select(1)
	session.match_end.bank_run_xp()
	dialog.confirmed.emit()
	assert_eq(session.profile.stash[0].uid, "0")
	assert_eq(CharacterProfile.load_or_create(ID).stash[0].uid, "0")
	assert_true(session.loot.pack.items.is_empty())


func test_full_pack_can_exchange_its_last_reserved_slot_without_discarding_stash() -> void:
	for slot: int in CharacterProfile.STASH_SIZE - Pack.CAPACITY:
		session.profile.stash[slot] = {"uid": str(slot), "base": "vest_light", "rar": "common"}
	for slot: int in Pack.CAPACITY:
		session.loot.pack.add({"uid": "pack%d" % slot, "base": "vest_light", "rar": "common"})
	session.loot.send_drop(1, {"uid": "new", "base": "vest_light", "rar": "rare"}, player.global_position)
	var drop: LootDrop = session.loot.get_child(0) as LootDrop
	assert_string_contains(drop.get_prompt(player), "[F]")
	drop.interact(player)
	var dialog: StashExchange = drop.get_node("StashExchange") as StashExchange
	assert_eq(dialog._choices.item_count, Pack.CAPACITY + 1)
	dialog._choices.select(3)
	dialog.confirmed.emit()
	assert_eq(session.loot.pack.items[2].uid, "new")
	assert_eq(session.profile.free_stash_slots(), Pack.CAPACITY)
