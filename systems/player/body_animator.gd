## Plays the third-person body clips from the player's measured movement, crouch and downed state,
## puts the held gun in the right hand and plays its fire and reload motions on the upper body.
## Visual only: works the same for the owner's shadow body and for remote teammates.
class_name BodyAnimator
extends Node

## Ground speed (m/s) at which each clip's feet stay planted, from the stride and
## cycle length in tools/assets/player_clips.py. The tree speeds clips up past them.
const WALK_CLIP_SPEED: float = 3.1
const RUN_CLIP_SPEED: float = 5.5
const CROUCH_CLIP_SPEED: float = 1.6
const MAX_TIME_SCALE: float = 1.7
## A position jump longer than this between two pose updates is a teleport (respawn), not movement.
const TELEPORT_DISTANCE: float = 2.5
## Synced positions can skip ticks; a body that has not moved for this long is standing still.
const STALE_TIME: float = 0.25
const SMOOTHING: float = 12.0
## Downed players crawl at this share of walk speed (Player._move).
const DOWNED_SPEED_SHARE: float = 0.2
const FADE_TIME: float = 0.2
const GROUND: StringName = &"ground"
const CROUCH: StringName = &"crouch"
const DOWNED: StringName = &"downed"
const STATE_REQUEST: StringName = &"parameters/state/transition_request"
const STATE_CURRENT: StringName = &"parameters/state/current_state"
const GROUND_BLEND: StringName = &"parameters/ground/blend_position"
const CROUCH_BLEND: StringName = &"parameters/crouch/blend_position"
const DOWNED_BLEND: StringName = &"parameters/downed/blend_position"
const TIME_SCALE: StringName = &"parameters/speed/scale"
const FIRE_REQUEST: StringName = &"parameters/fire/request"
const RELOAD_REQUEST: StringName = &"parameters/reload/request"
const RELOAD_SCALE: StringName = &"parameters/reload_speed/scale"
## Bones the fire and reload clips move; the legs keep walking underneath.
const UPPER_BODY: Array[StringName] = [
	&"spine_02",
	&"spine_03",
	&"neck",
	&"head",
	&"clavicle_L",
	&"upperarm_L",
	&"forearm_L",
	&"hand_L",
	&"clavicle_R",
	&"upperarm_R",
	&"forearm_R",
	&"hand_R",
]
## Where a gun's grip point sits in hand_R's bone space, tuned on the teammate look render.
const PALM: Vector3 = Vector3(0.0, -0.109, -0.051)

@export var player: Player
## The imported player.glb instance that holds the Skeleton3D and AnimationPlayer.
@export var model: Node3D
## The synced head pivot whose pitch the chest and head follow.
@export var pitch_source: Node3D

## No screen (dedicated server, headless soak): nothing is posed. Tests clear it before _ready.
var headless: bool = DisplayServer.get_name() == "headless"
var tree: AnimationTree
var aim: AimPitch
var local_velocity: Vector3 = Vector3.ZERO
## Set by the owner each tick and sent to everyone by PoseSync.
var held_weapon: StringName = &""
## Seconds the current reload takes (empty mag and Serums included); 0 when not reloading.
var reload_time: float = 0.0
var gun: Node3D
## This peer drives the player. Read once in _ready: asking every tick errors once the peer has left.
var is_owner: bool = false

var _last_position: Vector3 = Vector3.ZERO
var _since_update: float = 0.0
var _measured: Vector3 = Vector3.ZERO
var _state: StringName = GROUND
var _hand: BoneAttachment3D
var _shown_weapon: StringName = &""
var _shown_reload: float = 0.0
var _reload_length: float = 1.0
var _started_reload: float = 0.0


func _ready() -> void:
	Events.reload_started.connect(_on_reload_started)
	is_owner = player.is_multiplayer_authority()
	if headless:
		return
	var players: Array[Node] = model.find_children("*", "AnimationPlayer", true, false)
	if players.is_empty() or not (players[0] as AnimationPlayer).has_animation(&"reload"):
		Log.warn(&"player", &"body_clips_missing", {"model": model.scene_file_path})
		headless = true
		return
	var anim: AnimationPlayer = players[0] as AnimationPlayer
	_reload_length = anim.get_animation(&"reload").length
	tree = AnimationTree.new()
	tree.name = "BodyTree"
	tree.tree_root = _build_tree(player.walk_speed, player.sprint_speed)
	_add_upper_body(tree.tree_root as AnimationNodeBlendTree, _upper_body_tracks(anim.get_animation(&"fire")))
	model.add_child(tree)
	tree.anim_player = tree.get_path_to(anim)
	tree.active = true
	tree.set(STATE_REQUEST, String(GROUND))
	var skeleton: Skeleton3D = model.find_children("*", "Skeleton3D", true, false)[0] as Skeleton3D
	aim = AimPitch.new()
	aim.name = "AimPitch"
	aim.pitch_source = pitch_source
	skeleton.add_child(aim)
	_hand = BoneAttachment3D.new()
	_hand.name = "HeldGun"
	_hand.bone_name = "hand_R"
	skeleton.add_child(_hand)
	_last_position = player.global_position


func _physics_process(delta: float) -> void:
	if is_owner:
		_publish()
	if tree == null:
		return
	_measure(delta)
	_apply(pick_state(player.is_downed, player.is_crouching))
	if held_weapon != _shown_weapon:
		_show_weapon()
	if reload_time != _shown_reload:
		_play_reload()


## A teammate's shot: a short upper-body kick on top of whatever the legs do.
func fire() -> void:
	if tree:
		tree.set(FIRE_REQUEST, AnimationNodeOneShot.ONE_SHOT_REQUEST_FIRE)


func _publish() -> void:
	var weapon: Weapon = player.weapons.current
	held_weapon = weapon.data.id if weapon else &""
	reload_time = _started_reload if weapon and weapon.is_reloading() else 0.0


## Per-round guns report one round's time; the whole reload loads every missing round.
func _on_reload_started(reloader: Player, duration: float) -> void:
	if reloader != player:
		return
	_started_reload = duration
	var weapon: Weapon = player.weapons.current
	if weapon and weapon.data.reload_per_round:
		var ammo: WeaponInstance = weapon.instance
		var rounds: int = mini(weapon.data.magazine_size - ammo.ammo_in_mag, ammo.ammo_reserve)
		_started_reload += maxi(rounds - 1, 0) * weapon._reload_duration


## Velocity over the time since the position last changed, so pose updates that skip ticks still read as steady.
func _measure(delta: float) -> void:
	_since_update += delta
	var step: Vector3 = player.global_position - _last_position
	step.y = 0.0
	if not step.is_zero_approx() or _since_update >= STALE_TIME:
		var moved: bool = step.length() <= TELEPORT_DISTANCE
		_measured = player.global_basis.inverse() * (step / _since_update) if moved else Vector3.ZERO
		_last_position = player.global_position
		_since_update = 0.0
	local_velocity = local_velocity.lerp(_measured, 1.0 - exp(-SMOOTHING * delta))


## Downed wins over crouch, crouch over standing.
static func pick_state(downed: bool, crouching: bool) -> StringName:
	if downed:
		return DOWNED
	return CROUCH if crouching else GROUND


func _apply(state: StringName) -> void:
	if state != _state:
		_state = state
		tree.set(STATE_REQUEST, String(state))
	var speed: float = Vector2(local_velocity.x, local_velocity.z).length()
	var walk: float = player.walk_speed
	tree.set(GROUND_BLEND, Vector2(local_velocity.x, -local_velocity.z) / walk)
	tree.set(CROUCH_BLEND, clampf(speed / (walk * player.crouch_speed_multiplier), 0.0, 1.0))
	tree.set(DOWNED_BLEND, clampf(speed / (walk * DOWNED_SPEED_SHARE), 0.0, 1.0))
	tree.set(TIME_SCALE, time_scale(state, speed, walk))


## Speeds clips up when the body moves faster than the clip's own stride, so feet do not slide.
static func time_scale(state: StringName, speed: float, walk: float) -> float:
	var clip_speed: float = WALK_CLIP_SPEED
	if state == CROUCH:
		clip_speed = CROUCH_CLIP_SPEED
	elif state == GROUND and speed > walk * 1.05:
		clip_speed = RUN_CLIP_SPEED
	elif state == DOWNED:
		return 1.0
	return clampf(speed / clip_speed, 1.0, MAX_TIME_SCALE)


func _show_weapon() -> void:
	_shown_weapon = held_weapon
	if gun:
		gun.queue_free()
		gun = null
	if held_weapon.is_empty() or not Content.has(&"weapons", held_weapon):
		return
	var data: WeaponData = Content.weapon(held_weapon)
	if data.world_model == null:
		Log.warn(&"player", &"world_model_missing", {"weapon": String(held_weapon)})
		return
	gun = data.world_model.instantiate() as Node3D
	gun.transform = hold_transform(data.grip)
	_hand.add_child(gun)
	if is_owner:
		for node: Node in gun.find_children("*", "GeometryInstance3D", true, false):
			(node as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY


## The gun model in hand_R's space: barrel along the bone, grip point on the palm.
static func hold_transform(grip: GripData) -> Transform3D:
	var turn: Basis = Basis(Vector3.RIGHT, PI / 2.0)
	var anchor: Vector3 = Vector3.ZERO
	if grip:
		anchor = Vector3(grip.right_anchor.x, grip.right_anchor.z, -grip.right_anchor.y)
	return Transform3D(turn, PALM - turn * anchor)


## The reload clip is stretched to the owner's real reload time and fades out when the reload ends early.
func _play_reload() -> void:
	_shown_reload = reload_time
	if reload_time <= 0.0:
		tree.set(RELOAD_REQUEST, AnimationNodeOneShot.ONE_SHOT_REQUEST_FADE_OUT)
		return
	tree.set(RELOAD_SCALE, _reload_length / maxf(reload_time, 0.1))
	tree.set(RELOAD_REQUEST, AnimationNodeOneShot.ONE_SHOT_REQUEST_FIRE)


func _build_tree(walk: float, sprint: float) -> AnimationNodeBlendTree:
	var ground: AnimationNodeBlendSpace2D = AnimationNodeBlendSpace2D.new()
	var reach: float = sprint / walk
	ground.min_space = Vector2(-1.0, -1.0)
	ground.max_space = Vector2(1.0, reach)
	var points: Dictionary[StringName, Vector2] = {
		&"idle": Vector2.ZERO,
		&"walk_fwd": Vector2(0.0, 1.0),
		&"walk_back": Vector2(0.0, -1.0),
		&"walk_left": Vector2(-1.0, 0.0),
		&"walk_right": Vector2(1.0, 0.0),
		&"run": Vector2(0.0, reach),
	}
	for clip: StringName in points:
		ground.add_blend_point(_clip(clip), points[clip], -1, clip)
	var root: AnimationNodeBlendTree = AnimationNodeBlendTree.new()
	root.add_node(GROUND, ground)
	root.add_node(CROUCH, _line(&"crouch_idle", &"crouch_walk"))
	root.add_node(DOWNED, _line(&"downed_idle", &"downed_crawl"))
	var state: AnimationNodeTransition = AnimationNodeTransition.new()
	state.xfade_time = FADE_TIME
	for input: StringName in [GROUND, CROUCH, DOWNED]:
		state.add_input(String(input))
	root.add_node(&"state", state)
	root.add_node(&"speed", AnimationNodeTimeScale.new())
	for index: int in 3:
		root.connect_node(&"state", index, [GROUND, CROUCH, DOWNED][index])
	root.connect_node(&"speed", 0, &"state")
	return root


## Fire and reload play after the speed scale, so running does not speed them up.
func _add_upper_body(root: AnimationNodeBlendTree, tracks: Array[NodePath]) -> void:
	root.add_node(&"fire", _one_shot(tracks, 0.03, 0.12))
	root.add_node(&"fire_clip", _clip(&"fire"))
	root.add_node(&"reload", _one_shot(tracks, 0.15, 0.2))
	root.add_node(&"reload_speed", AnimationNodeTimeScale.new())
	root.add_node(&"reload_clip", _clip(&"reload"))
	root.connect_node(&"fire", 0, &"speed")
	root.connect_node(&"fire", 1, &"fire_clip")
	root.connect_node(&"reload_speed", 0, &"reload_clip")
	root.connect_node(&"reload", 0, &"fire")
	root.connect_node(&"reload", 1, &"reload_speed")
	root.connect_node(&"output", 0, &"reload")


func _upper_body_tracks(clip: Animation) -> Array[NodePath]:
	var tracks: Array[NodePath] = []
	for index: int in clip.get_track_count():
		var path: NodePath = clip.track_get_path(index)
		if StringName(path.get_concatenated_subnames()) in UPPER_BODY:
			tracks.append(path)
	return tracks


func _one_shot(tracks: Array[NodePath], fade_in: float, fade_out: float) -> AnimationNodeOneShot:
	var shot: AnimationNodeOneShot = AnimationNodeOneShot.new()
	shot.fadein_time = fade_in
	shot.fadeout_time = fade_out
	shot.filter_enabled = true
	for path: NodePath in tracks:
		shot.set_filter_path(path, true)
	return shot


func _line(still: StringName, moving: StringName) -> AnimationNodeBlendSpace1D:
	var line: AnimationNodeBlendSpace1D = AnimationNodeBlendSpace1D.new()
	line.min_space = 0.0
	line.max_space = 1.0
	line.add_blend_point(_clip(still), 0.0, -1, still)
	line.add_blend_point(_clip(moving), 1.0, -1, moving)
	return line


func _clip(clip: StringName) -> AnimationNodeAnimation:
	var node: AnimationNodeAnimation = AnimationNodeAnimation.new()
	node.animation = clip
	return node
