## Weapon-local hand targets and camera-relative shoulders for the shared arm rig.
class_name PlayerArmProfiles
extends RefCounted

const METADATA: String = "res://assets/models/characters/player_arm_grips.json"
static var _geometry: Dictionary = {}


class Hand:
	extends RefCounted
	var wrist: Vector3
	var rotation: Basis
	var shoulder: Vector3
	## Lateral response to weapon height: x when lowering, y when raising.
	var shoulder_sway: Vector2 = Vector2.ZERO
	## Maximum vertical and fore/aft accommodation while the weapon rises.
	var shoulder_lift: Vector2 = Vector2(.07, .112)
	var shoulder_drop: float = 0.0
	## Camera-space shoulder offset blended by the weapon’s existing sprint progress.
	var shoulder_sprint_offset: Vector3 = Vector3.ZERO
	var source_index: Vector3
	var source_thumb: Vector3


class Profile:
	extends RefCounted
	var id: StringName
	var morph: StringName
	var carry_morph: StringName
	var carry_index: Vector3
	var carry_thumb: Vector3
	var hip_position: Vector3
	var right: Hand
	var left: Hand
	var support_part: NodePath


static func weapon_ids() -> Array[StringName]:
	return Content.sorted_ids(&"grips")


static func profile(data: WeaponData) -> Profile:
	var grip: GripData = data.grip if data else null
	if grip == null:
		return null
	var source: Dictionary = _source(grip.id)
	if source.is_empty():
		push_error("Missing authored arm grip geometry: " + String(grip.id))
		return null
	var result: Profile = Profile.new()
	result.id = grip.id
	result.morph = StringName(source["morph"])
	if source.has("carry"):
		var carry: Dictionary = source["carry"]
		var conversion: Basis = Basis(Vector3.RIGHT, Vector3.FORWARD, Vector3.UP)
		result.carry_morph = StringName(carry["morph"])
		result.carry_index = conversion * _vector(carry["index"])
		result.carry_thumb = conversion * _vector(carry["thumb"])
	result.hip_position = data.hip_position
	result.right = _hand(
		"R", grip.right_anchor, source["R"], grip.right_forward, grip.right_dorsal, grip.right_shoulder
	)
	result.left = _hand("L", grip.left_anchor, source["L"], grip.left_forward, grip.left_dorsal, grip.left_shoulder)
	result.right.shoulder_lift = grip.right_shoulder_lift
	result.left.shoulder_lift = grip.left_shoulder_lift
	result.left.shoulder_sway = grip.left_shoulder_sway
	result.right.shoulder_sprint_offset = grip.right_sprint_offset
	result.support_part = grip.support_part
	return result


static func _source(id: StringName) -> Dictionary:
	if _geometry.is_empty() and FileAccess.file_exists(METADATA):
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(METADATA))
		if parsed is Dictionary:
			_geometry = (parsed as Dictionary).get("profiles", {}) as Dictionary
	return _geometry.get(String(id), {}) as Dictionary


static func _hand(
	side: String, anchor: Vector3, source: Dictionary, forward: Vector3, dorsal: Vector3, shoulder: Vector3
) -> Hand:
	var sign_x: float = -1.0 if side == "R" else 1.0
	var rest_forward: Vector3 = Vector3(sign_x, 0, -1).normalized()
	var rotation: Basis = _basis(forward, dorsal) * _basis(rest_forward, Vector3(0, 1, 0)).inverse()
	var centre: Vector3 = _vector(source["center"])
	var rest_wrist: Vector3 = Vector3(sign_x * .61, 0, 1.05)
	var conversion: Basis = Basis(Vector3.RIGHT, Vector3.FORWARD, Vector3.UP)
	var result: Hand = Hand.new()
	result.wrist = conversion * (anchor - rotation * (centre - rest_wrist))
	result.rotation = conversion * rotation * conversion.inverse()
	result.shoulder = conversion * shoulder
	result.shoulder_drop = .35 if side == "L" else 0.0
	result.source_index = conversion * _vector(source["index"])
	result.source_thumb = conversion * _vector(source["thumb"])
	return result


static func _basis(forward: Vector3, dorsal: Vector3) -> Basis:
	var axis: Vector3 = forward.normalized()
	var outward: Vector3 = (dorsal - axis * dorsal.dot(axis)).normalized()
	return Basis(outward.cross(axis), outward, axis)


static func _vector(value: Array) -> Vector3:
	return Vector3(float(value[0]), float(value[1]), float(value[2]))
