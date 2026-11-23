## Both break-action viewmodels follow the gameplay clock and the morphed support glove.
extends GutTest

const MODELS: Array[StringName] = [
	&"coachman_2b", &"grubber_sawnoff", &"coachman_2b_reforged", &"grubber_sawnoff_reforged"
]


func _holder(id: StringName, loaded: int, reserve: int) -> WeaponHolder:
	var camera: Camera3D = Camera3D.new()
	add_child_autofree(camera)
	var holder: WeaponHolder = WeaponHolder.new()
	camera.add_child(holder)
	holder.setup(null, camera)
	var weapon: Weapon = holder.give(Content.weapon(id))
	weapon.instance.ammo_in_mag = loaded
	weapon.instance.ammo_reserve = reserve
	assert_true(weapon.start_reload())
	return holder


func _advance(holder: WeaponHolder, fraction: float) -> void:
	var weapon: Weapon = holder.current
	weapon.tick(weapon._reload_duration * fraction)
	weapon.pose.update(0.05)
	holder.arm_view.update_pose()


func test_open_action_carries_shells_between_thumb_and_index_then_seats_them() -> void:
	for id: StringName in MODELS:
		var holder: WeaponHolder = _holder(id, 0, 2)
		var gun: Weapon = holder.current
		var action: BreakActionReload = gun.pose.break_action
		var hinge: Node3D = action.get_parent_node_3d()
		var barrel: MeshInstance3D = hinge.get_node("BarrelL")
		var first: Node3D = action.get_node("ShellL")
		var second: Node3D = action.get_node("ShellR")
		var view: PlayerArmView = holder.arm_view
		var seat: Vector3 = barrel.transform * (Vector3.BACK * barrel.get_aabb().end.z)
		_advance(holder, 0.4)
		assert_lt(hinge.rotation.x, -0.8, String(id))
		assert_true(first.visible and second.visible)
		assert_eq(view.mesh.get_blend_shape_value(view.mesh.find_blend_shape_by_name(view.profile.carry_morph)), 1.0)
		var hand: Transform3D = (
			view.skeleton.global_transform * view.skeleton.get_bone_global_pose(view.skeleton.find_bone("hand_L"))
		)
		for marker_name: String in ["GripIndexTip_L", "GripThumbTip_L"]:
			var tip: Node3D = view.find_child(marker_name, true, false)
			var center: Vector3 = second.to_global(Vector3.FORWARD * 0.014)
			assert_between((hand * tip.position).distance_to(center), 0.005, 0.012, String(id) + " " + marker_name)
		assert_almost_eq(first.position.distance_to(second.position), 0.019, 0.0001, "both shells touch in the glove")
		assert_gt(first.position.distance_to(seat), 0.055)
		_advance(holder, 0.33)
		assert_almost_eq(first.position, seat, Vector3.ONE * 0.0001)
		assert_eq(gun.instance.ammo_in_mag, 0)
		_advance(holder, 0.28)
		assert_eq(gun.instance.ammo_in_mag, 2)
		assert_eq(hinge.rotation.x, 0.0)
		assert_false(first.visible or second.visible)
		holder.get_parent().free()


func test_top_up_leaves_loaded_shell_seated_and_one_in_reserve_supplies_only_one() -> void:
	for id: StringName in MODELS:
		for loaded: int in [0, 1]:
			var holder: WeaponHolder = _holder(id, loaded, 1)
			var action: BreakActionReload = holder.current.pose.break_action
			var left: Node3D = action.get_node("ShellL")
			var right: Node3D = action.get_node("ShellR")
			_advance(holder, 0.20)
			assert_eq(left.visible, loaded == 1)
			var seated: Vector3 = left.position
			_advance(holder, 0.22)
			assert_true(left.visible)
			assert_eq(right.visible, loaded == 1)
			if loaded == 1:
				assert_eq(left.position, seated)
			RoundReload.cancel(holder.current)
			for step: int in 4:
				holder.current.pose.update(0.05)
				holder.arm_view.update_pose()
			assert_eq(action.get_parent_node_3d().rotation.x, 0.0)
			assert_false(left.visible or right.visible)
			assert_eq(holder.current.instance.ammo_in_mag, loaded)
			assert_eq(holder.current.instance.ammo_reserve, 1)
			assert_true(holder.current.start_reload())
			_advance(holder, 1.01)
			assert_eq(holder.current.instance.ammo_in_mag, loaded + 1)
			holder.get_parent().free()
