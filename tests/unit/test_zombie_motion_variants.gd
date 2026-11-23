## Exercise ZombieGait, ZombieStrike and ZombieReactions through the enemy scenes at their gameplay times.
extends GutTest


func _enemy(kind: String) -> Zombie:
	var type: String = "walker" if kind.begins_with("shambler") else kind
	var data: EnemyData = load("res://content/enemies/zombie_%s.tres" % type) as EnemyData
	var zombie: Zombie = data.scene.instantiate() as Zombie
	var id: int = 1
	if type == "walker":
		var look_index: int = 1 if kind == "shambler_guard" else 0
		while posmod(hash(id), 2) != look_index:
			id += 1
	var rng: RandomNumberGenerator = RandomNumberGenerator.new()
	rng.seed = 1
	zombie.setup(data, id, 1.0, 1.0, 1.0, rng)
	add_child_autofree(zombie)
	zombie.set_process(false)
	zombie.set_physics_process(false)
	zombie.visual.position = Vector3.ZERO
	return zombie


func _bone(zombie: Zombie, name_of_bone: StringName) -> Vector3:
	var skeleton: Skeleton3D = zombie.visual.find_children("*", "Skeleton3D", true, false)[0] as Skeleton3D
	return zombie.to_local(skeleton.to_global(skeleton.get_bone_global_pose(skeleton.find_bone(name_of_bone)).origin))


func _strike(zombie: Zombie, windup: float, recovery: float = 0.0) -> void:
	zombie.state = Zombie.State.ATTACKING
	zombie.state_time = zombie.data.attack_windup * windup + Zombie.STRIKE_TIME * recovery
	zombie.visual.follow(zombie, 0.0)


func test_guard_braces_the_left_forearm_at_contact() -> void:
	var guard: Zombie = _enemy("shambler_guard")
	_strike(guard, 0.82)
	var planted: Vector3 = _bone(guard, &"foot_L")
	_strike(guard, 1.0)
	var hand: Vector3 = _bone(guard, &"hand_L")
	var elbow: Vector3 = _bone(guard, &"forearm_L")
	assert_lt(hand.z, -0.75)
	assert_gt(hand.y, elbow.y + 0.12, "the bent forearm leads across the chest")
	assert_lt(elbow.z, _bone(guard, &"hand_R").z - 0.4, "rear hand stays tucked")
	assert_lt(planted.distance_to(_bone(guard, &"foot_L")), 0.005)


func test_bloater_loads_its_weight_and_pushes_both_hands_together() -> void:
	var bloater: Zombie = _enemy("bloater")
	_strike(bloater, 0.0)
	var ready: Vector3 = _bone(bloater, &"pelvis")
	_strike(bloater, 0.82)
	var feet: Array[Vector3] = [_bone(bloater, &"foot_L"), _bone(bloater, &"foot_R")]
	assert_lt(_bone(bloater, &"pelvis").y, ready.y - 0.1)
	_strike(bloater, 1.0)
	var left: Vector3 = _bone(bloater, &"hand_L")
	var right: Vector3 = _bone(bloater, &"hand_R")
	assert_lt(maxf(left.z, right.z), -0.75, "both wrists reach the target on the damage frame")
	assert_lt(absf(left.z - right.z), 0.03)
	assert_between(right.x - left.x, 0.23, 0.55, "palms land shoulder-width apart")
	assert_lt(feet[0].distance_to(_bone(bloater, &"foot_L")), 0.006)
	assert_lt(feet[1].distance_to(_bone(bloater, &"foot_R")), 0.006)


func test_glower_slashes_up_from_a_crouch_and_catches_itself_on_the_right_foot() -> void:
	var glower: Zombie = _enemy("glower")
	_strike(glower, 0.82)
	var low: Vector3 = _bone(glower, &"hand_L")
	var planted: Vector3 = _bone(glower, &"foot_R")
	_strike(glower, 1.0)
	var hit: Vector3 = _bone(glower, &"hand_L")
	assert_gt(hit.y, low.y + 0.3)
	assert_lt(hit.z, -0.65)
	assert_lt(planted.distance_to(_bone(glower, &"foot_R")), 0.005)
	_strike(glower, 1.0, 0.29)
	assert_gt(_bone(glower, &"hand_L").y, hit.y + 0.35, "the claw follows through upwards")


func test_gaits_are_distinct_at_the_same_ground_speed() -> void:
	var lab: Zombie = _enemy("shambler")
	var guard: Zombie = _enemy("shambler_guard")
	var bloater: Zombie = _enemy("bloater")
	var glower: Zombie = _enemy("glower")
	for zombie: Zombie in [lab, guard, bloater, glower]:
		zombie.visual.pose_walk(1.6, 0.5, 0.12)
	assert_lt(guard.visual.get_offset(&"forearm_L").x, lab.visual.get_offset(&"forearm_L").x - 0.4)
	assert_gt(absf(bloater.visual.get_offset(&"Torso").z), 0.07, "Bloater leans onto the planted leg")
	assert_lt(bloater.visual.get_offset(&"Torso").x, lab.visual.get_offset(&"Torso").x - 0.05)
	assert_gt(glower.visual.get_offset(&"Torso").x, lab.visual.get_offset(&"Torso").x + 0.17)
	assert_gt(glower.visual.get_offset(&"shin_L").x, guard.visual.get_offset(&"shin_L").x + 0.25)


func test_vaults_lead_with_different_legs_and_falls_settle_in_different_directions() -> void:
	var guard: Zombie = _enemy("shambler_guard")
	var bloater: Zombie = _enemy("bloater")
	var glower: Zombie = _enemy("glower")
	for zombie: Zombie in [guard, bloater, glower]:
		zombie.visual.pose_vault(0.5)
		assert_almost_eq(zombie.visual.position.y, ZombieRig.VAULT_HEIGHT, 0.001)
	assert_lt(guard.visual.get_offset(&"LegL").x, guard.visual.get_offset(&"LegR").x - 0.4)
	assert_almost_eq(bloater.visual.get_offset(&"LegL").x, bloater.visual.get_offset(&"LegR").x, 0.01)
	assert_gt(glower.visual.get_offset(&"LegL").x, glower.visual.get_offset(&"LegR").x + 0.8)
	for zombie: Zombie in [guard, bloater, glower]:
		zombie.visual.pose_vault(1.0)
		var fall: Tween = zombie.visual.fall_over(false, false)
		fall.pause()
		fall.custom_step(0.46)
	assert_lt(guard.visual.rotation.x, -1.2)
	assert_gt(bloater.visual.rotation.x, 1.4)
	assert_gt(absf(glower.visual.rotation.z), 1.4)
