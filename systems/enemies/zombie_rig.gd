## Animates the zombie's skinned body during pursuit, attacks, vaults and death.
class_name ZombieRig
extends Node3D

## A foot came down in the walk cycle (twice per cycle).
signal stepped

const HANDS: Array[StringName] = [&"hand_L", &"hand_R"]
const PARTS: Dictionary[StringName, StringName] = {
	&"Hips": &"pelvis",
	&"Torso": &"spine_02",
	&"Head": &"head",
	&"ArmL": &"upperarm_L",
	&"ArmR": &"upperarm_R",
	&"LegL": &"thigh_L",
	&"LegR": &"thigh_R",
}
## Fraction of the pre-hit time spent drawing the striking arm back.
const ATTACK_DRAW: float = 0.62
## Arms start lifting toward a target closer than this.
const REACH_DISTANCE: float = 3.0
const CORPSE_TIME: float = 5.0
## How high the body hops at the middle of a window vault.
const VAULT_HEIGHT: float = 0.45
## Below this stride (a shuffle on the spot) no footsteps play.
const STEP_MIN_STRIDE: float = 0.2

## A skinned .glb from tripo_intake.py --kind zombie, facing +Z.
@export var model: PackedScene
## Other looks of the same zombie type; `look` picks one of `model` and these.
@export var extra_models: Array[PackedScene] = []
## Swell on hit in metres for the glowing parts (Bloater pods); 0 = none. Instance shader parameter `pulse`.
@export var pulse_size: float = 0.0

## Which look to show, the same on every peer (the Zombie sets it from its synced net_id).
var look: int = 0

var head: Node3D

var _skeleton: Skeleton3D
var _bones: Dictionary[StringName, int] = {}
var _rest: Dictionary[StringName, Quaternion] = {}
var _axes: Dictionary[StringName, Quaternion] = {}
var _offsets: Dictionary[StringName, Vector3] = {}
var _hips_rest: Vector3 = Vector3.ZERO
var _body_mesh: GeometryInstance3D
var _pulse_tween: Tween
var _phase: float = 0.0
var _crawler: bool = false
var _look_name: StringName
var _cadence: float = 1.0
var _attack_clip: ZombieStrike


func _ready() -> void:
	var index: int = posmod(look, 1 + extra_models.size())
	var selected: PackedScene = model if index == 0 else extra_models[index - 1]
	var body: Node3D = selected.instantiate() as Node3D
	body.rotation.y = PI
	add_child(body)
	# Keep the existing horde's lighting cost: no per-frame lightmap probe capture.
	for mesh: Node in body.find_children("*", "GeometryInstance3D", true, false):
		(mesh as GeometryInstance3D).gi_mode = GeometryInstance3D.GI_MODE_DISABLED
	_skeleton = body.find_children("*", "Skeleton3D", true, false)[0] as Skeleton3D
	_look_name = selected.resource_path.get_file().get_basename()
	_cadence = ZombieGait.cadence(_look_name)
	_crawler = body.find_child("Crawler", true, false) != null
	if not _crawler:
		_attack_clip = ZombieStrike.attach(_look_name, _skeleton)
	for part_name: StringName in PARTS:
		if _crawler and part_name in [&"LegL", &"LegR"]:
			continue
		_cache_bone(part_name, PARTS[part_name])
	for bone_name: StringName in [&"forearm_L", &"forearm_R", &"hand_L", &"hand_R", &"shin_L", &"shin_R"]:
		_cache_bone(bone_name, bone_name)
	_hips_rest = _skeleton.get_bone_pose_position(_bones[&"Hips"])
	_attach_head(body)
	if not _crawler:
		pose_walk(0.0, 0.0, 0.0)
	_body_mesh = body.find_child("Body", true, false) as GeometryInstance3D
	if _body_mesh and pulse_size > 0.0:
		_body_mesh.extra_cull_margin = pulse_size


func _cache_bone(part_name: StringName, bone_name: StringName) -> void:
	var bone: int = _skeleton.find_bone(bone_name)
	_bones[part_name] = bone
	_rest[part_name] = _skeleton.get_bone_pose_rotation(bone)
	_axes[part_name] = _skeleton.get_bone_global_rest(bone).basis.get_rotation_quaternion()
	_offsets[part_name] = Vector3.ZERO


func _attach_head(body: Node3D) -> void:
	head = body.find_child("HeadCenter", true, false) as Node3D
	var center: Transform3D = _skeleton.global_transform.affine_inverse() * head.global_transform
	var attachment: BoneAttachment3D = BoneAttachment3D.new()
	attachment.name = "HeadAttachment"
	attachment.bone_name = &"head"
	_skeleton.add_child(attachment)
	attachment.transform = _skeleton.get_bone_global_rest(_bones[&"Head"])
	head.reparent(attachment, false)
	head.transform = attachment.transform.affine_inverse() * center


## Present the current gameplay state at its synchronized time.
func follow(zombie: Zombie, delta: float) -> void:
	var t: float = zombie.state_time
	if zombie.state == Zombie.State.SPAWNING:
		position.y = lerpf(-1.8, 0.0, clampf(t / Zombie.SPAWN_TIME, 0.0, 1.0))
		return
	if zombie.state == Zombie.State.DEAD:
		return
	var vault: float = zombie.entry.vault_progress()
	if vault >= 0.0:
		pose_vault(vault, delta)
		return
	position = position.lerp(Vector3.ZERO, clampf(delta * 10.0, 0.0, 1.0))
	if zombie.state == Zombie.State.ATTACKING:
		var windup: float = maxf(zombie.data.attack_windup, 0.01)
		if t < windup:
			pose_attack(t / windup, true)
		else:
			pose_attack(1.0 + (t - windup) / Zombie.STRIKE_TIME, true)
		return
	var reach: float = 0.0
	if zombie.state == Zombie.State.ENTERING:
		reach = 1.0
	elif zombie.target:
		var distance: float = zombie.global_position.distance_to(zombie.target.global_position)
		reach = clampf(1.0 - distance / REACH_DISTANCE, 0.0, 1.0)
	pose_walk(Vector2(zombie.velocity.x, zombie.velocity.z).length(), reach, delta)


## Limbs go slack, the body tips over onto a blood pool, lies for a while and
## sinks. Runs on every peer. Connect to the returned tween to free the zombie at the end.
## `popped`: killed by a headshot. `fresh`: seen dying, not a corpse a late joiner found,
## which gets the missing head but no pool or flying chunks.
func fall_over(popped: bool = false, fresh: bool = true) -> Tween:
	pose_dead()
	var scene: Node = get_tree().current_scene
	var parent: Node = scene if scene else get_tree().root
	if fresh:
		BloodPool.lay_death(parent, (get_parent() as Node3D).global_position)
	if popped and Impact.gore() == Impact.Gore.FULL and not Build.is_server():
		pop_head()
		if fresh:
			HeadPop.spawn(parent, head.global_position)
	var fall_dir: float = 1.0 if randf() < 0.5 else -1.0  # cosmetic
	var tween: Tween = create_tween()
	ZombieReactions.fall(self, tween, _look_name, fall_dir)
	tween.tween_interval(CORPSE_TIME)
	tween.tween_property(self, "position:y", -1.0, 1.5)
	return tween


## Collapses the head bone: the head and face skinned to it shrink into the neck, leaving a stump.
func pop_head() -> void:
	_skeleton.set_bone_pose_scale(_bones[&"Head"], Vector3.ONE * 0.01)


## The head bone's scale in skeleton space (1 normally, near 0 after pop_head).
func head_scale() -> float:
	return _skeleton.get_bone_global_pose(_bones[&"Head"]).basis.get_scale().x


func has_part(part_name: StringName) -> bool:
	return _bones.has(part_name)


## Limb angle away from the model's rest pose (x = pitch), for tests and effects.
func get_offset(part_name: StringName) -> Vector3:
	if _attack_clip and _attack_clip.is_playing() and _bones.has(part_name):
		var delta: Quaternion = _rest[part_name].inverse() * _skeleton.get_bone_pose_rotation(_bones[part_name])
		return (_axes[part_name] * delta * _axes[part_name].inverse()).get_euler()
	return _offsets.get(part_name, Vector3.ZERO)


## Walk cycle scaled by ground speed; `reach` (0..1) lifts the arms toward a close target.
func pose_walk(speed: float, reach: float, delta: float) -> void:
	if _crawler:
		_pose_crawl(speed, reach, delta)
		return
	if _attack_clip:
		_attack_clip.release()
	var before: float = sin(_phase)
	_phase += delta * (1.5 + speed * 2.5) * _cadence
	var stride: float = clampf(speed / 2.0, 0.0, 1.0)
	if stride > STEP_MIN_STRIDE and signf(sin(_phase)) != signf(before):
		stepped.emit()
	ZombieGait.pose(self, _look_name, _phase, stride, reach)
	if _attack_clip:
		_attack_clip.blend_out(delta)


## The model reaches contact at t = 1 and finishes recovering at t = 2.
func pose_attack(t: float, blend_from_walk: bool = false) -> void:
	if _crawler:
		_pose_crawl_attack(t)
	else:
		_attack_clip.sample(t, blend_from_walk)


func _pose_crawl(speed: float, reach: float, delta: float) -> void:
	_phase += delta * (1.5 + speed * 2.5)
	var swing: float = sin(_phase) * clampf(speed / 2.0, 0.0, 1.0)
	var lift: float = -0.12 - 0.16 * reach
	pose_part(&"ArmL", Vector3(lift - swing * 0.12, 0.0, 0.0))
	pose_part(&"ArmR", Vector3(lift + swing * 0.12, 0.0, 0.0))
	pose_part(&"forearm_L", Vector3(-0.15 - maxf(swing, 0.0) * 0.18, 0.0, 0.0))
	pose_part(&"forearm_R", Vector3(-0.15 - maxf(-swing, 0.0) * 0.18, 0.0, 0.0))
	pose_part(&"Torso", Vector3(-0.025, 0.0, swing * 0.025))
	pose_part(&"Head", Vector3(0.0, 0.0, sin(_phase * 0.5) * 0.06))
	_skeleton.set_bone_pose_position(_bones[&"Hips"], _hips_rest)


func _pose_crawl_attack(t: float) -> void:
	var raised: float = ease(clampf(t, 0.0, 1.0), 0.5)
	var lowered: float = ease(clampf(t - 1.0, 0.0, 1.0), 0.3)
	var lift: float = raised * (1.0 - lowered)
	pose_part(&"ArmL", Vector3(-0.75 * lift, 0.0, 0.0))
	pose_part(&"ArmR", Vector3(-0.75 * lift, 0.0, 0.0))
	pose_part(&"forearm_L", Vector3(-0.14 - 0.18 * lift, 0.0, 0.0))
	pose_part(&"forearm_R", Vector3(-0.14 - 0.18 * lift, 0.0, 0.0))
	pose_part(&"Torso", Vector3(-0.10 * lift, 0.0, 0.0))
	_skeleton.set_bone_pose_position(_bones[&"Hips"], _hips_rest)


## Climb over a window sill. `t` 0..1: hands reach for the sill, the body
## hops up and pitches forward, legs tuck, then it drops into the room.
func pose_vault(t: float, delta: float = 1.0) -> void:
	if _attack_clip:
		_attack_clip.release()
	for hand: StringName in HANDS:
		_skeleton.set_bone_pose_rotation(_bones[hand], _rest[hand])
	var hop: float = sin(t * PI)
	position = Vector3(0.0, VAULT_HEIGHT * hop, 0.0)
	ZombieReactions.vault(self, _look_name, t, hop)
	if _attack_clip:
		_attack_clip.blend_out(delta)


## Limbs go slack as the body falls.
func pose_dead() -> Tween:
	var tween: Tween = create_tween().set_parallel().set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	var slack: Dictionary[StringName, Vector3] = {
		&"ArmL": Vector3(0.9, 0.0, -0.3),
		&"ArmR": Vector3(0.7, 0.0, 0.3),
		&"Head": Vector3(0.5, 0.0, 0.3),
		&"LegL": Vector3(0.2, 0.0, 0.0),
		&"LegR": Vector3(-0.15, 0.0, 0.0),
		&"Torso": Vector3.ZERO,
		&"forearm_L": Vector3(-0.2, 0.0, 0.0),
		&"forearm_R": Vector3(-0.15, 0.0, 0.0),
		&"hand_L": Vector3.ZERO,
		&"hand_R": Vector3.ZERO,
		&"shin_L": Vector3(0.25, 0.0, 0.0),
		&"shin_R": Vector3(0.2, 0.0, 0.0),
	}
	ZombieReactions.relax_pose(_look_name, slack)
	for part_name: StringName in slack:
		if _bones.has(part_name):
			_relax_bone(tween, part_name, slack[part_name])
	if _attack_clip:
		_attack_clip.relax(tween, _bones.values())
	return tween


## Bloater belly swells for a moment when hit (zombies with a `pulse_size`).
func pulse_belly() -> void:
	if _body_mesh == null or pulse_size <= 0.0:
		return
	if _pulse_tween:
		_pulse_tween.kill()
	_set_pulse(pulse_size)
	_pulse_tween = create_tween()
	_pulse_tween.tween_method(_set_pulse, pulse_size, 0.0, 0.25).set_trans(Tween.TRANS_ELASTIC).set_ease(Tween.EASE_OUT)


func pulse_amount() -> float:
	if _body_mesh == null:
		return 0.0
	var amount: Variant = _body_mesh.get_instance_shader_parameter(&"pulse")
	return amount if amount is float else 0.0


func _set_pulse(amount: float) -> void:
	_body_mesh.set_instance_shader_parameter(&"pulse", amount)


func set_hip_offset(offset: Vector3) -> void:
	_skeleton.set_bone_pose_position(_bones[&"Hips"], _hips_rest + offset)


## Roll along each bone's length so the palm turns without swinging the wrist off its strike path.
func pose_grasp(forearm: StringName, hand: StringName, elbow: Vector3, roll: float) -> void:
	pose_part(forearm, elbow, Quaternion(Vector3.UP, roll * 0.7))
	_skeleton.set_bone_pose_rotation(_bones[hand], _rest[hand] * Quaternion(Vector3.UP, roll * 0.3))


func pose_part(part_name: StringName, offset: Vector3, twist: Quaternion = Quaternion.IDENTITY) -> void:
	if _bones.has(part_name):
		_offsets[part_name] = offset
		var turn: Quaternion = _axes[part_name].inverse() * Quaternion.from_euler(offset) * _axes[part_name]
		_skeleton.set_bone_pose_rotation(_bones[part_name], _rest[part_name] * turn * twist)


func _relax_bone(tween: Tween, part_name: StringName, slack: Vector3) -> void:
	var bone: int = _bones[part_name]
	var start: Quaternion = _skeleton.get_bone_pose_rotation(bone)
	var axes: Quaternion = _axes[part_name]
	var finish: Quaternion = _rest[part_name] * axes.inverse() * Quaternion.from_euler(slack) * axes
	var offset: Vector3 = get_offset(part_name)
	var relax: Callable = func(weight: float) -> void:
		_skeleton.set_bone_pose_rotation(bone, start.slerp(finish, weight))
		_offsets[part_name] = offset.lerp(slack, weight)
	tween.tween_method(relax, 0.0, 1.0, 0.4)
