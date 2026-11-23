## Samples each upright model's Blender clip at the zombie's synchronized attack time.
## The manual player yields its tracked channels to the procedural rig on exit.
class_name ZombieStrike
extends AnimationPlayer

const CLIPS: Dictionary[StringName, Animation] = {
	&"shambler": preload("res://assets/animations/zombies/shambler_attack.tres"),
	&"shambler_guard": preload("res://assets/animations/zombies/shambler_guard_attack.tres"),
	&"bloater": preload("res://assets/animations/zombies/bloater_attack.tres"),
	&"glower": preload("res://assets/animations/zombies/glower_attack.tres"),
}
const CONTACT_TIME: float = 0.45
const BLEND_TIME: float = 0.10

var _clip: Animation
var _skeleton: Skeleton3D
var _mesh: MeshInstance3D
var _fingers: int
var _hips: int
var _playing_clip: bool = false
var _exit_left: float = 0.0
var _start_rotations: Array[Quaternion] = []
var _start_hips: Vector3
var _start_fingers: float


static func attach(look_name: StringName, skeleton: Skeleton3D) -> ZombieStrike:
	if not CLIPS.has(look_name):
		return null
	var player: ZombieStrike = ZombieStrike.new(skeleton, CLIPS[look_name])
	skeleton.get_parent().add_child(player)
	return player


func _init(skeleton: Skeleton3D, clip: Animation) -> void:
	_clip = clip
	_skeleton = skeleton
	_mesh = skeleton.get_node("Body") as MeshInstance3D
	_fingers = _mesh.find_blend_shape_by_name("ReachFingers")
	_hips = skeleton.find_bone("pelvis")
	_start_rotations.resize(skeleton.get_bone_count())
	callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	var library: AnimationLibrary = AnimationLibrary.new()
	library.add_animation(&"strike", _clip)
	add_animation_library(&"", library)


func sample(phase: float, blend_from_walk: bool) -> void:
	if not _playing_clip:
		_snapshot()
		_playing_clip = true
		_exit_left = 0.0
		play(&"strike")
	var time: float = clampf(phase, 0.0, 1.0) * CONTACT_TIME
	time += clampf(phase - 1.0, 0.0, 1.0) * (_clip.length - CONTACT_TIME)
	seek(time, true)
	if blend_from_walk and time < BLEND_TIME:
		_blend(smoothstep(0.0, BLEND_TIME, time))


## Remove last frame's clip contribution before walk or vault writes its own bones.
func release() -> void:
	if _playing_clip:
		_snapshot()
		_playing_clip = false
		stop(true)
		_exit_left = BLEND_TIME
	if _exit_left > 0.0:
		for bone: int in _skeleton.get_bone_count():
			_skeleton.set_bone_pose_rotation(bone, _skeleton.get_bone_rest(bone).basis.get_rotation_quaternion())
		_skeleton.set_bone_pose_position(_hips, _skeleton.get_bone_rest(_hips).origin)
		if _fingers >= 0:
			_mesh.set_blend_shape_value(_fingers, 0.0)


func blend_out(delta: float) -> void:
	if _exit_left > 0.0:
		_exit_left = maxf(0.0, _exit_left - delta)
		_blend(1.0 - smoothstep(0.0, BLEND_TIME, _exit_left))


## Death already animates the procedural limbs. Unwind the remaining clip-only channels too.
func relax(tween: Tween, limb_bones: Array) -> void:
	if not _playing_clip and _exit_left <= 0.0:
		return
	stop(true)
	_playing_clip = false
	_exit_left = 0.0
	_snapshot()
	var release_clip: Callable = func(weight: float) -> void:
		for bone: int in _skeleton.get_bone_count():
			if bone == _hips or bone not in limb_bones:
				var rest: Quaternion = _skeleton.get_bone_rest(bone).basis.get_rotation_quaternion()
				_skeleton.set_bone_pose_rotation(bone, _start_rotations[bone].slerp(rest, weight))
		_skeleton.set_bone_pose_position(_hips, _start_hips.lerp(_skeleton.get_bone_rest(_hips).origin, weight))
		if _fingers >= 0:
			_mesh.set_blend_shape_value(_fingers, lerpf(_start_fingers, 0.0, weight))
	tween.tween_method(release_clip, 0.0, 1.0, 0.4)


func _snapshot() -> void:
	for bone: int in _skeleton.get_bone_count():
		_start_rotations[bone] = _skeleton.get_bone_pose_rotation(bone)
	_start_hips = _skeleton.get_bone_pose_position(_hips)
	if _fingers >= 0:
		_start_fingers = _mesh.get_blend_shape_value(_fingers)


func _blend(weight: float) -> void:
	for bone: int in _skeleton.get_bone_count():
		var rotation: Quaternion = _skeleton.get_bone_pose_rotation(bone)
		_skeleton.set_bone_pose_rotation(bone, _start_rotations[bone].slerp(rotation, weight))
	_skeleton.set_bone_pose_position(_hips, _start_hips.lerp(_skeleton.get_bone_pose_position(_hips), weight))
	if _fingers >= 0:
		_mesh.set_blend_shape_value(_fingers, lerpf(_start_fingers, _mesh.get_blend_shape_value(_fingers), weight))
