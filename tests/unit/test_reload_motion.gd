## Magazine reload motion: rest at both ends, magazine home before ammo lands, hand carries the magazine.
extends GutTest

const PLAYER: PackedScene = preload("res://systems/player/player.tscn")
const CENTER: Vector3 = Vector3(0.0, -0.1, -0.2)
const TOP: Vector3 = Vector3(0.0, -0.04, -0.2)
const STARTERS: Array[StringName] = [&"rifle_ar", &"kestrel_smg", &"talon_dmr"]


func _motion() -> ReloadMotion:
	return ReloadMotion.for_magazine(CENTER, TOP, Vector3.DOWN)


func test_rest_at_start_and_end() -> void:
	var motion: ReloadMotion = _motion()
	for empty: bool in [false, true]:
		for t: float in [0.0, 1.0]:
			motion.sample(empty, t)
			assert_eq(motion.hand_weight, 0.0)
			assert_eq(motion.mag_offset, Vector3.ZERO)
			assert_eq(motion.roll, 0.0)
			assert_eq(motion.bolt_back, 0.0 if t == 1.0 or not empty else 1.0)


func test_magazine_seated_before_ammo_lands() -> void:
	var motion: ReloadMotion = _motion()
	for empty: bool in [false, true]:
		var seated: float = ReloadMotion.seated_at(empty)
		assert_lt(seated, 0.8)
		var t: float = seated
		while t <= 1.0:
			motion.sample(empty, t)
			assert_eq(motion.mag_offset, Vector3.ZERO, "seated at %.2f" % t)
			t += 0.01
		motion.sample(empty, seated - 0.08)
		assert_gt(motion.mag_offset.length(), 0.001, "magazine still moving before it seats")


func test_hand_carries_the_magazine_while_it_moves() -> void:
	var motion: ReloadMotion = _motion()
	var t: float = 0.12
	while t < ReloadMotion.SEATED:
		motion.sample(false, t)
		assert_almost_eq(motion.hand_weight, 1.0, 0.0001)
		assert_almost_eq(motion.hand_target, CENTER + ReloadMotion.GRAB + motion.mag_offset, Vector3.ONE * 0.01)
		t += 0.01


func test_empty_reload_presses_the_bolt_catch_then_releases_the_bolt() -> void:
	var motion: ReloadMotion = _motion()
	motion.sample(false, 0.84)
	assert_eq(motion.bolt_back, 0.0, "tactical reload never moves the bolt")
	motion.sample(true, 0.765)
	assert_eq(motion.bolt_back, 1.0, "bolt stays locked back until the catch is pressed")
	assert_almost_eq(motion.hand_target, TOP + ReloadMotion.CATCH + ReloadMotion.PRESS, Vector3.ONE * 0.002)
	motion.sample(true, ReloadMotion.BOLT_RELEASE + 0.005)
	assert_eq(motion.bolt_back, 0.0, "bolt home after the release")


func _player_with(id: StringName) -> Player:
	var player: Player = PLAYER.instantiate() as Player
	add_child_autofree(player)
	player.set_physics_process(false)
	player.weapons.set_process(false)
	player.weapons.give(Content.weapon(id)).set_process(false)
	player.weapons.arm_view.set_process(false)
	return player


func test_magazine_guns_get_the_motion_and_others_keep_the_dip() -> void:
	for id: StringName in STARTERS:
		assert_not_null(_player_with(id).weapons.current.pose.motion, String(id))
	assert_not_null(_player_with(&"brenner_trench").weapons.current.pose.motion, "shell loading from LoadShell")
	assert_null(_player_with(&"fieldhand_lever").weapons.current.pose.motion, "round by round with no LoadShell")


func test_left_arm_reaches_every_key_pose_and_returns_to_its_grip() -> void:
	for id: StringName in STARTERS:
		var player: Player = _player_with(id)
		var weapon: Weapon = player.weapons.current
		var view: PlayerArmView = player.weapons.arm_view
		var magazine: Node3D = weapon.find_child("Magazine", true, false) as Node3D
		var rest: Vector3 = magazine.position
		for empty: bool in [false, true]:
			for t: float in [0.12, 0.25, 0.65, 0.7, 0.75, 0.78, 0.8, 0.86]:
				weapon.state = Weapon.State.RELOADING
				weapon._empty_reload = empty
				weapon._reload_duration = 1.0
				weapon._reload_timer = 1.0 - t
				weapon.pose.update(1.0)
				view.update_pose()
				assert_lt(
					view.left_reach_gap(), 0.02, "%s %s reach at %.2f" % [id, "empty" if empty else "tactical", t]
				)
		weapon.tick(1.0)
		assert_false(weapon.is_reloading())
		weapon.pose.update(1.0)
		view.update_pose()
		var hand: int = view.skeleton.find_bone("hand_L")
		var wrist: Vector3 = weapon.transform * view.profile.left.wrist
		assert_almost_eq(view.skeleton.get_bone_global_pose(hand).origin, wrist, Vector3.ONE * 0.0001)
		assert_eq(magazine.position, rest)


func test_brenner_hand_carries_one_shell_into_the_port_per_round() -> void:
	var player: Player = _player_with(&"brenner_trench")
	var weapon: Weapon = player.weapons.current
	var shell: Node3D = weapon.find_child("LoadShell", true, false) as Node3D
	var rest: Vector3 = shell.position
	assert_false(shell.visible, "hidden until a reload")
	weapon.instance.ammo_in_mag = 3
	assert_true(weapon.start_reload())
	for step: Array in [[0.4, true], [ReloadMotion.SHELL_IN + 0.01, true], [0.9, false]]:
		weapon._reload_timer = weapon._reload_duration * (1.0 - step[0])
		weapon.pose.update(1.0)
		player.weapons.arm_view.update_pose()
		assert_eq(shell.visible, step[1], "shell shown at %.2f" % step[0])
		assert_lt(player.weapons.arm_view.left_reach_gap(), 0.02)
	weapon._reload_timer = weapon._reload_duration * (1.0 - ReloadMotion.SHELL_IN)
	weapon.pose.update(1.0)
	assert_almost_eq(shell.position, rest, Vector3.ONE * 0.0001, "in the port before the round counts")
	weapon.tick(10.0)
	weapon.pose.update(1.0)
	assert_false(weapon.is_reloading())
	assert_false(shell.visible)


func _cues_in_sweep(motion: ReloadMotion, empty: bool) -> Array[StringName]:
	var heard: Array[StringName] = []
	var last: float = 0.0
	for step: int in range(1, 101):
		var t: float = step / 100.0
		var cue: StringName = motion.cue_between(empty, last, t)
		if not cue.is_empty():
			heard.append(cue)
		last = t
	return heard


func test_each_sound_moment_plays_once_in_order() -> void:
	var magazine: ReloadMotion = _motion()
	assert_eq(_cues_in_sweep(magazine, false), [&"mag_out", &"mag_in"] as Array[StringName])
	assert_eq(_cues_in_sweep(magazine, true), [&"mag_out", &"mag_in", &"bolt"] as Array[StringName])
	var shells: ReloadMotion = ReloadMotion.for_shells(CENTER)
	assert_eq(_cues_in_sweep(shells, false), [&"shell_in"] as Array[StringName])
	assert_eq(_cues_in_sweep(shells, true), [&"shell_in", &"pump"] as Array[StringName])
	for cue: StringName in [&"mag_out", &"mag_in", &"bolt", &"shell_in", &"pump"]:
		assert_true(WeaponPose.CUES.has(cue), String(cue))


func _heard_during_reload(player: Player, seconds: float) -> Array[AudioStream]:
	var weapon: Weapon = player.weapons.current
	var heard: Array[AudioStream] = []
	var steps: int = int(seconds / 0.01)
	for i: int in steps:
		weapon.tick(0.01)
		weapon.pose.update(0.01)
		if weapon.pose.mech_audio.stream and (heard.is_empty() or heard[-1] != weapon.pose.mech_audio.stream):
			heard.append(weapon.pose.mech_audio.stream)
	return heard


func test_magazine_reload_plays_its_moves_instead_of_the_old_sound() -> void:
	var player: Player = _player_with(&"rifle_ar")
	var weapon: Weapon = player.weapons.current
	weapon.instance.ammo_in_mag = 0
	assert_true(weapon.start_reload())
	assert_null(weapon.pose.mech_audio.stream, "no single reload sound for a gun with the motion")
	var heard: Array[AudioStream] = _heard_during_reload(player, weapon._reload_duration + 0.1)
	var cues: Dictionary[StringName, AudioStream] = WeaponPose.CUES
	assert_eq(heard, [cues[&"mag_out"], cues[&"mag_in"], cues[&"bolt"]] as Array[AudioStream])
	assert_false(weapon.is_reloading())


func test_brenner_plays_a_shell_sound_per_round_and_racks_once_from_empty() -> void:
	var player: Player = _player_with(&"brenner_trench")
	var weapon: Weapon = player.weapons.current
	weapon.instance.ammo_in_mag = 0
	weapon.instance.ammo_reserve = 2
	assert_true(weapon.start_reload())
	var heard: Array[AudioStream] = _heard_during_reload(player, 3.0)
	var cues: Dictionary[StringName, AudioStream] = WeaponPose.CUES
	assert_false(weapon.is_reloading())
	assert_eq(heard, [cues[&"shell_in"], cues[&"pump"], cues[&"shell_in"]] as Array[AudioStream])


func test_cancelled_reload_plays_no_later_moves() -> void:
	var player: Player = _player_with(&"kestrel_smg")
	var weapon: Weapon = player.weapons.current
	weapon.instance.ammo_in_mag = 3
	assert_true(weapon.start_reload())
	var heard: Array[AudioStream] = _heard_during_reload(player, weapon._reload_duration * 0.3)
	assert_eq(heard, [WeaponPose.CUES[&"mag_out"]] as Array[AudioStream])
	RoundReload.cancel(weapon)
	assert_eq(_heard_during_reload(player, 1.0), heard, "nothing new after the cancel")


func test_sprint_cancel_eases_the_hand_back_to_its_grip() -> void:
	var player: Player = _player_with(&"rifle_ar")
	var weapon: Weapon = player.weapons.current
	var view: PlayerArmView = player.weapons.arm_view
	var hand: int = view.skeleton.find_bone("hand_L")
	weapon.instance.ammo_in_mag = 3
	assert_true(weapon.start_reload())
	weapon._reload_timer = weapon._reload_duration * 0.6
	weapon.pose.update(1.0)
	view.update_pose()
	assert_gt(weapon.pose.reload_relax(), 0.9, "hand on the magazine mid-reload")
	RoundReload.cancel(weapon)
	var last: Vector3 = weapon.transform.affine_inverse() * view.skeleton.get_bone_global_pose(hand).origin
	var start_gap: float = last.distance_to(view.profile.left.wrist)
	for i: int in 30:
		weapon.pose.update(1.0 / 60.0)
		view.update_pose()
		var now: Vector3 = weapon.transform.affine_inverse() * view.skeleton.get_bone_global_pose(hand).origin
		assert_lt(now.distance_to(last), start_gap * 0.4, "eases, no pop, at frame %d" % i)
		last = now
	assert_almost_eq(last, view.profile.left.wrist, Vector3.ONE * 0.005, "back on the grip after half a second")


func test_viewmodel_kick_survives_a_slow_frame_and_matches_faster_frames() -> void:
	var slow: Weapon = _player_with(&"kestrel_smg").weapons.current
	var fast: Weapon = _player_with(&"kestrel_smg").weapons.current
	for gun: Weapon in [slow, fast]:
		gun.pose.update(1.0)
		gun.pose.on_fired()
	slow.pose.update(1.0 / 24.0)
	for i: int in 5:
		fast.pose.update(1.0 / 120.0)
	assert_gt(slow.position.z - slow.data.hip_position.z, 0.002, "a short kick is visible at 24 fps")
	assert_almost_eq(slow.position, fast.position, Vector3.ONE * 0.0001, "same pose at the same shot age")
	slow.pose.update(0.5)
	assert_almost_eq(slow.position, slow.data.hip_position, Vector3.ONE * 0.0001)


func test_reload_has_a_body_arc_while_the_support_hand_is_away() -> void:
	for id: StringName in [&"synapse", &"coachman_2b"]:
		var gun: Weapon = _player_with(id).weapons.current
		gun.instance.ammo_in_mag = 1
		assert_true(gun.start_reload())
		gun._reload_timer = gun._reload_duration * 0.75
		gun.pose.update(1.0)
		var early: float = gun.rotation.y
		gun._reload_timer = gun._reload_duration * 0.5
		gun.pose.update(1.0)
		assert_gt(absf(gun.rotation.y - early), 0.012, "%s continues to turn through the reload" % id)
		gun.tick(gun._reload_duration)
		gun.pose.update(1.0)
		assert_almost_eq(gun.position, gun.data.hip_position, Vector3.ONE * 0.0001)
		assert_almost_eq(gun.rotation, Vector3.ZERO, Vector3.ONE * 0.0001)


func test_coachman_keeps_the_receiver_in_frame_during_the_reload() -> void:
	var gun: Weapon = _player_with(&"coachman_2b").weapons.current
	var receiver: MeshInstance3D = gun.find_child("Receiver", true, false) as MeshInstance3D
	gun.instance.ammo_in_mag = 1
	assert_true(gun.start_reload())
	for fraction: float in [0.3, 0.5, 0.7]:
		gun._reload_timer = gun._reload_duration * (1.0 - fraction)
		gun.pose.update(1.0)
		var center: Vector3 = receiver.to_global(receiver.get_aabb().get_center())
		assert_true(gun.camera.is_position_in_frustum(center), "receiver visible at %.0f%%" % (fraction * 100.0))


func test_gaining_quickhands_mid_reload_preserves_the_active_animation_clock() -> void:
	var quickhands: SerumData = load("res://content/serums/quickhands.tres") as SerumData
	for id: StringName in [&"fieldhand_lever", &"brenner_trench"]:
		var player: Player = _player_with(id)
		var gun: Weapon = player.weapons.current
		gun.instance.ammo_in_mag = 0
		assert_true(gun.start_reload())
		var first: float = gun._reload_timer
		var later: float = gun._reload_duration
		gun.tick(first * 0.25)
		gun.pose.update(1.0)
		var before: Transform3D = gun.transform
		player.serums.append(quickhands)
		gun.pose.update(1.0)
		assert_true(before.is_equal_approx(gun.transform), "%s pose holds when a stat changes" % id)
		assert_almost_eq(RoundReload.cycle_t(gun), 0.25, 0.001)
		gun.tick(first * 0.75 + later * 0.5)
		assert_almost_eq(RoundReload.cycle_t(gun), 0.5, 0.001, "later cycles retain the same interval")
		RoundReload.cancel(gun)
		gun.instance.ammo_in_mag = 0
		assert_true(gun.start_reload())
		assert_lt(gun._reload_timer, first, "the next reload picks up Quickhands")
