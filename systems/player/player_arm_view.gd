## One imported first-person arm rig per weapon holder, showing the owner's worn vest cuffs, charm and implant.
class_name PlayerArmView
extends Node3D

const ARMS: PackedScene = preload("res://assets/models/characters/player_arms.glb")
const COMMON: RarityLook = preload("res://content/looks/rarity/common.tres")
const FRAG_MODEL: PackedScene = preload("res://assets/models/throwables/frag.glb")
const PLACEHOLDERS: Array[String] = ["HandRight", "HandLeft", "SleeveRight", "SleeveLeft"]

static var _warned_no_grip: Dictionary[StringName, bool] = {}
static var _warned_reach: Dictionary[StringName, bool] = {}
static var _warned_piece: Dictionary[StringName, bool] = {}

var skeleton: Skeleton3D
var mesh: MeshInstance3D
var weapon: Weapon
var profile: PlayerArmProfiles.Profile
## The owner's lethal slot; its cook drives grenade_hold (the left hand holds the frag).
var thrower: GrenadeThrower
var grenade_hold: GrenadeHold = GrenadeHold.new()

var _solver: PlayerArmPose
var _support: Node3D
var _support_rest: Vector3 = Vector3.ZERO
var _carry_index: int = -1
var _carry_weight: float = 0.0
var _morph_index: int = -1
var _markers: Array[Node3D] = []
var _hand_rest: Array[Transform3D] = []
var _gear: Array[Node3D] = []
var _charm: Node3D
var _mount: Node3D
var _swing: CharmSwing = CharmSwing.new()
var _frag: Node3D
var _left_hand: int = -1


func _ready() -> void:
	process_priority = 1
	physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF
	var arms: Node3D = ARMS.instantiate() as Node3D
	add_child(arms)
	skeleton = arms.find_children("*", "Skeleton3D", true, false)[0] as Skeleton3D
	mesh = arms.find_child("PlayerArms", true, false) as MeshInstance3D
	_solver = PlayerArmPose.new(skeleton)
	_left_hand = skeleton.find_bone("hand_L")
	for side: String in ["R", "L"]:
		_hand_rest.append(skeleton.get_bone_global_rest(skeleton.find_bone("hand_" + side)))
		_markers.append(arms.find_child("GripIndexTip_" + side, true, false) as Node3D)
		_markers.append(arms.find_child("GripThumbTip_" + side, true, false) as Node3D)
	for node: Node in find_children("*", "GeometryInstance3D", true, false):
		var geometry: GeometryInstance3D = node as GeometryInstance3D
		geometry.layers = ScopeLens.VIEWMODEL_LAYER
		geometry.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	GearLook.apply(self, COMMON, Color.WHITE, Color.WHITE)
	hide()


func bind_weapon(current: Weapon) -> void:
	weapon = current
	profile = null
	_support = null
	_mount = null
	_swing.reset()
	if current == null:
		hide()
		return
	profile = PlayerArmProfiles.profile(current.data)
	if profile == null:
		_warn_no_grip(current.data)
		hide()
		return
	var viewmodel: Node3D = current.get_node("Viewmodel").get_child(0) as Node3D
	_mount = viewmodel.find_child("CharmMount", true, false) as Node3D
	for part: String in PLACEHOLDERS:
		var placeholder: Node3D = viewmodel.find_child(part, true, false) as Node3D
		if placeholder:
			placeholder.hide()
	_support = (
		viewmodel.get_node_or_null(profile.support_part) as Node3D if not profile.support_part.is_empty() else null
	)
	if _support and not _support.has_meta(&"arm_support_rest"):
		_support.set_meta(&"arm_support_rest", current.to_local(_support.global_position))
	_support_rest = (_support.get_meta(&"arm_support_rest", Vector3.ZERO) as Vector3 if _support else Vector3.ZERO)
	_select_grip()
	update_pose()
	place_charm(0.0)


func _warn_no_grip(data: WeaponData) -> void:
	if data.grip != null or _warned_no_grip.has(data.id):
		return
	_warned_no_grip[data.id] = true
	Log.warn(&"player", &"weapon_has_no_grip", {"weapon": String(data.id)})


func _select_grip() -> void:
	if _carry_index >= 0:
		mesh.set_blend_shape_value(_carry_index, 0.0)
	_carry_weight = 0.0
	_carry_index = (mesh.find_blend_shape_by_name(profile.carry_morph) if not profile.carry_morph.is_empty() else -1)
	if _morph_index >= 0:
		mesh.set_blend_shape_value(_morph_index, 0.0)
	_morph_index = (mesh.find_blend_shape_by_name(profile.morph) if not profile.morph.is_empty() else -1)
	if _morph_index >= 0:
		mesh.set_blend_shape_value(_morph_index, 1.0)
	_set_markers(0, profile.right)
	_set_markers(1, profile.left)


func _set_markers(index: int, grip: PlayerArmProfiles.Hand) -> void:
	var inverse: Transform3D = _hand_rest[index].affine_inverse()
	_markers[index * 2].position = inverse * grip.source_index
	_markers[index * 2 + 1].position = inverse * grip.source_thumb


func _pose_fingers(weight: float) -> void:
	if _carry_index < 0 or weight == _carry_weight:
		return
	_carry_weight = weight
	mesh.set_blend_shape_value(_carry_index, weight)
	mesh.set_blend_shape_value(_morph_index, 1.0 - weight)
	var inverse: Transform3D = _hand_rest[1].affine_inverse()
	_markers[2].position = inverse * profile.left.source_index.lerp(profile.carry_index, weight)
	_markers[3].position = inverse * profile.left.source_thumb.lerp(profile.carry_thumb, weight)


func _process(delta: float) -> void:
	if thrower:
		grenade_hold.step(thrower.cooking, delta, thrower.data.recover_time)
	update_pose()
	place_charm(delta)


## Hangs the charm from the gun's CharmMount. It stays a child of this view, so a freed gun never frees it.
func place_charm(delta: float) -> void:
	if _charm == null:
		return
	_charm.visible = _mount != null and is_instance_valid(_mount)
	if _charm.visible:
		var mount: Transform3D = _mount.global_transform
		_charm.global_transform = Transform3D(mount.basis * _swing.step(mount, delta), mount.origin)


func update_pose() -> void:
	visible = is_instance_valid(weapon) and profile != null and weapon.active and weapon.visible
	if not visible or not is_visible_in_tree():
		return
	var pump_delta: Vector3 = weapon.to_local(_support.global_position) - _support_rest if _support else Vector3.ZERO
	pump_delta += weapon.pose.reload_hand(profile.left.wrist + pump_delta)
	var relax: float = weapon.pose.reload_relax()
	var to_holder: Basis = (get_parent() as Node3D).transform.basis.inverse()
	if weapon.pose.break_action and grenade_hold.weight == 0.0:
		var carry: BreakActionReload = weapon.pose.break_action
		_solver.set_left_hold(
			weapon.basis * BreakActionReload.FINGERS, weapon.basis * BreakActionReload.BACK, carry.relax, true
		)
		_pose_fingers(carry.hand_weight)
	else:
		_pose_fingers(0.0)
		_solver.set_left_hold(to_holder * GrenadeHold.FINGERS, to_holder * GrenadeHold.BACK, grenade_hold.weight)
	if grenade_hold.weight > 0.0:
		pump_delta += _hold_delta(profile.left.wrist + pump_delta)
		relax = maxf(relax, grenade_hold.weight)
	_solver.pose(profile, weapon.transform, pump_delta, weapon._sprint_progress, relax)
	if _carry_weight > 0.0:
		var pinch: Vector3 = (_markers[2].position + _markers[3].position) * 0.5
		var hand: Transform3D = skeleton.global_transform * skeleton.get_bone_global_pose(_left_hand)
		weapon.pose.break_action.place_in_hand(hand * pinch)
	_place_frag()
	if weapon.pose.motion and weapon.is_reloading() and not _warned_reach.has(weapon.data.id):
		_check_reach()


## Weapon-local offset that takes the left wrist from its grip to the grenade hold spot.
func _hold_delta(grip_wrist: Vector3) -> Vector3:
	var target: Vector3 = (get_parent() as Node3D).transform.affine_inverse() * grenade_hold.wrist_target()
	return (weapon.transform.affine_inverse() * target - grip_wrist) * grenade_hold.weight


## The frag in the left palm while cooking, on the viewmodel layer like the arms.
func _place_frag() -> void:
	if _frag == null:
		if not grenade_hold.shows_frag:
			return
		_frag = FRAG_MODEL.instantiate() as Node3D
		_frag.name = "HeldFrag"
		add_child(_frag)
		for node: Node in _frag.find_children("*", "GeometryInstance3D", true, false):
			(node as GeometryInstance3D).layers = ScopeLens.VIEWMODEL_LAYER
			(node as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_frag.visible = grenade_hold.shows_frag
	var holder: Transform3D = (get_parent() as Node3D).transform
	var wrist: Vector3 = holder * skeleton.get_bone_global_pose(_left_hand).origin
	_frag.position = holder.affine_inverse() * grenade_hold.frag_position(wrist)


## How far the left forearm stretches past its length; zero when the hand target is reachable.
func left_reach_gap() -> float:
	var hand: int = skeleton.find_bone("hand_L")
	var forearm: int = skeleton.get_bone_parent(hand)
	var length: float = skeleton.get_bone_rest(hand).origin.length()
	var span: float = skeleton.get_bone_global_pose(forearm).origin.distance_to(
		skeleton.get_bone_global_pose(hand).origin
	)
	return absf(span - length)


func _check_reach() -> void:
	var gap: float = left_reach_gap()
	if gap > 0.02:
		_warned_reach[weapon.data.id] = true
		Log.warn(
			&"player", &"reload_motion_unreachable", {"weapon": String(weapon.data.id), "gap": snappedf(gap, 0.001)}
		)


## Rebuilds the worn gear pieces seen in first person from the owner's look.
func apply_look(look: CharacterLook) -> void:
	for node: Node3D in _gear:
		node.free()
	_gear.clear()
	_charm = null
	if look.slots.has(&"vest"):
		_attach_cuffs(look.slots[&"vest"])
	if look.slots.has(&"charm"):
		_attach_charm(look.slots[&"charm"])
	if look.slots.has(&"implant"):
		_attach_implant(look.slots[&"implant"])


func _attach_implant(entry: Dictionary) -> void:
	var shown: Array = GearRig.resolve(&"implant", entry)
	var visual: GearVisual = shown[0]
	var finish: RarityLook = shown[1]
	var piece: Node3D = visual.scene_for(finish.tier).instantiate() as Node3D
	var port: Node = piece.find_child("Port", true, false)
	if port == null or piece.find_child("Module", true, false) == null:
		_warn_piece(visual.id)
		piece.free()
		return
	port.free()
	var attachment: BoneAttachment3D = BoneAttachment3D.new()
	attachment.name = "Implant"
	attachment.bone_name = "forearm_L"
	skeleton.add_child(attachment)
	attachment.add_child(piece)
	var rest: Transform3D = skeleton.get_bone_global_rest(skeleton.find_bone("forearm_L"))
	piece.basis = rest.basis.inverse() * Basis(Vector3.BACK, PI / 4.0)
	_show_piece(
		attachment, finish, entry.get("dyes", [CharacterLook.DEFAULT_DYE_MAIN, CharacterLook.DEFAULT_DYE_ACCENT])
	)


func _attach_charm(entry: Dictionary) -> void:
	var shown: Array = GearRig.resolve(&"charm", entry)
	var visual: GearVisual = shown[0]
	var finish: RarityLook = shown[1]
	_charm = visual.scene_for(finish.tier).instantiate() as Node3D
	_charm.name = "Charm"
	add_child(_charm)
	_show_piece(_charm, finish, entry.get("dyes", [CharacterLook.DEFAULT_DYE_MAIN, CharacterLook.DEFAULT_DYE_ACCENT]))
	place_charm(0.0)


func _attach_cuffs(entry: Dictionary) -> void:
	var shown: Array = GearRig.resolve(&"vest", entry)
	var visual: GearVisual = shown[0]
	var finish: RarityLook = shown[1]
	var vest: Node3D = visual.scene_for(finish.tier).instantiate() as Node3D
	var dyes: Array = entry.get("dyes", [CharacterLook.DEFAULT_DYE_MAIN, CharacterLook.DEFAULT_DYE_ACCENT])
	for side: String in ["R", "L"]:
		var cuff: Node3D = vest.find_child("CuffFP_" + side, true, false) as Node3D
		if cuff == null:
			_warn_piece(visual.id)
			continue
		var rest: Transform3D = skeleton.get_bone_global_rest(skeleton.find_bone("forearm_" + side))
		var offset: Transform3D = rest.affine_inverse() * cuff.transform
		cuff.get_parent().remove_child(cuff)
		cuff.owner = null
		var attachment: BoneAttachment3D = BoneAttachment3D.new()
		attachment.name = "Cuff_" + side
		attachment.bone_name = "forearm_" + side
		skeleton.add_child(attachment)
		attachment.add_child(cuff)
		cuff.transform = offset
		_show_piece(attachment, finish, dyes)
	vest.free()


func _show_piece(piece: Node3D, finish: RarityLook, dyes: Array) -> void:
	_gear.append(piece)
	GearLook.apply(piece, finish, dyes[0], dyes[1])
	for node: Node in piece.find_children("*", "GeometryInstance3D", true, false):
		var geometry: GeometryInstance3D = node as GeometryInstance3D
		geometry.layers = ScopeLens.VIEWMODEL_LAYER
		geometry.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


func _warn_piece(visual_id: StringName) -> void:
	if _warned_piece.has(visual_id):
		return
	_warned_piece[visual_id] = true
	Log.warn(&"gear", &"fp_piece_missing", {"visual": String(visual_id)})
