## Zombie models in game: each enemy type loads its Tripo model (Shamblers in two looks), the head
## hit zone rides on the head bone, and code-driven poses move the skeleton.
extends GutTest

const WALKER: String = "res://content/enemies/zombie_walker.tres"
const BLOATER: String = "res://content/enemies/zombie_bloater.tres"
const GLOWER: String = "res://content/enemies/zombie_glower.tres"


func _spawn(path: String) -> Zombie:
	var data: EnemyData = load(path) as EnemyData
	var zombie: Zombie = data.scene.instantiate() as Zombie
	zombie.setup(data, 1, 1.0, 1.0, 1.0, RandomNumberGenerator.new())
	add_child_autofree(zombie)
	return zombie


func test_walker_uses_shambler_model_with_all_limbs() -> void:
	var zombie: Zombie = _spawn(WALKER)
	for part: StringName in ZombieRig.PARTS:
		assert_true(zombie.visual.has_part(part), "walker model has " + part)
	assert_eq(_skeleton(zombie.visual).get_bone_count(), 22, "walker shares the character skeleton")


func test_head_zone_follows_the_head_bone_when_it_turns() -> void:
	var zombie: Zombie = _spawn(WALKER)
	zombie.set_process(false)
	zombie.set_physics_process(false)
	assert_eq(zombie.head_zone.get_parent(), zombie.visual.head, "head zone is on the model's head center")
	var anchor: BoneAttachment3D = zombie.visual.head.get_parent() as BoneAttachment3D
	assert_not_null(anchor, "head center rides a BoneAttachment3D")
	assert_eq(anchor.bone_name, &"head")
	assert_eq(zombie.head_zone.zone, DamageInfo.Zone.HEAD)
	zombie.visual.position = Vector3.ZERO
	var height: float = zombie.head_zone.global_position.y - zombie.global_position.y
	assert_between(height, 1.55, 1.9, "head zone sits at head height")
	var forward: float = (zombie.head_zone.global_position - zombie.global_position).dot(-zombie.global_basis.z)
	assert_gt(forward, 0.0, "model faces the zombie's forward (-Z)")
	var skeleton: Skeleton3D = _skeleton(zombie.visual)
	var bone: int = skeleton.find_bone("head")
	var before: Transform3D = zombie.head_zone.global_transform
	var rotation: Quaternion = skeleton.get_bone_pose_rotation(bone)
	skeleton.set_bone_pose_rotation(bone, rotation * Quaternion(Vector3.UP, 0.7))
	skeleton.force_update_all_bone_transforms()
	await wait_process_frames(1)
	var expected: Transform3D = skeleton.global_transform * skeleton.get_bone_global_pose(bone)
	expected = expected * zombie.visual.head.transform * zombie.head_zone.transform
	assert_almost_eq(zombie.head_zone.global_position.distance_to(expected.origin), 0.0, 0.001)
	assert_false(zombie.head_zone.global_basis.is_equal_approx(before.basis), "head zone turns with the head bone")
	assert_gt(zombie.head_zone.global_position.distance_to(before.origin), 0.01, "head center follows the turn")


func test_glower_tripo_model_has_every_posed_bone_and_a_head_zone() -> void:
	var zombie: Zombie = _spawn(GLOWER)
	zombie.set_physics_process(false)
	for part: StringName in ZombieRig.PARTS:
		assert_true(zombie.visual.has_part(part), "Glower model has " + part)
	assert_eq(_skeleton(zombie.visual).get_bone_count(), 22, "Glower shares the character skeleton")
	assert_eq(zombie.head_zone.get_parent(), zombie.visual.head, "head zone is on the Glower's head center")
	zombie.visual.position = Vector3.ZERO
	var height: float = zombie.head_zone.global_position.y - zombie.global_position.y
	assert_between(height, 1.4, 1.75, "head zone sits at the 1.7 m Glower's head height")
	var forward: float = (zombie.head_zone.global_position - zombie.global_position).dot(-zombie.global_basis.z)
	assert_gt(forward, 0.0, "Glower faces the zombie's forward (-Z)")
	var mesh: MeshInstance3D = zombie.visual.find_child("Body", true, false) as MeshInstance3D
	var glow: ShaderMaterial = mesh.mesh.surface_get_material(0) as ShaderMaterial
	assert_not_null(glow, "import gives the Glower its vein-glow material")
	assert_eq(glow.shader.resource_path, "res://assets/materials/glower_veins.gdshader")
	var maps: Dictionary[StringName, String] = {&"albedo_tex": "_albedo", &"normal_tex": "_normal", &"orm_tex": "_orm"}
	for slot: StringName in maps:
		var map: Texture2D = glow.get_shader_parameter(slot) as Texture2D
		assert_not_null(map, "glow reads the baked map in " + slot)
		if map:
			assert_string_contains(map.resource_path, maps[slot], slot + " gets the right baked map")


func test_walk_swings_legs_in_opposite_directions() -> void:
	var zombie: Zombie = _spawn(WALKER)
	var rig: ZombieRig = zombie.visual
	var left: Array[float] = []
	var right: Array[float] = []
	for i: int in 20:
		rig.pose_walk(2.0, 0.0, 0.05)
		left.append(_bone_offset(rig, "thigh_L").x)
		right.append(_bone_offset(rig, "thigh_R").x)
		assert_almost_eq(rig.get_offset(&"LegL").x, left[-1], 0.001, "legacy offset reads the thigh pose")
	assert_gt(left.max(), 0.3, "left leg swings forward and back")
	assert_lt(left.min(), -0.3)
	for i: int in left.size():
		assert_almost_eq(left[i], -right[i], 0.001, "legs move opposite")


func test_reach_lifts_the_arms() -> void:
	var zombie: Zombie = _spawn(WALKER)
	var rig: ZombieRig = zombie.visual
	rig.pose_walk(0.0, 0.0, 0.0)
	var relaxed: float = rig.get_offset(&"ArmL").x
	rig.pose_walk(0.0, 1.0, 0.0)
	assert_lt(rig.get_offset(&"ArmL").x, relaxed - 0.3, "close target: arms come up")


func test_upright_walk_keeps_the_wrists_near_shoulder_width() -> void:
	for kind: String in ["shambler", "shambler_guard", "bloater", "glower"]:
		var rig: ZombieRig = ZombieRig.new()
		rig.model = load("res://assets/models/zombies/%s.glb" % kind) as PackedScene
		add_child_autofree(rig)
		var widest: float = 0.0
		# Include the spawn pose, visible before the first walk update.
		for frame: int in range(-1, 24):
			if frame >= 0:
				rig.pose_walk(1.6, frame / 30.0, 1.0 / 24.0)
			var wrists: float = absf(_bone_position(rig, "hand_L").x - _bone_position(rig, "hand_R").x)
			var shoulders: float = absf(_bone_position(rig, "upperarm_L").x - _bone_position(rig, "upperarm_R").x)
			widest = maxf(widest, wrists - shoulders)
		assert_lt(widest, 0.45, kind + " carries the elbows in throughout the stride")


func test_shambler_rakes_forward_at_damage_time_and_recovers() -> void:
	var rig: ZombieRig = ZombieRig.new()
	rig.model = load("res://assets/models/zombies/shambler.glb") as PackedScene
	add_child_autofree(rig)
	rig.pose_attack(0.0)
	var ready: Vector3 = _bone_position(rig, "hand_R")
	rig.pose_attack(ZombieRig.ATTACK_DRAW)
	var drawn: Vector3 = _bone_position(rig, "hand_R")
	assert_gt(drawn.y, ready.y + 0.12, "raises the striking hand before the swipe")
	var elbow: float = rig.get_offset(&"forearm_R").x
	rig.pose_attack(1.0)
	var contact: Vector3 = _bone_position(rig, "hand_R")
	var skeleton: Skeleton3D = _skeleton(rig)
	var hand: int = skeleton.find_bone("hand_R")
	var turn: Basis = skeleton.get_bone_global_pose(hand).basis * skeleton.get_bone_global_rest(hand).basis.inverse()
	assert_lt(turn.z.y, -0.5, "turns the forward-facing rest palm down at contact")
	assert_lt(contact.z, drawn.z - 0.25, "drives the wrist forward by the hit frame")
	assert_lt(contact.z, _bone_position(rig, "hand_L").z - 0.15, "leads with one hand")
	assert_gt(rig.get_offset(&"forearm_R").x, elbow + 0.5, "extends the bent elbow")
	rig.pose_attack(1.34)
	var swept: Vector3 = _bone_position(rig, "hand_R")
	assert_lt(swept.x, contact.x - 0.05, "rakes across the target after contact")
	assert_lt(swept.y, contact.y - 0.04, "follows through below the hit")
	rig.pose_attack(2.0)
	assert_almost_eq(_bone_position(rig, "hand_R").distance_to(ready), 0.0, 0.001, "recovers")


func _bone_position(rig: ZombieRig, bone: String) -> Vector3:
	var skeleton: Skeleton3D = _skeleton(rig)
	return skeleton.to_global(skeleton.get_bone_global_pose(skeleton.find_bone(bone)).origin)


func test_death_disables_hit_zones_and_goes_limp() -> void:
	var zombie: Zombie = _spawn(WALKER)
	zombie.health.take_damage(DamageInfo.create(99999.0, null))
	assert_eq(zombie.state, Zombie.State.DEAD)
	assert_eq(zombie.head_zone.collision_layer, 0, "head zone off when dead")
	await wait_seconds(0.5)
	assert_gt(zombie.visual.get_offset(&"ArmL").x, 0.5, "arms fall slack")
	assert_lt(zombie.visual.rotation.x, -1.0, "body tipped over")
	assert_false(zombie.voice.is_processing(), "dead zombies stop groaning")


func test_walk_cycle_steps_twice_per_cycle() -> void:
	var zombie: Zombie = _spawn(WALKER)
	zombie.set_process(false)
	var rig: ZombieRig = zombie.visual
	var steps: Array[int] = [0]
	rig.stepped.connect(func() -> void: steps[0] += 1)
	var speed: float = 2.0
	var cycle: float = TAU / (1.5 + speed * 2.5)
	for i: int in 300:
		rig.pose_walk(speed, 0.0, cycle * 3.0 / 300.0)
	assert_between(steps[0], 5, 7, "two footsteps per walk cycle")
	steps[0] = 0
	for i: int in 300:
		rig.pose_walk(0.1, 0.0, 0.01)
	assert_eq(steps[0], 0, "no footsteps while shuffling on the spot")


func test_dying_zombie_says_a_death_sound_once() -> void:
	var zombie: Zombie = _spawn(WALKER)
	await wait_process_frames(1)
	zombie.health.take_damage(DamageInfo.create(99999.0, null))
	await wait_process_frames(2)
	assert_true(zombie.voice.stream in zombie.data.death_sounds, "death sound plays")
	zombie.voice.stream = null
	zombie.voice.show_state(Zombie.State.DEAD)
	assert_null(zombie.voice.stream, "the death plays only once")


func test_voice_waiting_for_sync_stays_silent_for_an_old_corpse() -> void:
	var zombie: Zombie = _spawn(WALKER)
	zombie.voice.waiting_for_sync = true
	zombie.voice.show_state(Zombie.State.DEAD)
	assert_null(zombie.voice.stream, "nothing plays before the first sync")
	zombie.voice.start_state(Zombie.State.DEAD)
	zombie.voice.show_state(Zombie.State.DEAD)
	assert_null(zombie.voice.stream, "a corpse already down at the first sync stays silent")
	assert_false(zombie.voice.is_processing(), "and does not groan")
	var live: Zombie = _spawn(WALKER)
	live.voice.waiting_for_sync = true
	live.voice.start_state(Zombie.State.CHASING)
	live.voice.show_state(Zombie.State.DEAD)
	assert_true(live.voice.stream in live.data.death_sounds, "a death after the first sync is heard")


func test_rising_zombie_climbs_out_of_the_floor() -> void:
	var zombie: Zombie = _spawn(WALKER)
	zombie.state_time = 0.0
	zombie.visual.follow(zombie, 0.0)
	assert_almost_eq(zombie.visual.position.y, -1.8, 0.01, "starts under the floor")
	zombie.state_time = Zombie.SPAWN_TIME
	zombie.visual.follow(zombie, 0.0)
	assert_almost_eq(zombie.visual.position.y, 0.0, 0.01, "standing at the end of the rise")


func test_voice_gets_the_enemy_groans() -> void:
	var zombie: Zombie = _spawn(WALKER)
	assert_eq(zombie.voice.groans, zombie.data.groan_sounds)
	assert_eq(zombie.voice.deaths, zombie.data.death_sounds)
	assert_eq(zombie.voice.footsteps, zombie.data.footstep_sounds)


func test_bloater_has_its_own_model_and_wider_body() -> void:
	var zombie: Zombie = _spawn(BLOATER)
	assert_eq(zombie.head_zone.get_parent(), zombie.visual.head, "bloater head zone on its head")
	var body: CollisionShape3D = zombie.get_node("HitZones/Body/Shape") as CollisionShape3D
	var mesh: MeshInstance3D = zombie.visual.find_child("Body", true, false) as MeshInstance3D
	assert_gt((body.shape as BoxShape3D).size.x, 0.9, "body zone covers the 0.84 m wide belly")
	var veins: ShaderMaterial = mesh.mesh.surface_get_material(0) as ShaderMaterial
	assert_eq(veins.shader.resource_path, "res://assets/materials/glower_veins.gdshader", "pods glow")


func test_moving_limbs_skip_lightmap_probes() -> void:
	for path: String in [WALKER, BLOATER]:
		var zombie: Zombie = _spawn(path)
		var meshes: Array[Node] = zombie.visual.find_children("*", "GeometryInstance3D", true, false)
		assert_gt(meshes.size(), 0, "%s has meshes" % path)
		for mesh: Node in meshes:
			var gi: int = (mesh as GeometryInstance3D).gi_mode
			assert_eq(gi, GeometryInstance3D.GI_MODE_DISABLED, "%s: no per-frame probe capture" % mesh.name)


func test_vault_pose_hops_and_reaches_forward() -> void:
	var zombie: Zombie = _spawn(WALKER)
	var rig: ZombieRig = zombie.visual
	rig.pose_vault(0.0)
	assert_almost_eq(rig.position.y, 0.0, 0.001, "starts on the ground")
	assert_lt(rig.get_offset(&"ArmL").x, -1.0, "hands reach for the sill")
	rig.pose_vault(0.5)
	assert_almost_eq(rig.position.y, ZombieRig.VAULT_HEIGHT, 0.001, "top of the hop")
	assert_gt(rig.get_offset(&"Torso").x, 0.4, "body pitches forward over the sill")
	assert_lt(rig.get_offset(&"LegL").x, -0.5, "legs tuck")
	rig.pose_vault(1.0)
	assert_almost_eq(rig.position.y, 0.0, 0.001, "lands")
	assert_eq(zombie.entry.vault_progress(), -1.0, "not vaulting outside a window")


func test_walk_and_vault_bend_the_new_elbows_and_knees() -> void:
	var rig: ZombieRig = _spawn(WALKER).visual
	rig.pose_walk(2.0, 0.0, 0.15)
	# A forearm can roll about its length. Measure the bend using the elbow-to-wrist direction.
	var skeleton: Skeleton3D = _skeleton(rig)
	var forearm: int = skeleton.find_bone("forearm_L")
	var axis: Vector3 = skeleton.get_bone_global_rest(forearm).basis.y.normalized()
	var bent: Vector3 = Basis.from_euler(_bone_offset(rig, "forearm_L")) * axis
	assert_gt(bent.z, axis.z + 0.20, "the leading forearm bends forward at the elbow")
	assert_gt(_bone_offset(rig, "shin_L").x, 0.1, "forward knee bends")
	rig.pose_vault(0.5)
	assert_gt(_bone_offset(rig, "shin_L").x, 0.7, "vault tucks the knees")
	assert_lt(_bone_offset(rig, "forearm_R").x, -0.3, "vault bends the elbows")


func test_crawler_keeps_the_skeleton_without_exposing_missing_legs() -> void:
	var rig: ZombieRig = ZombieRig.new()
	rig.model = load("res://assets/models/zombies/crawler.glb") as PackedScene
	add_child_autofree(rig)
	assert_eq(_skeleton(rig).get_bone_count(), 22)
	assert_true(rig.has_part(&"Head"))
	assert_false(rig.has_part(&"LegL"), "crawler has no visible legs")
	assert_false(rig.has_part(&"LegR"))
	rig.pose_walk(1.0, 1.0, 0.1)
	rig.pose_attack(1.0)
	rig.pose_vault(0.5)
	assert_eq(rig.get_offset(&"LegL"), Vector3.ZERO, "missing part retains the caller contract")
	assert_eq(rig.get_offset(&"Unknown"), Vector3.ZERO)


func _skeleton(rig: ZombieRig) -> Skeleton3D:
	return rig.find_children("*", "Skeleton3D", true, false)[0] as Skeleton3D


func _bone_offset(rig: ZombieRig, bone_name: String) -> Vector3:
	var skeleton: Skeleton3D = _skeleton(rig)
	var bone: int = skeleton.find_bone(bone_name)
	var rest: Quaternion = skeleton.get_bone_rest(bone).basis.get_rotation_quaternion()
	var axes: Quaternion = skeleton.get_bone_global_rest(bone).basis.get_rotation_quaternion()
	return (axes * rest.inverse() * skeleton.get_bone_pose_rotation(bone) * axes.inverse()).get_euler()


func test_death_unwinds_the_striking_hand_and_forearm_from_contact() -> void:
	var rig: ZombieRig = _spawn(WALKER).visual
	rig.pose_attack(1.0)
	var skeleton: Skeleton3D = _skeleton(rig)
	var hand: int = skeleton.find_bone("hand_R")
	var forearm: int = skeleton.find_bone("forearm_R")
	var hand_start: Quaternion = skeleton.get_bone_pose_rotation(hand)
	var forearm_start: Quaternion = skeleton.get_bone_pose_rotation(forearm)
	var settling: Tween = rig.pose_dead()
	settling.pause()
	settling.custom_step(0.01)
	assert_lt(hand_start.angle_to(skeleton.get_bone_pose_rotation(hand)), 0.1, "wrist eases out of the strike")
	assert_lt(forearm_start.angle_to(skeleton.get_bone_pose_rotation(forearm)), 0.15, "forearm keeps its roll")
	settling.custom_step(0.4)
	assert_almost_eq(_bone_offset(rig, "hand_R"), Vector3.ZERO, Vector3.ONE * 0.001, "hand relaxes")
	assert_almost_eq(_bone_offset(rig, "forearm_R"), Vector3(-0.15, 0, 0), Vector3.ONE * 0.001, "elbow relaxes")
