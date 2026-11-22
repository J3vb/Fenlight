## Basic zombie brain: rises, queues at and tears through its window barrier
## (if it spawned behind one), vaults in, chases the nearest living player over
## the navmesh, swings when close, dies. State machine is a plain enum + match. The body
## (ZombieRig) and voice (ZombieVoice) are child nodes with their own scripts; the
## way in through a window lives in ZombieEntry.
class_name Zombie
extends CharacterBody3D

enum State { SPAWNING, ENTERING, CHASING, ATTACKING, DEAD }

const SPAWN_TIME: float = 0.9
const SEPARATION_RADIUS: float = 0.9
const SEPARATION_FORCE: float = 2.5
const STRIKE_TIME: float = 0.35
## A swing still lands this far past attack_range (also the reach through a window).
const HIT_SLACK: float = 0.3

var data: EnemyData
var net_id: int = 0
var state: State = State.SPAWNING
var frozen: bool = false:
	set(value):
		if frozen == value:
			return
		frozen = value
		if is_node_ready():
			_show_ice()
## Stasis power-up: stands still, no attacks, no plank tearing. Synced; hits do not shatter it.
var stasis: bool = false:
	set(value):
		if stasis == value:
			return
		stasis = value
		if is_node_ready():
			_show_ice()
## Shock Pulse: seconds left standing still, no attacks (server only; positions sync).
var stun_left: float = 0.0
## Seconds since the current state began.
var state_time: float = 0.0
var head_popped: bool = false
var target: Player
## The window this zombie climbs through; set by the Spawner, cleared once inside.
var barrier: Barrier
## The Spawner's live zombies (shared array, not a copy); separation pushes off these.
var neighbours: Array[Zombie] = []
## Server only, not synced: a Blackout pack follower's leader, and the side (-1/+1) it splits to.
var pack_leader: Zombie
var pack_side: int = 0
## Window queue, plank tearing and vault (ZombieEntry).
var entry: ZombieEntry = ZombieEntry.new()
## Decoy Siren: walks to a point instead of chasing for a few seconds (server only).
var lure: ZombieLure = ZombieLure.new()

var _max_health: float = 100.0
var _speed: float = 1.8
var _damage: float = 35.0
var _attack_cooldown: float = 0.0
var _attack_landed: bool = false
var _repath_timer: float = 0.0
var _retarget_timer: float = 0.0
var _stuck_watch: ZombieStuckWatch = ZombieStuckWatch.new()
var _gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
var _rng: RandomNumberGenerator

@onready var health: HealthComponent = $HealthComponent
@onready var agent: NavigationAgent3D = $NavigationAgent3D
@onready var visual: ZombieRig = $Visual
@onready var head_zone: HitZone = $HitZones/Head
@onready var voice: ZombieVoice = $Voice
@onready var hit_zones: Array[HitZone] = [$HitZones/Head, $HitZones/Body]


## Called by the Spawner before adding to the tree.
func setup(
	p_data: EnemyData, p_id: int, health_mult: float, speed_mult: float, damage_mult: float, rng: RandomNumberGenerator
) -> void:
	data = p_data
	net_id = p_id
	# Before the rig is ready (`visual` is @onready): every peer picks the same look from the synced id.
	($Visual as ZombieRig).look = hash(net_id)
	_max_health = data.max_health * health_mult
	_speed = data.move_speed * speed_mult
	if not data.uses_speed_mix:
		_speed *= rng.randf_range(0.9, 1.1)
	_damage = data.attack_damage * damage_mult
	_rng = rng


func _ready() -> void:
	add_to_group(&"enemies")
	collision_layer = Layers.ENEMY
	collision_mask = Layers.WORLD
	if _rng == null:
		_rng = RandomNumberGenerator.new()
	if data:
		health.reset(_max_health)
		visual.scale = Vector3.ONE * data.body_scale
		voice.setup(data)
	# The head zone rides on the model's head so headshots follow the animation.
	head_zone.reparent(visual.head, false)
	head_zone.position = Vector3.ZERO
	health.damaged.connect(_on_damaged)
	health.died.connect(_on_died)
	visual.stepped.connect(voice.step)
	_repath_timer = _rng.randf() * 0.25
	visual.position.y = -1.8
	_enter(State.SPAWNING)
	if frozen or stasis:
		_show_ice()


## One ice coat for a Cryo freeze or Stasis, so either ending keeps the other's ice.
func _show_ice() -> void:
	Frost.show_frozen(self, frozen or stasis)


func _physics_process(delta: float) -> void:
	if _held(delta):
		return
	state_time += delta
	_attack_cooldown = maxf(_attack_cooldown - delta, 0.0)
	if not is_on_floor():
		velocity.y -= _gravity * delta
	else:
		velocity.y = -0.1
	match state:
		State.SPAWNING:
			_tick_spawning()
		State.ENTERING:
			entry.tick(self, delta)
		State.CHASING:
			_tick_chasing(delta)
		State.ATTACKING:
			_tick_attacking(delta)
		State.DEAD:
			velocity.x = 0.0
			velocity.z = 0.0
	move_and_slide()


## Stands still for seconds, no attacks. A zombie on its feet inside (chasing or swinging) is
## shoved by push first and its swing is cancelled; one rising or at a window is only held.
func stun(seconds: float, push: Vector3) -> void:
	if state == State.DEAD:
		return
	stun_left = maxf(stun_left, seconds)
	if state == State.CHASING or state == State.ATTACKING:
		velocity.x = push.x
		velocity.z = push.z
		_enter(State.CHASING)
	_stuck_watch.restart(global_position)


## Frozen, in Stasis or stunned: true when this tick is spent held in place.
func _held(delta: float) -> bool:
	if stun_left > 0.0:
		stun_left = maxf(stun_left - delta, 0.0)
		if stun_left == 0.0:
			_stuck_watch.restart(global_position)
	if state == State.DEAD:
		return false
	if frozen or stasis:
		velocity = Vector3.ZERO
		return true
	if stun_left > 0.0:
		_tick_stunned(delta)
		return true
	return false


## Rising or at a window: held in place like Stasis. Inside: the shove slows to a stop.
func _tick_stunned(delta: float) -> void:
	if state != State.CHASING:
		velocity = Vector3.ZERO
		return
	velocity.y = -0.1 if is_on_floor() else velocity.y - _gravity * delta
	_steer(Vector3.ZERO, delta)
	move_and_slide()


func _enter(new_state: State) -> void:
	state = new_state
	state_time = 0.0
	_attack_landed = false


func _tick_spawning() -> void:
	velocity.x = 0.0
	velocity.z = 0.0
	if state_time >= SPAWN_TIME:
		_stuck_watch.restart(global_position)
		entry.tear_timer = data.plank_time
		_enter(State.ENTERING if barrier else State.CHASING)


func _tick_chasing(delta: float) -> void:
	if lure.tick(self, delta):
		return
	_update_target(delta)
	if target == null:
		_steer(Vector3.ZERO, delta)
		return
	var to_target: Vector3 = target.global_position - global_position
	to_target.y = 0.0
	var distance: float = to_target.length()
	_stuck_watch.tick(self, delta, distance)
	if distance <= data.attack_range * 0.85 and _attack_cooldown <= 0.0 and _can_see(target):
		_enter(State.ATTACKING)
		return

	_repath_timer -= delta
	if _repath_timer <= 0.0:
		_repath_timer = _repath_interval(distance)
		agent.target_position = target.global_position

	var next: Vector3 = agent.get_next_path_position()
	var direction: Vector3 = next - global_position
	direction.y = 0.0
	if direction.length_squared() < 0.01 or agent.is_navigation_finished():
		direction = to_target
	direction = direction.normalized()
	if distance < data.attack_range * 0.7:
		direction = Vector3.ZERO
	_steer(direction * _speed + _separation(), delta)
	_face(to_target, delta)


## Chase again from where we stand (after a vault or a relocate); health is kept.
func restart_chase() -> void:
	entry.vault_time = -1.0
	_repath_timer = 0.0
	_stuck_watch.restart(global_position)
	_enter(State.CHASING)


## Where this zombie's loot and power-ups land: inside its window when it died
## outside (still queued, tearing or vaulting), else where it fell.
func drop_point() -> Vector3:
	return barrier.drop_point(global_position) if barrier else global_position


## The round's last zombies run at least this fast so the round never stalls.
func hurry(speed: float) -> void:
	_speed = maxf(_speed, speed)


func _tick_attacking(delta: float) -> void:
	velocity.x = move_toward(velocity.x, 0.0, data.acceleration * delta)
	velocity.z = move_toward(velocity.z, 0.0, data.acceleration * delta)
	if target:
		_face(target.global_position - global_position, delta)
	if not _attack_landed and state_time >= data.attack_windup:
		_attack_landed = true
		_try_hit_target()
	if state_time >= data.attack_windup + STRIKE_TIME:
		_attack_cooldown = data.attack_cooldown
		_enter(State.ENTERING if barrier else State.CHASING)


func _try_hit_target() -> void:
	if target == null or not target.is_alive() or not Net.is_authority():
		return
	var flat: Vector3 = target.global_position - global_position
	flat.y = 0.0
	if flat.length() <= data.attack_range + HIT_SLACK and _can_see(target):
		var info: DamageInfo = DamageInfo.create(_damage, self, DamageInfo.Type.MELEE)
		info.position = target.global_position
		info.impulse = flat.normalized()
		target.take_damage(info)


## True when no world geometry sits between our chest and the target's.
func _can_see(other: Node3D) -> bool:
	var start: Vector3 = global_position + Vector3.UP * 1.2
	var end: Vector3 = other.global_position + Vector3.UP * 1.2
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(start, end, Layers.WORLD)
	return get_world_3d().direct_space_state.intersect_ray(query).is_empty()


func _update_target(delta: float) -> void:
	_retarget_timer -= delta
	if _retarget_timer > 0.0 and target != null and target.is_alive():
		return
	_retarget_timer = 0.5
	target = null
	var best: float = INF
	for node: Node in get_tree().get_nodes_in_group(&"players"):
		var player: Player = node as Player
		if player == null or not player.is_alive():
			continue
		var d: float = global_position.distance_squared_to(player.global_position)
		if d < best:
			best = d
			target = player


func _repath_interval(distance: float) -> float:
	return 0.25 if distance < 10.0 else (0.5 if distance < 30.0 else 1.5)


func _separation() -> Vector3:
	var push: Vector3 = Vector3.ZERO
	for other: Zombie in neighbours:
		if other == self or other.state == State.DEAD:
			continue
		var away: Vector3 = global_position - other.global_position
		away.y = 0.0
		var d: float = away.length()
		if d > 0.001 and d < SEPARATION_RADIUS:
			push += away / d * (SEPARATION_RADIUS - d) / SEPARATION_RADIUS
	return push * SEPARATION_FORCE


func _steer(wish: Vector3, delta: float) -> void:
	var horizontal: Vector3 = Vector3(velocity.x, 0.0, velocity.z).move_toward(wish, data.acceleration * delta)
	velocity.x = horizontal.x
	velocity.z = horizontal.z


func _face(direction: Vector3, delta: float) -> void:
	direction.y = 0.0
	if direction.length_squared() < 0.0001:
		return
	rotation.y = lerp_angle(rotation.y, atan2(-direction.x, -direction.z), clampf(data.turn_speed * delta, 0.0, 1.0))


func _on_damaged(info: DamageInfo) -> void:
	Events.enemy_damaged.emit(self, info)
	if state == State.DEAD:
		return
	DoubleBarrel.apply_impulse(self, info)
	# Flinch: small shove of the body mesh, reads as impact.
	visual.position += global_basis.inverse() * info.impulse.normalized() * 0.06
	visual.pulse_belly()


func _on_died(info: DamageInfo) -> void:
	head_popped = info.is_headshot()
	_enter(State.DEAD)
	if barrier:
		barrier.release(self)
	collision_layer = 0
	for zone: HitZone in hit_zones:
		zone.set_enabled(false)
	Events.enemy_killed.emit(self, info)
	visual.fall_over(head_popped).tween_callback(queue_free)


func _process(delta: float) -> void:
	voice.show_state(state)
	if (frozen or stasis) and state != State.DEAD:
		Frost.initialize_pose(self)
	else:
		visual.follow(self, delta)
