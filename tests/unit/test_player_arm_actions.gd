## Imported arms preserve both-barrel fire and held-trigger spin-up on real weapon scenes.
extends GutTest

const PLAYER: PackedScene = preload("res://systems/player/player.tscn")


func _player_with_weapon(id: StringName) -> Player:
	var player: Player = PLAYER.instantiate() as Player
	add_child_autofree(player)
	player.set_physics_process(false)
	player.weapons.set_process(false)
	player.weapons.give(Content.weapon(id)).set_process(false)
	player.weapons.arm_view.set_process(false)
	return player


func _assert_carry_pose(view: PlayerArmView, pose: Transform3D, rest: Basis) -> void:
	var gun: Weapon = view.weapon
	var grip: Vector3 = view.profile.left.wrist
	var wrist: Vector3 = gun.transform * (grip + gun.pose.reload_hand(grip))
	assert_almost_eq(pose.origin, wrist, Vector3.ONE * .00001)
	assert_gt(wrist.distance_to(gun.transform * grip), .10, "the support hand has left the forepiece")
	var dorsal: Vector3 = pose.basis * rest.inverse() * Vector3.FORWARD
	assert_gt(dorsal.dot((gun.basis * BreakActionReload.BACK).normalized()), 0.5)
	var shell: Node3D = gun.pose.break_action.get_node("ShellR")
	var between_tips: Vector3 = shell.to_global(Vector3.FORWARD * 0.014)
	for tip_name: String in ["GripIndexTip_L", "GripThumbTip_L"]:
		var tip: Node3D = view.find_child(tip_name, true, false)
		var distance: float = (view.skeleton.global_transform * pose * tip.position).distance_to(between_tips)
		assert_between(distance, .005, .012, tip_name)


func _assert_pose_preserves_fire_state(holder: WeaponHolder, carrying: bool = false) -> void:
	var weapon: Weapon = holder.current
	var ammo: int = weapon.instance.ammo_in_mag
	var state: Weapon.State = weapon.state
	var shot_timer: float = weapon._shot_timer
	var reload_timer: float = weapon._reload_timer
	var spin: float = weapon._spin_up._elapsed
	var transform: Transform3D = weapon.transform
	var view: PlayerArmView = holder.arm_view
	view.update_pose()
	assert_eq(view.weapon, weapon)
	assert_true(view.is_visible_in_tree())
	var grips: Array[PlayerArmProfiles.Hand] = [view.profile.right, view.profile.left]
	for index: int in 2:
		var bone: int = view.skeleton.find_bone("hand_R" if index == 0 else "hand_L")
		var pose: Transform3D = view.skeleton.get_bone_global_pose(bone)
		var rest: Basis = view.skeleton.get_bone_global_rest(bone).basis
		if index == 1 and carrying:
			_assert_carry_pose(view, pose, rest)
		else:
			assert_almost_eq(pose.origin, transform * grips[index].wrist, Vector3.ONE * .00001)
			assert_true(pose.basis.is_equal_approx(transform.basis * grips[index].rotation * rest))
		var forearm: int = view.skeleton.get_bone_parent(bone)
		var upper: int = view.skeleton.get_bone_parent(forearm)
		var elbow: Vector3 = view.skeleton.get_bone_global_pose(forearm).origin
		var shoulder: Vector3 = view.skeleton.get_bone_global_pose(upper).origin
		assert_almost_eq(elbow.distance_to(pose.origin), view.skeleton.get_bone_rest(bone).origin.length(), .0001)
		assert_almost_eq(shoulder.distance_to(elbow), view.skeleton.get_bone_rest(forearm).origin.length(), .0001)
	assert_eq(weapon.transform, transform)
	assert_eq(weapon.instance.ammo_in_mag, ammo)
	assert_eq(weapon.state, state)
	assert_eq(weapon._shot_timer, shot_timer)
	assert_eq(weapon._reload_timer, reload_timer)
	assert_eq(weapon._spin_up._elapsed, spin)


func test_imported_arms_follow_both_barrel_blast_and_automatic_empty_reload() -> void:
	for id: StringName in [&"coachman_2b", &"coachman_2b_reforged", &"grubber_sawnoff", &"grubber_sawnoff_reforged"]:
		var player: Player = _player_with_weapon(id)
		var weapon: Weapon = player.weapons.current
		watch_signals(weapon)
		player.last_frame.buttons = InputFrame.ALT_FIRE
		weapon.tick(0.0)
		weapon._process(.001)
		assert_eq(weapon.instance.ammo_in_mag, 0, String(id) + " both barrels consume their rounds")
		assert_signal_emit_count(weapon, "fired", 1)
		assert_true(weapon.is_reloading(), String(id) + " empty gun starts its normal reload")
		_assert_pose_preserves_fire_state(player.weapons)
		weapon.tick(weapon._reload_duration * .5)
		weapon._process(.05)
		_assert_pose_preserves_fire_state(player.weapons, true)
		player.last_frame.buttons = 0
		weapon.tick(weapon._reload_timer + .001)
		weapon._process(.05)
		assert_false(weapon.is_reloading())
		assert_eq(weapon.instance.ammo_in_mag, 2)
		_assert_pose_preserves_fire_state(player.weapons)


func test_imported_arms_follow_bastion_spin_up_and_survive_holster_reset() -> void:
	for id: StringName in [&"bastion_lmg", &"bastion_lmg_reforged"]:
		var player: Player = _player_with_weapon(id)
		var weapon: Weapon = player.weapons.current
		var interval: float = weapon.data.get_fire_interval()
		weapon.trigger_held = true
		weapon.tick(0.0)
		assert_eq(weapon.instance.ammo_in_mag, weapon.data.magazine_size - 1)
		assert_almost_eq(weapon._shot_timer, interval / SpinUp.START_RATE, .00001)
		for frame: int in 30:
			weapon.tick(1.0 / 60.0)
			weapon._process(1.0 / 60.0)
			_assert_pose_preserves_fire_state(player.weapons)
		assert_lt(weapon.instance.ammo_in_mag, weapon.data.magazine_size - 1)
		assert_almost_eq(weapon._spin_up.scale_interval(interval), interval, .00001)
		player.weapons.give(Content.weapon(&"rifle_ar")).set_process(false)
		assert_almost_eq(weapon._spin_up.scale_interval(interval), interval / SpinUp.START_RATE, .00001)
		player.weapons.equip(0)
		weapon.trigger_held = false
		weapon.tick(0.0)
		weapon._process(.001)
		_assert_pose_preserves_fire_state(player.weapons)
