## Hitscan WeaponInstance node; public inputs drive firing, spread, recoil, reload and viewmodel poses.
class_name Weapon
extends Node3D

signal ammo_changed(in_mag: int, reserve: int)
signal fired
## The trigger was pulled on an empty magazine; once per press, not every tick.
signal dry_fired
signal reload_started(duration: float)
signal hit_landed(is_kill: bool, info: DamageInfo, zone: HitZone)
signal traced(point: Vector3, normal: Vector3, kind: Impact.Kind)

enum State { IDLE, RELOADING }

const BUFFER_TIME: float = 0.12

var instance: WeaponInstance
var data: WeaponData:
	get:
		return instance.data
var shooter: Player
var item: ItemInstance
var camera: Camera3D
var trigger_held: bool = false
var aiming: bool = false
var sprinting: bool = false
var move_factor: float = 0.0

var state: State = State.IDLE
var ads_progress: float = 0.0
var active: bool = false

var _shot_timer: float = 0.0
var _burst_left: int = 0
var _buffered: float = 0.0
var _trigger_was_held: bool = false
var _shots_in_string: int = 0
var _since_last_shot: float = 99.0
var _bloom: float = 0.0
var _sprint_block: float = 0.0
var _sprint_progress: float = 0.0
var _reload_timer: float = 0.0
var _reload_duration: float = 0.0
var _first_round_duration: float = 0.0
var _empty_reload: bool = false
var _rng: RandomNumberGenerator
var _spin_up: SpinUp = SpinUp.new()

@onready var pose: WeaponPose = WeaponPose.attach_to(self)
@onready var _double_barrel: DoubleBarrel = DoubleBarrel.attach_to(self)
@onready var _viewmodel_root: Node3D = $Viewmodel
@onready var _fire_audio: AudioStreamPlayer = $FireAudio


func setup(p_instance: WeaponInstance, p_shooter: Player, p_camera: Camera3D) -> void:
	instance = p_instance
	shooter = p_shooter
	camera = p_camera
	_rng = shooter.get_rng() if shooter else RandomNumberGenerator.new()


func _ready() -> void:
	if data.viewmodel_scene:
		var vm: Node = data.viewmodel_scene.instantiate()
		_viewmodel_root.add_child(vm)
		pose.find_moving_parts(vm)
	_spin_up.configure(data.spin_up_time, _viewmodel_root.find_child("SpinUpAudio", true, false) as AudioStreamPlayer)
	pose.set_flash(false)
	_fire_audio.stream = data.fire_sound
	position = data.hip_position
	fired.connect(_on_fired)
	traced.connect(_on_traced)


func set_active(value: bool) -> void:
	active = value
	visible = value
	if not value:
		_spin_up.reset()
	if value:
		_emit_ammo()


func is_reloading() -> bool:
	return state == State.RELOADING


func get_current_spread() -> float:
	var base: float = lerpf(data.hip_spread, data.ads_spread, ads_progress)
	var movement: float = data.move_spread * move_factor * (1.0 - ads_progress * 0.8)
	return minf(base + movement + _bloom, data.max_spread)


func start_reload() -> bool:
	if state == State.RELOADING or not instance.needs_reload():
		return false
	state = State.RELOADING
	_spin_up.reset()
	_burst_left = 0
	_empty_reload = instance.ammo_in_mag == 0
	_reload_duration = (data.empty_reload_time if _empty_reload else data.reload_time) * _stat(&"reload_time")
	_reload_timer = _reload_duration
	if data.reload_per_round:
		_reload_duration = RoundReload.duration(self)
		_first_round_duration = RoundReload.cycle_length(self)
		_reload_timer = _first_round_duration
	if pose.motion == null:
		pose.play_mech(data.reload_sound)
	if (
		OwnerTraits.wants_cold_snap(item, _owns(), _empty_reload)
		and shooter.session
		and shooter.session.legendary_traits
	):
		shooter.session.legendary_traits.request_cold_snap(shooter, str(item.data.get("uid", "")))
	reload_started.emit(_reload_timer)
	return true


func _stat(stat: StringName) -> float:
	if shooter:
		return shooter.get_stat(stat, 1.0, item.stats if item else null)
	return item.weapon_stat(stat) if item else 1.0


func _owns() -> bool:
	return item != null and shooter != null and shooter.is_inside_tree() and shooter.is_multiplayer_authority()


func can_fire() -> bool:
	return active and (state == State.IDLE or RoundReload.can_fire(self)) and _sprint_block <= 0.0 and not sprinting


## Simulation step, run from the owner's physics tick.
func tick(delta: float) -> void:
	_tick_timers(delta)
	if state == State.RELOADING and data.reload_per_round:
		RoundReload.tick(self, delta)
	elif state == State.RELOADING:
		_reload_timer -= delta
		if _reload_timer <= 0.0:
			_finish_reload()
	_spin_up.tick(delta, trigger_held and can_fire() and instance.ammo_in_mag > 0)
	_handle_trigger()
	_spin_up.tick(0.0, trigger_held and can_fire() and instance.ammo_in_mag > 0)
	_trigger_was_held = trigger_held


func _process(delta: float) -> void:
	if not active:
		return
	pose.update(delta)


func _tick_timers(delta: float) -> void:
	_shot_timer -= delta
	_since_last_shot += delta
	_buffered = _double_barrel.buffer(maxf(_buffered - delta, 0.0)) if _double_barrel else maxf(_buffered - delta, 0.0)
	_bloom = move_toward(_bloom, 0.0, data.spread_recovery * delta)
	_sprint_block = (
		data.sprint_to_fire_time * _stat(&"sprint_out_time") if sprinting else maxf(_sprint_block - delta, 0.0)
	)
	var ads_target: float = 1.0 if aiming and state != State.RELOADING else 0.0
	ads_progress = move_toward(ads_progress, ads_target, delta / maxf(data.ads_time * _stat(&"ads_time"), 0.01))
	_sprint_progress = move_toward(_sprint_progress, 1.0 if sprinting else 0.0, delta * 6.0)
	if _since_last_shot > (data.recoil.reset_time if data.recoil else 0.3):
		_shots_in_string = 0


func _handle_trigger() -> void:
	var pressed_now: bool = trigger_held and not _trigger_was_held
	if pressed_now:
		_buffered = BUFFER_TIME
	while _shot_timer <= 0.0:
		var wants: bool = false
		match data.fire_mode:
			WeaponData.FireMode.AUTO:
				wants = trigger_held
			WeaponData.FireMode.SEMI:
				wants = _buffered > 0.0
			WeaponData.FireMode.BURST:
				if _burst_left == 0 and _buffered > 0.0:
					_burst_left = data.burst_count
				wants = _burst_left > 0
		if not wants or not can_fire():
			break
		var fresh_press: bool = _buffered > 0.0
		_buffered = 0.0
		if instance.ammo_in_mag <= 0:
			_dry_fire(fresh_press)
			break
		fire()
		_burst_left = maxi(_burst_left - 1, 0)
		var extra: float = 0.12 if data.fire_mode == WeaponData.FireMode.BURST and _burst_left == 0 else 0.0
		_shot_timer += _spin_up.scale_interval(data.get_fire_interval(), _shot_timer) * _stat(&"fire_interval") + extra
	_shot_timer = maxf(_shot_timer, 0.0)


## Holding the trigger on an empty gun clicks once, then stays quiet until the next press.
func _dry_fire(fresh_press: bool) -> void:
	_burst_left = 0
	if fresh_press:
		pose.play_mech(data.dry_fire_sound)
		dry_fired.emit()
	start_reload()


## Fires one shot (all pellets) right now. Public for tests and AI.
func fire() -> void:
	RoundReload.cancel(self)
	var rounds: int = DoubleBarrel.consume_rounds(self, _double_barrel)
	var spread: float = get_current_spread()
	var origin: Vector3 = camera.global_position
	var basis: Basis = PlayerCamera.aim_of(camera)
	for i: int in OwnerTraits.take_pellets(item, instance, _owns()) * rounds:
		_trace(origin, _spread_direction(basis, spread))
	_bloom = minf(_bloom + data.spread_per_shot, data.max_spread)
	_apply_recoil()
	_shots_in_string += 1
	_since_last_shot = 0.0
	fired.emit()
	_emit_ammo()
	if instance.ammo_in_mag == 0 and instance.ammo_reserve > 0:
		start_reload()


func _apply_recoil() -> void:
	if data.recoil == null or shooter == null:
		return
	var kick: Vector2 = data.recoil.get_kick(_shots_in_string, _rng)
	kick *= lerpf(1.0, data.recoil.ads_multiplier, ads_progress)
	shooter.camera_rig.add_recoil(kick, data.recoil.recovery_speed, data.recoil.permanent_ratio)


func _spread_direction(basis: Basis, spread_degrees: float) -> Vector3:
	var forward: Vector3 = -basis.z
	if spread_degrees <= 0.0:
		return forward
	var angle: float = deg_to_rad(spread_degrees) * sqrt(_rng.randf())
	var around: float = _rng.randf() * TAU
	var offset: Vector3 = (basis.x * cos(around) + basis.y * sin(around)) * tan(angle)
	return (forward + offset).normalized()


func _trace(origin: Vector3, direction: Vector3) -> void:
	if data.effect == WeaponData.Effect.WELL:
		GravityWell.launch(self)
		return
	var hits: Array[Dictionary] = Pierce.trace(self, origin, direction)
	if shooter and shooter.session and shooter.session.remote_shots:
		var end: Vector3 = hits[-1].position if not hits.is_empty() else origin + direction * data.max_range
		shooter.session.remote_shots.record_trace(self, end)
	for result: Dictionary in hits:
		_hit(result, origin, direction)


func _hit(result: Dictionary, origin: Vector3, direction: Vector3) -> void:
	var point: Vector3 = result.position
	var normal: Vector3 = result.normal
	var hit_zone: HitZone = result.collider as HitZone
	traced.emit(point, normal, Impact.kind_for(hit_zone))
	if hit_zone == null:
		return
	var info: DamageInfo = DamageInfo.create(data.get_damage_at(origin.distance_to(point)), shooter)
	info.amount *= float(result.damage_scale)
	info.weapon_id = data.id
	info.item_uid = str(item.data.get("uid", "")) if item else ""
	info.position = point
	info.normal = normal
	info.impulse = _double_barrel.impulse(direction) if _double_barrel else direction * 2.0
	info.amount *= data.get_zone_multiplier(hit_zone.zone)
	if hit_zone.zone == DamageInfo.Zone.HEAD:
		info.amount *= _stat(&"head_damage")
	info.amount *= OwnerTraits.last_round_scale(item, instance, _owns())
	if not Net.is_authority():
		if shooter and shooter.session:
			shooter.session.hit_claims.submit_hit(self, hit_zone, info)
		return
	HitClaims.apply_host_hit(shooter, hit_zone, info)
	hit_landed.emit(hit_zone.health.is_dead, info, hit_zone)


func _on_fired() -> void:
	pose.on_fired()
	if _fire_audio.stream:
		_fire_audio.pitch_scale = randf_range(0.95, 1.05)  # cosmetic
		_fire_audio.play()


func _on_traced(point: Vector3, normal: Vector3, kind: Impact.Kind) -> void:
	Impact.spawn(get_tree().current_scene, point, normal, kind)


func _finish_reload() -> void:
	state = State.IDLE
	instance.charged = instance.refill_magazine() > 0 or instance.charged
	_emit_ammo()


func _emit_ammo() -> void:
	if active:
		ammo_changed.emit(instance.ammo_in_mag, instance.ammo_reserve)
