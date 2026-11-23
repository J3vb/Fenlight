## BodyAnimator picks the clip for each move state from measured movement, crouch and downed,
## and shows the held gun with its fire and reload motions.
extends GutTest

const PLAYER: PackedScene = preload("res://systems/player/player.tscn")

var player: Player
var animator: BodyAnimator


func before_each() -> void:
	player = PLAYER.instantiate() as Player
	animator = player.get_node("Body/BodyAnimator") as BodyAnimator
	animator.headless = false
	add_child_autofree(player)
	player.set_physics_process(false)
	player.camera.current = false


func _move(velocity: Vector3, frames: int = 40) -> void:
	for _frame: int in frames:
		await get_tree().physics_frame
		player.global_position += velocity * get_physics_process_delta_time()


func _ground() -> Vector2:
	return animator.tree.get(BodyAnimator.GROUND_BLEND)


func _state() -> String:
	return animator.tree.get(BodyAnimator.STATE_CURRENT)


func test_standing_still_plays_idle() -> void:
	await _move(Vector3.ZERO, 10)
	assert_eq(_state(), "ground")
	assert_almost_eq(_ground().length(), 0.0, 0.01, "idle sits at the blend origin")


func test_walk_directions_pick_their_clip() -> void:
	var walk: float = player.walk_speed
	var cases: Dictionary[String, Vector3] = {
		"forward": Vector3(0.0, 0.0, -walk),
		"back": Vector3(0.0, 0.0, walk),
		"right": Vector3(walk, 0.0, 0.0),
		"left": Vector3(-walk, 0.0, 0.0),
	}
	var expected: Dictionary[String, Vector2] = {
		"forward": Vector2(0.0, 1.0), "back": Vector2(0.0, -1.0), "right": Vector2(1.0, 0.0), "left": Vector2(-1.0, 0.0)
	}
	for direction: String in cases:
		await _move(cases[direction])
		assert_almost_eq(_ground().distance_to(expected[direction]), 0.0, 0.05, direction + " walk blend point")


func test_moves_are_measured_in_the_body_frame_after_turning() -> void:
	player.rotation.y = PI / 2.0
	await _move(Vector3(-player.walk_speed, 0.0, 0.0))
	assert_almost_eq(_ground().distance_to(Vector2(0.0, 1.0)), 0.0, 0.05, "walking where the body faces is forward")


func test_sprint_speed_reaches_the_run_clip_and_speeds_it_up() -> void:
	await _move(Vector3(0.0, 0.0, -player.sprint_speed))
	assert_almost_eq(_ground().y, player.sprint_speed / player.walk_speed, 0.05, "run blend point")
	assert_gt(animator.tree.get(BodyAnimator.TIME_SCALE), 1.0, "run clip speeds up to match the ground")


func test_crouch_and_crouch_walk() -> void:
	player.is_crouching = true
	await _move(Vector3.ZERO, 10)
	await wait_seconds(BodyAnimator.FADE_TIME)
	assert_eq(_state(), "crouch")
	assert_almost_eq(animator.tree.get(BodyAnimator.CROUCH_BLEND), 0.0, 0.01, "crouch idle")
	await _move(Vector3(0.0, 0.0, -player.walk_speed * player.crouch_speed_multiplier))
	assert_almost_eq(animator.tree.get(BodyAnimator.CROUCH_BLEND), 1.0, 0.05, "crouch walk")


func test_downed_wins_over_crouch_and_crawls_when_moving() -> void:
	player.is_crouching = true
	player.is_downed = true
	await _move(Vector3.ZERO, 10)
	assert_eq(_state(), "downed")
	await _move(Vector3(0.0, 0.0, -player.walk_speed * BodyAnimator.DOWNED_SPEED_SHARE))
	assert_almost_eq(animator.tree.get(BodyAnimator.DOWNED_BLEND), 1.0, 0.05, "downed crawl")
	player.is_downed = false
	player.is_crouching = false
	await _move(Vector3.ZERO, 5)
	assert_eq(_state(), "ground", "standing up again returns to the ground clips")


func test_pose_updates_that_skip_ticks_still_read_as_steady_running() -> void:
	var sprint: float = player.sprint_speed
	for frame: int in 60:
		await get_tree().physics_frame
		if frame % 3 == 0:
			player.global_position += Vector3(0.0, 0.0, -sprint) * get_physics_process_delta_time() * 3.0
	assert_almost_eq(-animator.local_velocity.z, sprint, sprint * 0.1, "a 20 Hz pose stream is still a sprint")


func test_teleport_is_not_read_as_running() -> void:
	player.global_position += Vector3(50.0, 0.0, 0.0)
	await wait_physics_frames(2)
	assert_almost_eq(animator.local_velocity.length(), 0.0, 0.01)


func test_look_pitch_bends_the_head_after_the_clip() -> void:
	await _move(Vector3.ZERO, 5)
	assert_true(animator.aim is AimPitch, "the look pitch modifier sits on the skeleton")
	var skeleton: Skeleton3D = animator.aim.get_skeleton()
	var level: Vector3 = await _head_forward(skeleton)
	player.camera_rig.rotation.x = 0.5
	var looking: Vector3 = await _head_forward(skeleton)
	assert_almost_eq(level.angle_to(looking), 0.5, 0.05, "chest and head together turn by the full pitch")


func _head_forward(skeleton: Skeleton3D) -> Vector3:
	await skeleton.skeleton_updated
	await skeleton.skeleton_updated
	return skeleton.get_bone_global_pose(skeleton.find_bone("head")).basis.z


func test_headless_builds_no_tree() -> void:
	var other: Player = PLAYER.instantiate() as Player
	var headless: BodyAnimator = other.get_node("Body/BodyAnimator") as BodyAnimator
	headless.headless = true
	add_child_autofree(other)
	headless.set_physics_process(false)
	headless.held_weapon = &"rifle_ar"
	headless._physics_process(0.016)
	assert_null(headless.tree, "a dedicated server poses nothing")
	assert_null(headless.gun, "and holds no gun model")


func test_owner_publishes_its_current_gun_and_holds_it_as_a_shadow() -> void:
	var weapon: Weapon = player.weapons.give(Content.weapon(&"rifle_ar"))
	await wait_physics_frames(2)
	assert_eq(animator.held_weapon, &"rifle_ar")
	assert_eq(animator.reload_time, 0.0)
	assert_eq((animator.gun.get_parent() as BoneAttachment3D).bone_name, "hand_R")
	assert_not_null(animator.gun.find_child("Muzzle"), "the world model is the bare gun")
	var mesh: GeometryInstance3D = animator.gun.find_children("*", "GeometryInstance3D", true, false)[0]
	assert_eq(mesh.cast_shadow, GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY, "owner sees only its shadow")
	weapon.instance.ammo_in_mag = 0
	assert_true(weapon.start_reload())
	await wait_physics_frames(2)
	var empty_reload: float = Content.weapon(&"rifle_ar").empty_reload_time
	assert_almost_eq(animator.reload_time, empty_reload, 0.001, "the owner publishes the real (empty) reload time")


func test_owner_publishes_the_whole_per_round_reload() -> void:
	var data: WeaponData = Content.weapon(&"fieldhand_lever")
	var weapon: Weapon = player.weapons.give(data)
	weapon.instance.ammo_in_mag = 0
	assert_true(weapon.start_reload())
	await wait_physics_frames(2)
	var rounds: int = mini(data.magazine_size, weapon.instance.ammo_reserve)
	assert_almost_eq(animator.reload_time, data.per_round_time * rounds, 0.001, "every missing round, not one")


func test_teammate_swaps_the_held_gun_when_the_synced_id_changes() -> void:
	animator.is_owner = false
	animator.held_weapon = &"rifle_ar"
	await wait_physics_frames(2)
	var rifle: Node3D = animator.gun
	var mesh: GeometryInstance3D = rifle.find_children("*", "GeometryInstance3D", true, false)[0]
	assert_eq(mesh.cast_shadow, GeometryInstance3D.SHADOW_CASTING_SETTING_ON, "teammates see the gun")
	animator.held_weapon = &"kestrel_smg"
	await wait_physics_frames(2)
	assert_false(is_instance_valid(rifle), "the old gun is gone")
	assert_eq(animator.gun.scene_file_path, Content.weapon(&"kestrel_smg").world_model.resource_path)
	animator.held_weapon = &""
	await wait_physics_frames(2)
	assert_null(animator.gun, "empty hands hold nothing")


func test_fire_kicks_only_the_upper_body() -> void:
	await _move(Vector3.ZERO, 3)
	animator.fire()
	await wait_physics_frames(2)
	assert_true(animator.tree.get(&"parameters/fire/active"), "the fire one-shot plays")
	var shot: AnimationNodeOneShot = (animator.tree.tree_root as AnimationNodeBlendTree).get_node(&"fire")
	var clip: Animation = animator.tree.get_animation(&"fire")
	var arm: NodePath = NodePath()
	var leg: NodePath = NodePath()
	for index: int in clip.get_track_count():
		var bone: String = clip.track_get_path(index).get_concatenated_subnames()
		if bone == "forearm_R":
			arm = clip.track_get_path(index)
		elif bone == "thigh_L":
			leg = clip.track_get_path(index)
	assert_true(shot.is_path_filtered(arm), "arms take the kick")
	assert_false(shot.is_path_filtered(leg), "legs keep walking")


func test_reload_stretches_to_the_synced_reload_time_and_fades_out_when_it_ends() -> void:
	animator.is_owner = false
	animator.held_weapon = &"rifle_ar"
	animator.reload_time = 2.8
	await wait_physics_frames(2)
	var length: float = animator.tree.get_animation(&"reload").length
	var expected: float = length / 2.8
	assert_almost_eq(animator.tree.get(BodyAnimator.RELOAD_SCALE) as float, expected, 0.001)
	assert_true(animator.tree.get(&"parameters/reload/active"))
	animator.reload_time = 0.0
	await wait_seconds(0.4)
	assert_false(animator.tree.get(&"parameters/reload/active"), "a finished reload fades out")


func test_hold_transform_puts_the_grip_point_on_the_palm() -> void:
	var grip: GripData = Content.weapon(&"kestrel_smg").grip
	var anchor: Vector3 = Vector3(grip.right_anchor.x, grip.right_anchor.z, -grip.right_anchor.y)
	var palm: Vector3 = BodyAnimator.hold_transform(grip) * anchor
	assert_almost_eq(palm.distance_to(BodyAnimator.PALM), 0.0, 0.0001)
	var barrel: Vector3 = BodyAnimator.hold_transform(grip).basis * Vector3.FORWARD
	assert_almost_eq(barrel.distance_to(Vector3.UP), 0.0, 0.0001, "the barrel runs along the hand bone")


func test_teammate_reload_clip_counts_the_long_first_cycle_only_once() -> void:
	var gun: Weapon = player.weapons.give(Content.weapon(&"brenner_trench"))
	gun.instance.ammo_in_mag = 0
	gun.instance.ammo_reserve = 3
	assert_true(gun.start_reload())
	await wait_physics_frames(2)
	var first: float = gun.data.empty_reload_time
	var rest: float = gun.data.per_round_time
	assert_almost_eq(animator.reload_time, first + 2.0 * rest, 0.001)
	gun.tick(first + 2.0 * rest + 0.01)
	await wait_physics_frames(2)
	assert_eq(animator.reload_time, 0.0)
