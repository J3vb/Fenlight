## In-match HUD; gameplay facts arrive through Events. Pause and results are router screens.
class_name Hud
extends CanvasLayer

const BLOOD_RED: Color = Color("c8202a")
const OFF_WHITE: Color = Color("f2ede0")
var _toast_tween: Tween
var _prompt_text: String = ""
var _player: Player
var _hurt: float = 0.0
var _damage_effects: float = 1.0
var _health_ratio: float = 1.0
var _center_time: float = 0.0
var _delta_time: float = 0.0
var _delta_sum: int = 0
var _exfil: ExfilHatch
var _squad: SquadCards

@onready var coop_hud: CoopHud = $Root/Coop
@onready var crosshair: Crosshair = $Root/Crosshair
@onready var hit_marker: HitMarker = $Root/HitMarker
@onready var vignette: ColorRect = $Root/DamageVignette
@onready var round_counter: RoundCounter = $Root/RoundInfo
@onready var points_label: Label = $Root/Loadout/PointsLabel
@onready var points_delta: Label = $Root/Loadout/PointsDelta
@onready var weapon_label: Label = $Root/Loadout/WeaponLabel
@onready var exfil_box: PanelContainer = $Root/ExfilBox
@onready var exfil_title: Label = $Root/ExfilBox/Box/Title
@onready var exfil_bar: ProgressBar = $Root/ExfilBox/Box/Hold
@onready var exfil_time: Label = $Root/ExfilBox/Box/Time
@onready var prompt_box: PanelContainer = $Root/Prompt
@onready var world_prompt: WorldPrompt = $Root/WorldPrompt
@onready var prompt_key: Label = $Root/Prompt/Row/Key
@onready var prompt_price: Label = $Root/Prompt/Row/Price
@onready var hint_label: Label = $Root/HintLabel
@onready var center_label: Label = $Root/CenterLabel
@onready var prompt_label: Label = $Root/Prompt/Row/PromptLabel
@onready var xp_bar: ProgressBar = $Root/XpBar
@onready var level_label: Label = $Root/Level
@onready var level_toast: Label = $Root/LevelToast
@onready var hit_sound: AudioStreamPlayer = $HitSound
@onready var round_sound: AudioStreamPlayer = $RoundSound
@onready var _fps_label: Label = $Root/Fps


func _ready() -> void:
	level_toast.modulate.a = 0.0
	center_label.modulate.a = 0.0
	points_delta.modulate.a = 0.0
	hint_label.text = ""
	prompt_key.text = Settings.key_name(&"interact")
	world_prompt.box = prompt_box
	Settings.changed.connect(_on_setting_changed)
	_damage_effects = Settings.get_value(&"comfort", &"damage_effects")
	$Root.add_child(VersionLabel.new())
	_squad = SquadCards.new()
	$Root.add_child(_squad)
	$Root.add_child(AbilityIcon.new())
	Events.player_spawned.connect(_on_player_spawned)
	Events.player_health_changed.connect(_on_health_changed)
	Events.player_damaged.connect(_on_player_damaged)
	Events.points_changed.connect(_on_points_changed)
	Events.ammo_changed.connect(_on_ammo_changed)
	Events.weapon_switched.connect(_on_weapon_switched)
	Events.hit_confirmed.connect(_on_hit_confirmed)
	Events.power_up_collected.connect(_on_power_up_collected)
	Events.player_revived.connect(_on_player_revived)
	Events.round_started.connect(_on_round_started)
	Events.round_ended.connect(_on_round_ended)
	Events.intermission_started.connect(_on_intermission)
	Events.exfil_opened.connect(
		func() -> void:
			_exfil = get_tree().get_first_node_in_group(&"exfil") as ExfilHatch
			_update_exfil()
	)
	Events.exfil_called.connect(func(hatch: ExfilHatch) -> void: _exfil = hatch)
	Events.game_over.connect(_on_game_over)
	Events.player_leveled_up.connect(_on_player_leveled_up)


func _physics_process(delta: float) -> void:
	var frame: InputFrame = InputFrame.new()
	if is_instance_valid(_player) and _player.local_input.interact_held():
		frame.buttons = InputFrame.INTERACT
	coop_hud.apply_frame(frame, delta)


func _process(delta: float) -> void:
	_fps_label.visible = bool(Settings.get_value(&"graphics", &"show_fps"))
	_fps_label.text = "FPS: %d" % Engine.get_frames_per_second()
	_hurt = maxf(_hurt - delta * 1.5, 0.0)
	var low: float = clampf((0.6 - _health_ratio) / 0.6, 0.0, 1.0)
	var shade: ShaderMaterial = vignette.material as ShaderMaterial
	if shade:  # null in the dedicated server export, which strips visual resources
		shade.set_shader_parameter("intensity", clampf(maxf(_hurt, low * 0.85), 0.0, 1.0) * _damage_effects)
	if _center_time > 0.0:
		_center_time -= delta
		center_label.modulate.a = clampf(_center_time, 0.0, 1.0)
	if _delta_time > 0.0:
		_delta_time -= delta
		points_delta.modulate.a = clampf(_delta_time * 2.0, 0.0, 1.0)
		if _delta_time <= 0.0:
			_delta_sum = 0

	_update_exfil()
	_update_prompt(coop_hud.get_prompt(_player if is_instance_valid(_player) else null, UI.top() != &""))
	if is_instance_valid(_player) and _player.weapons.current:
		var w: Weapon = _player.weapons.current
		crosshair.spread_degrees = w.get_current_spread()
		crosshair.fov_degrees = _player.camera.fov
		crosshair.lines_alpha = 0.0 if (w.ads_progress > 0.5 or _player.is_sprinting) else 1.0
		crosshair.visible = _player.is_alive()


func _update_exfil() -> void:
	exfil_box.visible = is_instance_valid(_exfil) and (_exfil.is_open or _exfil.is_holding)
	if not exfil_box.visible:
		return
	exfil_title.text = "Hold the hatch" if _exfil.is_holding else "Exfil open · Containment Wing"
	exfil_bar.visible = _exfil.is_holding
	if not _exfil.is_holding:
		exfil_time.text = "Hold %ds for +50%% run XP\nor stay for the next wave" % int(ExfilHatch.HOLD_TIME)
		return
	exfil_bar.value = 1.0 - _exfil.hold_left / ExfilHatch.HOLD_TIME
	var seconds: int = maxi(ceili(_exfil.hold_left), 0)
	exfil_time.text = "Hold %d:%02d" % [seconds / 60, seconds % 60]
	if _exfil.is_holding and not _exfil.has_player_in_zone():
		exfil_time.text += " · Return to hatch"


func _update_prompt(text: String) -> void:
	if text == _prompt_text:
		return
	_prompt_text = text
	prompt_box.visible = not text.is_empty()
	prompt_key.visible = text.contains("[F]")
	prompt_price.text = ""
	var parts: PackedStringArray = text.split("[F]", true, 1)
	if parts.size() == 2 and parts[1].strip_edges().is_valid_int():
		prompt_price.text = parts[1].strip_edges()
		prompt_label.text = parts[0].strip_edges()
	else:
		prompt_label.text = text.replace("[F]", "").strip_edges()


func _on_setting_changed(section: StringName, key: StringName, value: Variant) -> void:
	if section == &"comfort" and key == &"damage_effects":
		_damage_effects = value
	if section != &"bindings":
		return
	prompt_key.text = Settings.key_name(&"interact")
	if hint_label.text.begins_with("RELOAD"):
		hint_label.text = "RELOAD [%s]" % Settings.key_name(&"reload")


func _format_points(value: int) -> String:
	var digits: String = str(absi(value))
	var index: int = digits.length() - 3
	while index > 0:
		digits = digits.insert(index, ",")
		index -= 3
	return ("-" if value < 0 else "") + digits


func _flash_center(text: String, seconds: float) -> void:
	center_label.text = text
	_center_time = seconds


func _on_player_spawned(player: Player) -> void:
	if _player == null and player.is_multiplayer_authority():
		_player = player
		_squad.local_player = player
		if player.session:
			player.session.progression.xp_gained.connect(_on_xp_gained)
			_on_xp_gained(player, 0, 0)


func _on_health_changed(player: Player, current: float, maximum: float) -> void:
	if player == _player:
		_health_ratio = clampf(current / maxf(maximum, 1.0), 0.0, 1.0)


func _on_player_damaged(player: Player, _info: DamageInfo) -> void:
	if player == _player:
		_hurt = 0.8


func _on_points_changed(player: Player, total: int, delta: int) -> void:
	if player != _player:
		return
	points_label.text = _format_points(total)
	if delta > 0:
		_delta_sum += delta
		points_delta.text = "+%d" % _delta_sum
		_delta_time = 1.2


func _on_ammo_changed(player: Player, in_mag: int, reserve: int) -> void:
	if player != _player:
		return
	var low: bool = _player.weapons.current and in_mag <= _player.weapons.current.data.magazine_size / 4
	if in_mag == 0 and reserve == 0:
		hint_label.text = "NO AMMO"
	elif low and reserve > 0:
		hint_label.text = "RELOAD [%s]" % Settings.key_name(&"reload")
	else:
		hint_label.text = ""


func _on_weapon_switched(player: Player, weapon: Weapon) -> void:
	if player == _player:
		weapon_label.text = weapon.data.display_name


func _on_hit_confirmed(player: Player, is_kill: bool, is_headshot: bool) -> void:
	if player != _player:
		return
	hit_marker.show_hit(is_kill, is_headshot)
	hit_sound.pitch_scale = 0.8 if is_kill else 1.0
	hit_sound.play()


func _on_power_up_collected(_collector: Player, power_up: PowerUpData) -> void:
	_flash_center(power_up.display_name.to_upper(), 2.0)


func _on_player_revived(player: Player) -> void:
	if player == _player:
		_flash_center("REVIVED" if Net.is_coop() else "SECOND WIND", 2.0)


func _on_round_started(round_number: int, _count: int) -> void:
	_flash_center("ROUND %d" % round_number, 3.0)
	round_sound.play()


func _on_round_ended(round_number: int) -> void:
	($RoundEndSound as AudioStreamPlayer).play()
	_flash_center("ROUND %d SURVIVED" % round_number, 3.0)


func _on_intermission(next_round: int, duration: float) -> void:
	if next_round == 1:
		_flash_center("SURVIVE", duration)


func _on_game_over(_stats: Dictionary) -> void:
	_exfil = null
	exfil_box.hide()


func _on_xp_gained(player: Player, _amount: int, _total: int) -> void:
	if player != _player:
		return
	var progression: ProgressionService = player.session.progression
	var level: int = progression.get_level(player)
	var needed: int = progression.rules.xp_to_next(level)
	level_label.text = "LV %d" % level
	xp_bar.max_value = maxf(needed, 1.0)
	xp_bar.value = progression.get_total_xp(player) - progression.rules.total_xp_for_level(level) if needed > 0 else 1


func _on_player_leveled_up(player: Player, level: int) -> void:
	if player != _player:
		return
	if _toast_tween:
		_toast_tween.kill()
	level_toast.text = "LEVEL %d" % level
	level_toast.modulate.a = 0.0
	_toast_tween = create_tween()
	_toast_tween.tween_property(level_toast, "modulate:a", 1.0, 0.12)
	_toast_tween.tween_interval(1.68)
	_toast_tween.tween_property(level_toast, "modulate:a", 0.0, 0.2)
