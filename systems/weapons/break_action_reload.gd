## First-person break-action animation. Both shell props live in the barrel set's frame.
class_name BreakActionReload
extends Node3D

const FINGERS: Vector3 = Vector3(0.84, 0.13, -0.53)
const BACK: Vector3 = Vector3(-0.15, 0.88, 0.44)

var hand_weight: float = 0.0
var relax: float = 0.0
var _hinge: Node3D
var _closed_to_weapon: Transform3D
var _loaded: int = 0
var _shell_center: Vector3
var _follow_hand: float = 0.0
var _first: int = 0
var _held: int = 0
var _open: float = 0.0
var _seats: PackedVector3Array = []
@onready var _shells: Array[Node3D] = [$ShellL, $ShellR]


func bind(weapon: Weapon) -> void:
	_hinge = get_parent() as Node3D
	_closed_to_weapon = weapon.global_transform.affine_inverse() * _hinge.global_transform
	for part: String in ["BarrelL", "BarrelR"]:
		var barrel: MeshInstance3D = _hinge.get_node(part) as MeshInstance3D
		var cap: Vector3 = Vector3.BACK * barrel.get_aabb().end.z
		_seats.append(barrel.transform * cap)


func sample(t: float, loaded: int, reserve: int) -> void:
	_loaded = loaded
	_open = smoothstep(0.015, 0.25, t) * (1.0 - smoothstep(0.77, 0.97, t))
	_hinge.rotation.x = -0.98 * _open
	var insert: float = smoothstep(0.36, 0.68, t)
	var carry: Vector3 = Vector3(-0.082, -0.046, 0.095) * (1.0 - insert)
	carry.y += 0.022 * sin(PI * insert)
	_first = clampi(loaded, 0, 1)
	_held = clampi(loaded + reserve - 1, _first, 1)
	for i: int in _shells.size():
		var moving: bool = i >= loaded
		_shells[i].position = _seats[i] + (carry if moving else Vector3.ZERO)
		_shells[i].visible = (_open > 0.04 and (not moving or (i <= _held and t >= 0.28 and reserve > 0)))
	_shell_center = _shells[_held].position
	_follow_hand = 1.0 - smoothstep(0.52, 0.68, t) if loaded < _shells.size() and reserve > 0 else 0.0
	hand_weight = smoothstep(0.10, 0.29, t) * (1.0 - smoothstep(0.68, 0.85, t))
	relax = smoothstep(0.01, 0.15, t) * (1.0 - smoothstep(0.82, 0.98, t))


func settle(delta: float, loaded: int) -> void:
	if _open == 0.0 and relax == 0.0 and not (_shells[0].visible or _shells[1].visible):
		return
	var step: float = 1.0 if loaded > _loaded else delta * 8.0
	_open = move_toward(_open, 0.0, step)
	relax = move_toward(relax, 0.0, step)
	hand_weight = move_toward(hand_weight, 0.0, step)
	_hinge.rotation.x = -0.98 * _open
	_follow_hand = 0.0
	for i: int in _shells.size():
		_shells[i].position = _seats[i]
		_shells[i].visible = i < loaded and _open > 0.04


## Keep the carried props between the solved glove tips, handing them to the barrel set as they seat.
func place_in_hand(pinch: Vector3) -> void:
	if _follow_hand == 0.0:
		return
	var start: Vector3 = _seats[_held]
	var carried: Vector3 = _shell_center.lerp(to_local(pinch) + Vector3.BACK * 0.014, _follow_hand)
	for i: int in range(_first, _held + 1):
		var spacing: Vector3 = _seats[i] - start
		_shells[i].position = carried + spacing.lerp(spacing.limit_length(0.019), _follow_hand)


func hand_offset(grip: Vector3) -> Vector3:
	if _open == 0.0 and hand_weight == 0.0:
		return Vector3.ZERO
	var local_grip: Vector3 = _closed_to_weapon.affine_inverse() * grip
	var opened: Transform3D = _closed_to_weapon * Transform3D(_hinge.basis, Vector3.ZERO)
	var wrist: Vector3 = opened * _shell_center + Vector3(-0.125, 0.014, 0.042)
	return (opened * local_grip).lerp(wrist, hand_weight) - grip
