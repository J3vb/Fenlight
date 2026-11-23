## Exercise the lab-coat attack through the walker scene, its look selection and its gameplay clock.
extends GutTest


func _walker(look_index: int) -> Zombie:
	var data: EnemyData = load("res://content/enemies/zombie_walker.tres") as EnemyData
	var zombie: Zombie = data.scene.instantiate() as Zombie
	var id: int = 1
	while posmod(hash(id), 2) != look_index:
		id += 1
	zombie.setup(data, id, 1.0, 1.0, 1.0, RandomNumberGenerator.new())
	add_child_autofree(zombie)
	zombie.set_process(false)
	zombie.set_physics_process(false)
	zombie.visual.position = Vector3.ZERO
	return zombie


func _skeleton(zombie: Zombie) -> Skeleton3D:
	return zombie.visual.find_children("*", "Skeleton3D", true, false)[0] as Skeleton3D


func test_walker_look_selects_its_strike_and_the_lab_hits_on_time() -> void:
	var lab: Zombie = _walker(0)
	var guard: Zombie = _walker(1)
	assert_eq(lab.visual.find_children("*", "AnimationPlayer", true, false).size(), 1)
	var lab_player: AnimationPlayer = lab.visual.find_children("*", "AnimationPlayer", true, false)[0]
	var guard_player: AnimationPlayer = guard.visual.find_children("*", "AnimationPlayer", true, false)[0]
	assert_eq(lab_player.get_animation(&"strike"), ZombieStrike.CLIPS[&"shambler"])
	assert_eq(guard_player.get_animation(&"strike"), ZombieStrike.CLIPS[&"shambler_guard"])
	var skeleton: Skeleton3D = _skeleton(lab)
	var body: MeshInstance3D = skeleton.get_node("Body") as MeshInstance3D
	var fingers: int = body.find_blend_shape_by_name("ReachFingers")
	var foot: int = skeleton.find_bone("foot_L")
	var wrist: int = skeleton.find_bone("hand_R")
	lab.state = Zombie.State.ATTACKING
	lab.state_time = 0.80 * lab.data.attack_windup
	lab.visual.follow(lab, 0.0)
	var planted: Vector3 = skeleton.get_bone_global_pose(foot).origin
	lab.state_time = lab.data.attack_windup
	lab.visual.follow(lab, 0.0)
	var contact: Vector3 = skeleton.to_global(skeleton.get_bone_global_pose(wrist).origin)
	var clip: Animation = ZombieStrike.CLIPS[&"shambler"]
	var pelvis_track: int = clip.find_track(^"Skeleton3D:pelvis", Animation.TYPE_POSITION_3D)
	var pelvis: int = skeleton.find_bone("pelvis")
	var authored_hit: Vector3 = clip.position_track_interpolate(pelvis_track, ZombieStrike.CONTACT_TIME)
	assert_almost_eq(skeleton.get_bone_pose_position(pelvis), authored_hit, Vector3.ONE * 0.001, "hit is in sync")
	assert_lt(contact.z, -0.70, "the wrist drives forward to the contact pose")
	assert_gt(body.get_blend_shape_value(fingers), 0.5, "fingers open during the reach")
	assert_lt(skeleton.get_bone_global_pose(foot).origin.distance_to(planted), 0.003, "lead foot stays planted")
	lab.state_time += Zombie.STRIKE_TIME * 0.20
	lab.visual.follow(lab, 0.0)
	assert_lt(body.get_blend_shape_value(fingers), 0.5, "fingers curl through the rake")


func test_interrupting_the_clip_blends_from_the_hit_into_walking() -> void:
	var lab: Zombie = _walker(0)
	var skeleton: Skeleton3D = _skeleton(lab)
	var body: MeshInstance3D = skeleton.get_node("Body") as MeshInstance3D
	var fingers: int = body.find_blend_shape_by_name("ReachFingers")
	var clavicle: int = skeleton.find_bone("clavicle_R")
	lab.state = Zombie.State.ATTACKING
	lab.state_time = lab.data.attack_windup
	lab.visual.follow(lab, 0.0)
	var struck: Quaternion = skeleton.get_bone_pose_rotation(clavicle)
	var rest: Quaternion = skeleton.get_bone_rest(clavicle).basis.get_rotation_quaternion()
	assert_gt(struck.angle_to(rest), 0.05, "clip drives the shoulder")
	lab.state = Zombie.State.CHASING
	lab.visual.follow(lab, 0.01)
	assert_lt(skeleton.get_bone_pose_rotation(clavicle).angle_to(struck), 0.03, "walk begins at the interrupted pose")
	lab.visual.follow(lab, 0.10)
	assert_lt(skeleton.get_bone_pose_rotation(clavicle).angle_to(rest), 0.001, "walk releases the clip-only shoulder")
	assert_almost_eq(body.get_blend_shape_value(fingers), 0.0, 0.001, "walk releases the hand shape")


func test_vault_after_partial_strike_releases_the_lunge() -> void:
	var lab: Zombie = _walker(0)
	var skeleton: Skeleton3D = _skeleton(lab)
	var pelvis: int = skeleton.find_bone("pelvis")
	var body: MeshInstance3D = skeleton.get_node("Body") as MeshInstance3D
	lab.visual.pose_attack(1.15)
	lab.visual.pose_vault(0.4, 0.1)
	assert_almost_eq(
		skeleton.get_bone_pose_position(pelvis), skeleton.get_bone_rest(pelvis).origin, Vector3.ONE * 0.001
	)
	assert_almost_eq(body.get_blend_shape_value(body.find_blend_shape_by_name("ReachFingers")), 0.0, 0.001)


func test_dying_during_contact_relaxes_the_authored_pelvis_and_fingers() -> void:
	var lab: Zombie = _walker(0)
	var skeleton: Skeleton3D = _skeleton(lab)
	var pelvis: int = skeleton.find_bone("pelvis")
	var body: MeshInstance3D = skeleton.get_node("Body") as MeshInstance3D
	lab.visual.pose_attack(1.0)
	var contact: Vector3 = skeleton.get_bone_pose_position(pelvis)
	var settling: Tween = lab.visual.pose_dead()
	settling.pause()
	settling.custom_step(0.01)
	assert_lt(skeleton.get_bone_pose_position(pelvis).distance_to(contact), 0.02, "weight shift settles smoothly")
	settling.custom_step(0.4)
	var rest: Transform3D = skeleton.get_bone_rest(pelvis)
	assert_almost_eq(skeleton.get_bone_pose_position(pelvis), rest.origin, Vector3.ONE * 0.001)
	assert_lt(skeleton.get_bone_pose_rotation(pelvis).angle_to(rest.basis.get_rotation_quaternion()), 0.001)
	assert_almost_eq(body.get_blend_shape_value(body.find_blend_shape_by_name("ReachFingers")), 0.0, 0.001)
