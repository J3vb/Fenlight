## Solves the shared arm rig against weapon grips while shoulders stay in camera space.
class_name PlayerArmPose
extends RefCounted

const RELAXED_BEND: float = 24.0

var _flex_positive: bool = true
var _skeleton: Skeleton3D
var _upper: PackedInt32Array = []
var _lower: PackedInt32Array = []
var _hand: PackedInt32Array = []
var _upper_rest: Array[Transform3D] = []
var _lower_rest: Array[Transform3D] = []
var _hand_rest: Array[Transform3D] = []
var _upper_length: PackedFloat32Array = []
var _lower_length: PackedFloat32Array = []
## Left hand turned to hold something (a frag) instead of its grip, blended in by hold_weight.
var _hold_rotation: Basis = Basis.IDENTITY
var _align_forearm: bool = false
var _hold_weight: float = 0.0


func _init(skeleton: Skeleton3D) -> void:
	_skeleton = skeleton
	for side: String in ["R", "L"]:
		var upper: int = skeleton.find_bone("upperarm_" + side)
		var lower: int = skeleton.find_bone("forearm_" + side)
		var hand: int = skeleton.find_bone("hand_" + side)
		_upper.append(upper)
		_lower.append(lower)
		_hand.append(hand)
		_upper_rest.append(skeleton.get_bone_global_rest(upper))
		_lower_rest.append(skeleton.get_bone_global_rest(lower))
		_hand_rest.append(skeleton.get_bone_global_rest(hand))
		_upper_length.append(skeleton.get_bone_rest(lower).origin.length())
		_lower_length.append(skeleton.get_bone_rest(hand).origin.length())


func pose(
	profile: PlayerArmProfiles.Profile,
	weapon_transform: Transform3D,
	pump_delta: Vector3 = Vector3.ZERO,
	sprint: float = 0.0,
	relax: float = 0.0
) -> void:
	var travel: Vector3 = weapon_transform.origin - profile.hip_position
	var right_lift: Vector3 = _shoulder_offset(profile.right, travel) + profile.right.shoulder_sprint_offset * sprint
	var left_lift: Vector3 = _shoulder_offset(profile.left, travel) + profile.left.shoulder_sprint_offset * sprint
	_arm(0, profile.right, weapon_transform, Vector3.ZERO, right_lift)
	_arm(1, profile.left, weapon_transform, pump_delta, left_lift, relax)


## Turns the left hand so its fingers point along `fingers` with the back of the hand toward `back`
## (skeleton space), blended over its grip by weight. Weight 0 gives the grip back.
func set_left_hold(fingers: Vector3, back: Vector3, weight: float, align_forearm: bool = false) -> void:
	_align_forearm = align_forearm and weight > 0.0
	_hold_weight = clampf(weight, 0.0, 1.0)
	_hold_rotation = (_basis(fingers, back) * _basis(_hand_rest[1].basis.y, Vector3.FORWARD).inverse())


func _shoulder_offset(grip: PlayerArmProfiles.Hand, travel: Vector3) -> Vector3:
	var rise: float = clampf(travel.y * 1.5, 0, .07)
	var lift: Vector3 = Vector3(0, minf(rise, grip.shoulder_lift.x), 0)
	lift.x = (clampf(travel.y, -.10, .10) * (grip.shoulder_sway.x if travel.y < 0 else grip.shoulder_sway.y))
	lift.y += clampf(travel.y * grip.shoulder_drop, -.04, 0)
	lift.z = minf(clampf(travel.z * .5, 0, rise * 1.6), grip.shoulder_lift.y)
	return lift


## relax (0-1) lets a hand that has left its grip turn toward its forearm, so the wrist stays within RELAXED_BEND.
func _arm(
	index: int,
	grip: PlayerArmProfiles.Hand,
	weapon_transform: Transform3D,
	part_delta: Vector3,
	lift: Vector3,
	relax: float = 0.0
) -> void:
	var rotation: Basis = weapon_transform.basis * grip.rotation
	if index == 1 and _hold_weight > 0.0:
		rotation = rotation.orthonormalized().slerp(_hold_rotation, _hold_weight)
	var target: Transform3D = Transform3D(
		rotation * _hand_rest[index].basis, weapon_transform * (grip.wrist + part_delta)
	)
	var palm: Vector3 = target.basis.y.normalized()
	var dorsal: Vector3 = rotation * Vector3.FORWARD
	var shoulder: Vector3 = grip.shoulder + lift
	var elbow: Vector3 = _elbow(index, shoulder, target.origin, palm, dorsal)
	if relax > 0.0:
		elbow = _toward_hanging(index, shoulder, target.origin, elbow, relax)
	var forearm: Vector3 = target.origin - elbow
	if relax > 0.0:
		target.basis = _relaxed(target.basis, forearm, relax)
		palm = target.basis.y.normalized()
		dorsal = target.basis * _hand_rest[index].basis.inverse() * Vector3.FORWARD
	_set_bone(_upper[index], _upper_rest[index], shoulder, elbow - shoulder, dorsal)
	var forearm_back: Vector3 = _forearm_dorsal(forearm, palm, dorsal)
	if index == 1 and _align_forearm:
		# Transport the glove's roll along the arm while the hand turns away from its grip.
		var neutral: Vector3 = Quaternion(palm, forearm.normalized()) * dorsal
		forearm_back = forearm_back.slerp(neutral, smoothstep(0.0, 0.25, relax))
	_set_bone(_lower[index], _lower_rest[index], elbow, forearm, forearm_back)
	_skeleton.set_bone_global_pose(_hand[index], target)


## Turns the elbow around the shoulder-wrist axis toward hanging out and down, so it cannot pop between poles
## while the hand follows reload key poses that the grip-based search was never tuned for.
func _toward_hanging(index: int, shoulder: Vector3, wrist: Vector3, elbow: Vector3, relax: float) -> Vector3:
	var axis: Vector3 = (wrist - shoulder).normalized()
	var center: Vector3 = shoulder + axis * axis.dot(elbow - shoulder)
	var current: Vector3 = elbow - center
	var outward: Vector3 = Vector3(1.0 if index == 0 else -1.0, -1.0, 0.0)
	var hanging: Vector3 = outward - axis * outward.dot(axis)
	if hanging.length_squared() < .000001 or current.length_squared() < .000001:
		return elbow
	var angle: float = current.signed_angle_to(hanging, axis)
	return center + current.rotated(axis, angle * relax)


func _relaxed(hand: Basis, forearm: Vector3, relax: float) -> Basis:
	var palm: Vector3 = hand.y.normalized()
	var forward: Vector3 = forearm.normalized()
	var bend: float = palm.angle_to(forward)
	var limit: float = lerpf(PI, deg_to_rad(16.0 if _align_forearm else RELAXED_BEND), relax)
	var axis: Vector3 = palm.cross(forward)
	if bend <= limit or axis.length_squared() < .000001:
		return hand
	return Basis(axis.normalized(), bend - limit) * hand


func _elbow(index: int, shoulder: Vector3, wrist: Vector3, palm: Vector3, dorsal: Vector3) -> Vector3:
	var offset: Vector3 = wrist - shoulder
	var direction: Vector3 = offset.normalized()
	var upper: float = _upper_length[index]
	var lower: float = _lower_length[index]
	var distance: float = clampf(offset.length(), absf(upper - lower) + .0001, upper + lower - .0001)
	var along: float = (upper * upper - lower * lower + distance * distance) / (2.0 * distance)
	var height: float = sqrt(maxf(0.0, upper * upper - along * along))
	var bend: Vector3 = _bend(palm, direction, index) * height
	var center: Vector3 = shoulder + direction * along
	var frame: Basis = Basis(bend, direction.cross(bend), center)
	# Keep one twist branch throughout the circle search so the elbow cannot pop.
	var preferred: Vector3 = (wrist - center - bend).normalized()
	_flex_positive = palm.dot(dorsal - preferred * dorsal.dot(preferred)) >= 0
	if _elbow_score(center + bend, shoulder, wrist, palm, dorsal, index) == 0.0:
		return center + bend
	# Search the elbow circle continuously so grips and segment lengths stay exact.
	var low: float = -PI * .5
	var high: float = PI * .5
	for _step: int in 18:
		var first: float = lerpf(low, high, .381966)
		var second: float = lerpf(low, high, .618034)
		var score_a: float = (
			_elbow_score(_circle(frame, first), shoulder, wrist, palm, dorsal, index) + first * first * .0001
		)
		var score_b: float = (
			_elbow_score(_circle(frame, second), shoulder, wrist, palm, dorsal, index) + second * second * .0001
		)
		if score_a < score_b:
			high = second
		else:
			low = first
	return _circle(frame, (low + high) * .5)


func _bend(palm: Vector3, direction: Vector3, index: int) -> Vector3:
	var bend: Vector3 = -palm + direction * palm.dot(direction)
	if bend.length_squared() < .000001:
		var outward: Vector3 = Vector3(1.0 if index == 0 else -1.0, -1, 0)
		bend = outward - direction * outward.dot(direction)
	if bend.length_squared() < .000001:
		bend = direction.cross(Vector3.FORWARD)
	return bend.normalized()


func _circle(frame: Basis, angle: float) -> Vector3:
	return frame.z + frame.x * cos(angle) + frame.y * sin(angle)


func _elbow_score(
	elbow: Vector3, shoulder: Vector3, wrist: Vector3, palm: Vector3, dorsal: Vector3, index: int
) -> float:
	var forward: Vector3 = (wrist - elbow).normalized()
	var outward: Vector3 = _forearm_dorsal(forward, palm, dorsal)
	var along: float = palm.dot(forward)
	var flex: float = absf(atan2(palm.dot(outward), along))
	var deviation: float = absf(atan2(palm.dot(outward.cross(forward)), along))
	var wrist_bend: float = forward.angle_to(palm)
	var side: float = 1.0 if index == 0 else -1.0
	var cost: float = pow(maxf(0, wrist_bend - deg_to_rad(34.5)), 2)
	cost += pow(maxf(0, flex - deg_to_rad(29.5)), 2)
	cost += pow(maxf(0, deviation - deg_to_rad(19.5)), 2)
	cost += pow(maxf(0, .005 - elbow.x * side) * 10, 2)
	cost += pow(maxf(0, elbow.y - shoulder.y - .01) * 10, 2)
	cost += pow(maxf(0, elbow.y - wrist.y + .005) * 10, 2)
	return cost


func _forearm_dorsal(direction: Vector3, palm: Vector3, dorsal: Vector3) -> Vector3:
	var forward: Vector3 = direction.normalized()
	var outward: Vector3 = (dorsal - forward * dorsal.dot(forward)).normalized()
	var lateral: Vector3 = outward.cross(forward)
	var across: float = palm.dot(lateral)
	var limit: float = maxf(0, palm.dot(forward)) * tan(deg_to_rad(19.5))
	if absf(across) <= limit:
		return outward
	var flex: float = palm.dot(outward)
	var angle: float = atan2(across, flex)
	var boundary: float = asin(clampf(limit / Vector2(flex, across).length(), 0, 1))
	var desired: float = signf(angle) * (boundary if _flex_positive else PI - boundary)
	var transported: Vector3 = Basis(Quaternion(forward, palm)) * outward
	var roll: float = transported.signed_angle_to(dorsal, palm)
	var turn: float = clampf(wrapf(desired - angle, -PI, PI), roll - deg_to_rad(19.5), roll + deg_to_rad(19.5))
	return outward.rotated(forward, turn)


func _set_bone(index: int, rest: Transform3D, at: Vector3, direction: Vector3, dorsal: Vector3) -> void:
	var rotation: Basis = _basis(direction, dorsal) * _basis(rest.basis.y, Vector3.FORWARD).inverse()
	_skeleton.set_bone_global_pose(index, Transform3D(rotation * rest.basis, at))


func _basis(direction: Vector3, dorsal: Vector3) -> Basis:
	var axis: Vector3 = direction.normalized()
	var outward: Vector3 = (dorsal - axis * dorsal.dot(axis)).normalized()
	return Basis(outward.cross(axis), outward, axis)
