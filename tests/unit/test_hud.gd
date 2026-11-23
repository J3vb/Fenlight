## HUD presentation follows Events without changing gameplay state.
extends GutTest

const HUD: PackedScene = preload("res://systems/ui/hud.tscn")
const PLAYER: PackedScene = preload("res://systems/player/player.tscn")

var hud: Hud
var player: Player
var progression: ProgressionService
var session: GameSession


func before_each() -> void:
	hud = HUD.instantiate() as Hud
	add_child_autofree(hud)
	hud.set_process(false)
	player = PLAYER.instantiate() as Player
	add_child_autofree(player)
	player.set_physics_process(false)
	player.weapons.give(Content.weapon(&"rifle_ar"))
	session = GameSession.new()
	autofree(session)
	progression = ProgressionService.new()
	add_child_autofree(progression)
	session.progression = progression
	player.session = session
	Events.player_spawned.emit(player)


func test_points_separators_and_delta_summing_then_expiry() -> void:
	Events.points_changed.emit(player, 14520, 100)
	Events.points_changed.emit(player, 14570, 50)
	assert_eq(hud.points_label.text, "14,570")
	assert_eq(hud.points_delta.text, "+150")
	hud._process(1.3)
	assert_eq(hud.points_delta.modulate.a, 0.0)
	Events.points_changed.emit(player, 14670, 100)
	assert_eq(hud.points_delta.text, "+100")
	Events.points_changed.emit(player, 999, -13671)
	assert_eq(hud.points_label.text, "999")


func test_ammo_hints_and_weapon_name() -> void:
	var magazine: int = player.weapons.current.data.magazine_size
	var low_count: int = floori(magazine * 0.25)
	Events.ammo_changed.emit(player, low_count, 210)
	assert_eq(hud.hint_label.text, "RELOAD [R]")
	Events.ammo_changed.emit(player, low_count + 1, 210)
	assert_eq(hud.hint_label.text, "")
	Events.ammo_changed.emit(player, 0, 0)
	assert_eq(hud.hint_label.text, "NO AMMO")
	Events.weapon_switched.emit(player, player.weapons.current)
	assert_eq(hud.weapon_label.text, player.weapons.current.data.display_name)


func test_exfil_shows_when_open_counts_hold_and_hides_when_closed() -> void:
	var hatch: ExfilHatch = preload("res://systems/interactables/exfil_hatch.tscn").instantiate() as ExfilHatch
	add_child_autofree(hatch)
	assert_false(hud.exfil_box.visible)
	hatch.is_open = true
	Events.exfil_opened.emit()
	assert_true(hud.exfil_box.visible)
	assert_eq(hud.exfil_title.text, "Exfil open · Containment Wing")
	assert_string_contains(hud.exfil_time.text, "60s for +50% run XP")
	assert_string_contains(hud.exfil_time.text, "stay for the next wave")
	assert_false(hud.exfil_bar.visible)
	hatch.is_holding = true
	hatch.hold_left = 39.0
	Events.exfil_called.emit(hatch)
	hud._process(0.0)
	assert_eq(hud.exfil_time.text, "Hold 0:39")
	assert_almost_eq(hud.exfil_bar.value, 0.35, 0.001)
	player.global_position = Vector3(10, 0, 0)
	hud._process(0.0)
	assert_eq(hud.exfil_time.text, "Hold 0:39 · Return to hatch")
	assert_almost_eq(hud.exfil_bar.value, 0.35, 0.001)
	player.global_position = Vector3.ZERO
	hud._process(0.0)
	assert_eq(hud.exfil_time.text, "Hold 0:39")
	hatch.is_open = false
	hatch.is_holding = false
	hud._process(0.0)
	assert_false(hud.exfil_box.visible)


func test_prompt_splits_existing_interactable_price_and_preserves_unclear_text() -> void:
	var door: Door = Door.new()
	autofree(door)
	door.cost = 1500
	door.label = "Labs"
	player.focus = door
	hud._process(0.0)
	assert_true(hud.prompt_box.visible)
	assert_true(hud.prompt_key.visible)
	assert_eq(hud.prompt_label.text, "Open Labs")
	assert_eq(hud.prompt_price.text, "1500")
	await get_tree().process_frame
	assert_gt(hud.prompt_box.position.y, hud.prompt_box.get_viewport_rect().size.y * 0.5)
	hud._update_prompt("Needs power")
	assert_eq(hud.prompt_label.text, "Needs power")
	assert_eq(hud.prompt_price.text, "")
	assert_false(hud.prompt_key.visible)
	hud._update_prompt("Buy Rifle 42 [F]  unknown")
	assert_eq(hud.prompt_label.text, "Buy Rifle 42   unknown")
	assert_eq(hud.prompt_price.text, "")
	player.focus = null
	hud._process(0.0)
	assert_false(hud.prompt_box.visible)


func test_other_player_events_ignored() -> void:
	var other: Player = Player.new()
	autofree(other)
	Events.points_changed.emit(other, 99999, 100)
	assert_eq(hud.points_label.text, "0")


func test_xp_bar_follows_grants_and_saved_total() -> void:
	assert_eq(hud.level_label.text, "LV 1")
	progression.add_xp(player, 250)
	assert_almost_eq(hud.xp_bar.value, 250.0, 0.001)
	assert_almost_eq(hud.xp_bar.max_value, 500.0, 0.001)
	progression.add_xp(player, 350)
	assert_eq(hud.level_label.text, "LV 2")
	assert_almost_eq(hud.xp_bar.value, 100.0, 0.001)
	progression.set_start_total(player, progression.rules.total_xp_for_level(7))
	progression.add_xp(player, 10)
	assert_eq(hud.level_label.text, "LV 7")
	assert_almost_eq(hud.xp_bar.value, 610.0, 0.001)
	assert_almost_eq(hud.xp_bar.max_value, float(progression.rules.xp_to_next(7)), 0.001)


func test_level_toast_fades_for_two_seconds_and_ignores_other_players() -> void:
	Events.player_leveled_up.emit(player, 8)
	assert_eq(hud.level_toast.text, "LEVEL 8")
	hud._toast_tween.pause()
	hud._toast_tween.custom_step(0.12)
	assert_almost_eq(hud.level_toast.modulate.a, 1.0, 0.001)
	hud._toast_tween.custom_step(1.68)
	assert_almost_eq(hud.level_toast.modulate.a, 1.0, 0.001)
	hud._toast_tween.custom_step(0.21)
	assert_almost_eq(hud.level_toast.modulate.a, 0.0, 0.001)
	var other: Player = Player.new()
	autofree(other)
	Events.player_leveled_up.emit(other, 9)
	progression.add_xp(other, 250)
	assert_eq(hud.level_toast.text, "LEVEL 8")
	assert_eq(hud.level_label.text, "LV 1")
	assert_almost_eq(hud.xp_bar.value, 0.0, 0.001)


func test_xp_bar_is_full_at_level_cap() -> void:
	progression.add_xp(player, progression.rules.total_xp_for_level(50) + 100)
	assert_eq(hud.level_label.text, "LV 50")
	assert_almost_eq(hud.xp_bar.value / hud.xp_bar.max_value, 1.0, 0.001)


func test_hud_initializes_from_saved_total_at_spawn() -> void:
	progression.set_start_total(player, progression.rules.total_xp_for_level(7) + 200)
	var fresh: Hud = HUD.instantiate() as Hud
	add_child_autofree(fresh)
	fresh.set_process(false)
	Events.player_spawned.emit(player)
	assert_eq(fresh.level_label.text, "LV 7")
	assert_almost_eq(fresh.xp_bar.value, 200.0, 0.001)


## The dedicated server export strips visual resources, so the vignette has no
## material there; the frame must still update everything after it.
func test_process_without_vignette_material_keeps_updating() -> void:
	hud.vignette.material = null
	hud._center_time = 0.5
	hud.center_label.modulate.a = 1.0
	hud._process(0.1)
	assert_almost_eq(hud.center_label.modulate.a, 0.4, 0.001)


func test_interact_badge_and_reload_hint_follow_rebinding() -> void:
	var old_path: String = Settings.config_path
	var old_values: Dictionary = Settings._values.duplicate(true)
	Settings.config_path = "user://test_hud_bindings.cfg"
	var door: Door = Door.new()
	autofree(door)
	door.cost = 1500
	player.focus = door
	hud._process(0.0)
	assert_eq(hud.prompt_key.text, "F")
	var low_count: int = floori(player.weapons.current.data.magazine_size * 0.25)
	Events.ammo_changed.emit(player, low_count, 210)
	var interact: InputEventKey = InputEventKey.new()
	interact.physical_keycode = KEY_E
	var reload: InputEventKey = InputEventKey.new()
	reload.physical_keycode = KEY_T
	Settings.swap_binding(&"interact", 0, interact)
	Settings.set_binding(&"reload", 0, reload)
	assert_eq(hud.prompt_key.text, "E", "a visible prompt shows the new key")
	assert_eq(hud.hint_label.text, "RELOAD [T]")
	Settings.reset_to_defaults()
	assert_eq(hud.prompt_key.text, "F", "Reset to defaults also refreshes prompts")
	assert_eq(hud.hint_label.text, "RELOAD [R]")
	Settings._values = old_values
	Settings._apply_all()
	DirAccess.remove_absolute(ProjectSettings.globalize_path(Settings.config_path))
	Settings.config_path = old_path
