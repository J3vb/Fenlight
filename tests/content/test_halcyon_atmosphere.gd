## Halcyon Labs atmosphere (plan docs/plans/halcyon-labs-atmosphere.md): dead and
## flickering ceiling lights come from layout.json light_states and are saved into
## the blockout (dead ones have no light, so the editor bake sees them dark), and
## every light in atmosphere.tscn is a cheap cosmetic light: unshadowed, never baked, at most a few per room.
extends GutTest

const BLOCKOUT: String = "res://levels/halcyon_labs/blockout.tscn"
const ATMOSPHERE: String = "res://levels/halcyon_labs/atmosphere.tscn"
const BUILDER: String = "res://tools/blockout_builder.gd"
const DEAD_LIGHT: String = "res://levels/kit/ceiling_light_dead.tscn"
const MAP: String = "res://levels/halcyon_labs/map.tscn"
const SCREEN_SHADER: String = "res://systems/effects/monitor_screen.gdshader"
const SOUND_SCRIPT: String = "res://tools/assets/ambience_sfx.py"
const MAX_SOUND_DISTANCE: float = 14.0
const STORY_TEXTURES: String = "res://assets/textures/story/"
const LEAK: String = "res://assets/textures/story/leak_pool.png"
const MAX_LIGHTS_PER_ROOM: int = 3
## Provisional budgets from the plan's Performance section.
const MAX_PARTICLES: int = 1500
const MAX_PARTICLES_PER_ROOM: int = 400
const PARTICLE_RANGE: float = 30.0


func _states() -> Dictionary:
	return (load(BUILDER) as GDScript).load_layout("halcyon_labs").get("light_states", {})


func _light(root: Node, room: String, index: float) -> Node3D:
	return root.get_node("%s/Lights/Light%d" % [room, int(index)]) as Node3D


func test_light_states_are_saved_into_the_blockout() -> void:
	var states: Dictionary = _states()
	assert_gt(states.size(), 0, "layout.json has light_states")
	var saved: Node = (load(BLOCKOUT) as PackedScene).instantiate()
	for room: String in states:
		for index: float in states[room].get("flicker", []):
			var light: CeilingLight = _light(saved, room, index) as CeilingLight
			assert_true(light != null and light.flickers, "%s Light%d flickers" % [room, index])
		for index: float in states[room].get("dead", []):
			var dead: Node3D = _light(saved, room, index)
			assert_eq(dead.scene_file_path, DEAD_LIGHT, "%s Light%d is a dead fixture" % [room, index])
			assert_eq(dead.find_children("*", "Light3D", true, false).size(), 0, "so the bake gets nothing from it")
	saved.free()


func test_dead_fixtures_keep_working_lights_in_every_room() -> void:
	var saved: Node = (load(BLOCKOUT) as PackedScene).instantiate()
	for room: String in _states():
		var working: int = 0
		for node: Node in saved.get_node("%s/Lights" % room).get_children():
			if node is CeilingLight:
				working += 1
		assert_gt(working, 0, "%s still has light" % room)
	saved.free()


func test_atmosphere_lights_are_unshadowed_and_never_baked() -> void:
	var scene: Node = (load(ATMOSPHERE) as PackedScene).instantiate()
	var lights: Array[Node] = scene.find_children("*", "Light3D", true, false)
	assert_gt(lights.size(), 0, "atmosphere has lights")
	for node: Node in lights:
		var light: Light3D = node as Light3D
		assert_false(light.shadow_enabled, "%s unshadowed" % light.name)
		assert_eq(light.light_bake_mode, Light3D.BAKE_DISABLED, "%s not in the bake" % light.name)
		assert_true(light.distance_fade_enabled, "%s fades out with distance" % light.name)
	for node: Node in scene.find_children("*", "GeometryInstance3D", true, false):
		assert_ne((node as GeometryInstance3D).gi_mode, GeometryInstance3D.GI_MODE_STATIC, "%s not baked" % node.name)
	scene.free()


func test_atmosphere_keeps_a_few_lights_per_room() -> void:
	var scene: Node3D = (load(ATMOSPHERE) as PackedScene).instantiate() as Node3D
	add_child_autofree(scene)
	var rooms: Array = (load(BUILDER) as GDScript).load_layout("halcyon_labs")["rooms"]
	for room: Dictionary in rooms:
		var r: Array = room["rect"]
		var rect: Rect2 = Rect2(r[0], r[1], r[2] - r[0], r[3] - r[1]).grow(0.5)
		var count: int = 0
		for node: Node in scene.find_children("*", "Light3D", true, false):
			var at: Vector3 = (node as Node3D).global_position
			if rect.has_point(Vector2(at.x, at.z)):
				count += 1
		assert_lte(count, MAX_LIGHTS_PER_ROOM, "%s atmosphere lights" % room["id"])


func test_alarm_beacons_spin_on_their_own() -> void:
	var scene: Node = (load(ATMOSPHERE) as PackedScene).instantiate()
	var players: Array[Node] = scene.find_children("*", "AnimationPlayer", true, false)
	assert_gt(players.size(), 0, "beacons have animation players")
	for node: Node in players:
		var player: AnimationPlayer = node as AnimationPlayer
		assert_ne(player.autoplay, &"", "%s autoplays" % player.get_parent().name)
		assert_eq(player.get_animation(player.autoplay).loop_mode, Animation.LOOP_LINEAR, "and loops")
	scene.free()


## Counts every emitter in the whole map, so the truck-wreck fire (map.tscn, not
## atmosphere.tscn) is inside the budget too.
func test_particles_stay_inside_the_budget() -> void:
	var map: Node3D = (load(MAP) as PackedScene).instantiate() as Node3D
	var emitters: Array[Node] = map.find_children("*", "GPUParticles3D", true, false)
	assert_not_null(map.get_node_or_null("TruckWreckage/Fire"), "the truck-wreck fire is counted")
	assert_gt(emitters.size(), 0, "the map has particles")
	var total: int = 0
	for node: Node in emitters:
		var particles: GPUParticles3D = node as GPUParticles3D
		total += particles.amount
		assert_between(particles.visibility_range_end, 1.0, PARTICLE_RANGE, "%s has a view range" % particles.name)
	assert_lte(total, MAX_PARTICLES, "map-wide particles")
	for room: Dictionary in (load(BUILDER) as GDScript).load_layout("halcyon_labs")["rooms"]:
		var r: Array = room["rect"]
		var rect: Rect2 = Rect2(r[0], r[1], r[2] - r[0], r[3] - r[1])
		var count: int = 0
		for node: Node in emitters:
			var at: Vector3 = _map_position(node as Node3D, map)
			if rect.has_point(Vector2(at.x, at.z)):
				count += (node as GPUParticles3D).amount
		assert_lte(count, MAX_PARTICLES_PER_ROOM, "%s particles" % room["id"])
	map.free()


## Position in map space without adding the map to the tree.
func _map_position(node: Node3D, map: Node3D) -> Vector3:
	var at: Transform3D = node.transform
	var parent: Node = node.get_parent()
	while parent and parent != map:
		if parent is Node3D:
			at = (parent as Node3D).transform * at
		parent = parent.get_parent()
	return at.origin


func test_atmosphere_is_decoration_under_an_atmosphere_root() -> void:
	var scene: Node = (load(ATMOSPHERE) as PackedScene).instantiate()
	assert_eq(scene.find_children("*", "CollisionObject3D", true, false).size(), 0, "decoration only")
	assert_true(scene is Atmosphere, "root swaps effects with the power")
	scene.free()


func test_airborne_dust_steam_and_smoke_have_soft_textured_edges() -> void:
	var scene: Node = (load(ATMOSPHERE) as PackedScene).instantiate()
	autofree(scene)
	for path: String in ["Dust/MainCorridor", "Steam/CoolantTunnel", "TruckFire/Smoke"]:
		var particles: GPUParticles3D = scene.get_node(path) as GPUParticles3D
		var material: StandardMaterial3D = (particles.draw_pass_1 as QuadMesh).material as StandardMaterial3D
		assert_eq(material.transparency, BaseMaterial3D.TRANSPARENCY_ALPHA, path)
		assert_not_null(material.albedo_texture, path)
		if material.albedo_texture:
			assert_eq(material.albedo_texture.resource_path, "res://assets/textures/halcyon/vapor_wisp.png", path)


func test_monitor_screens_use_the_powered_instance_uniform() -> void:
	var shader: Shader = load(SCREEN_SHADER) as Shader
	assert_string_contains(shader.code, "instance uniform float powered")
	var level: Level = (load(MAP) as PackedScene).instantiate() as Level
	add_child_autofree(level)
	var atmosphere: Atmosphere = level.get_node("Atmosphere") as Atmosphere
	assert_gt(atmosphere.screens().size(), 0, "the map has monitor screens")


func test_sound_spots_are_quiet_local_ambience() -> void:
	var scene: Node = (load(ATMOSPHERE) as PackedScene).instantiate()
	var players: Array[Node] = scene.find_children("*", "AudioStreamPlayer3D", true, false)
	assert_gt(players.size(), 0, "atmosphere has sound spots")
	var script: String = FileAccess.get_file_as_string(SOUND_SCRIPT)
	for node: Node in players:
		var player: AudioStreamPlayer3D = node as AudioStreamPlayer3D
		var path: String = player.stream.resource_path
		assert_eq(player.bus, &"Ambient", "%s on the Ambient bus" % path)
		assert_lte(player.max_distance, MAX_SOUND_DISTANCE, "%s only heard nearby" % path)
		assert_string_contains(script, path.get_file(), "generated by ambience_sfx.py")
		var ogg: AudioStreamOggVorbis = player.stream as AudioStreamOggVorbis
		if ogg:
			assert_true(ogg.loop, "%s loops" % path)
		else:
			assert_eq(
				(player.stream as AudioStreamWAV).loop_mode, AudioStreamWAV.LOOP_DISABLED, "%s is a one-shot" % path
			)
	scene.free()


func test_story_decals_use_story_textures_and_one_green_leak() -> void:
	var scene: Node = (load(ATMOSPHERE) as PackedScene).instantiate()
	var decals: Array[Node] = scene.find_children("*", "Decal", true, false)
	assert_gt(decals.size(), 0, "story decals placed")
	var leaks: int = 0
	for node: Node in decals:
		var decal: Decal = node as Decal
		var path: String = decal.texture_albedo.resource_path
		assert_true(path.begins_with(STORY_TEXTURES), "%s uses a story texture" % decal.name)
		assert_true(decal.distance_fade_enabled, "%s fades with distance" % decal.name)
		if path == LEAK:
			leaks += 1
	assert_eq(leaks, 1, "bio-green only on the one tank leak")
	scene.free()


func test_atmosphere_casts_no_shadows() -> void:
	# Moving particles and meshes that cast shadows make every shadowed light redraw its map each frame.
	var scene: Node = (load(ATMOSPHERE) as PackedScene).instantiate()
	var meshes: Array[Node] = scene.find_children("*", "GeometryInstance3D", true, false)
	assert_gt(meshes.size(), 0, "atmosphere has meshes and particles")
	for node: Node in meshes:
		var mesh: GeometryInstance3D = node as GeometryInstance3D
		assert_eq(mesh.cast_shadow, GeometryInstance3D.SHADOW_CASTING_SETTING_OFF, "%s casts no shadow" % mesh.name)
	scene.free()


func test_story_decals_stay_clear_of_props_and_machines() -> void:
	var level: Level = (load(MAP) as PackedScene).instantiate() as Level
	add_child_autofree(level)
	var props: Array[Rect2] = []
	for prop: Dictionary in (load(BUILDER) as GDScript).load_layout("halcyon_labs")["props"]:
		var box: Array = prop["box"]
		props.append(Rect2(box[0] - box[3] / 2.0, box[2] - box[5] / 2.0, box[3], box[5]))
	var machines: Array[Node] = level.get_node("NavigationRegion3D/Machines").get_children()
	for node: Node in level.get_node("Atmosphere/Story").find_children("*", "Decal", true, false):
		var decal: Decal = node as Decal
		var box: AABB = decal.global_transform * decal.get_aabb()
		var area: Rect2 = Rect2(box.position.x, box.position.z, box.size.x, box.size.z)
		for prop: Rect2 in props:
			assert_false(area.intersects(prop), "%s does not paint a prop" % decal.name)
		for machine: Node in machines:
			var at: Vector3 = (machine as Node3D).global_position
			assert_false(area.grow(0.5).has_point(Vector2(at.x, at.z)), "%s not behind %s" % [decal.name, machine.name])


func test_leak_glow_is_masked() -> void:
	# Decal emission ignores alpha, so the glow needs its own map that is black outside the pool.
	var glow: Image = (load(LEAK.replace("leak_pool", "leak_glow")) as Texture2D).get_image()
	glow.decompress()
	assert_lt(glow.get_pixel(0, 0).v, 0.05, "glow map is black outside the pool")


func test_small_life_fan_pa_and_papers() -> void:
	var scene: Node = (load(ATMOSPHERE) as PackedScene).instantiate()
	var fan: AnimationPlayer = scene.get_node("SmallLife/MessHallFan/AnimationPlayer") as AnimationPlayer
	var turn: Animation = fan.get_animation(fan.autoplay)
	assert_gte(turn.length, 4.0, "the Mess Hall fan turns slowly")
	assert_eq(String(turn.track_get_path(0)), "Blades:rotation:y", "only the blades turn")
	var crackle: AudioStreamPlayer3D = scene.get_node("SmallLife/CorridorPA/Crackle") as AudioStreamPlayer3D
	var timer: Timer = crackle.get_node("Timer") as Timer
	assert_true(timer.autostart, "the PA crackles on its own")
	assert_between(timer.wait_time, 20.0, 40.0, "every 20 to 40 s")
	assert_true(timer.is_connected(&"timeout", crackle.play), "the timer plays the crackle")
	var papers: GPUParticles3D = scene.get_node("SmallLife/LabsPapers") as GPUParticles3D
	assert_lte(papers.amount, 8, "a few papers, not a storm")
	scene.free()


func test_room_work_lights_follow_level_power_and_the_ramp_keeps_emergency_light() -> void:
	var level: Level = (load(MAP) as PackedScene).instantiate() as Level
	add_child_autofree(level)
	var dressing: Node = level.get_node("Atmosphere/RoomDressing")
	var task_lens: Node3D = dressing.get_node("GeneratorHall/WorkLens") as Node3D
	var work_light: Light3D = dressing.get_node("GeneratorHall/ServicePool") as Light3D
	var emergency: Light3D = dressing.get_node("ContainmentRamp/EmergencyPool") as Light3D
	assert_false(task_lens.is_visible_in_tree(), "portable reflector is dark before power")
	assert_false(work_light.is_visible_in_tree(), "no light from the unpowered work lamp")
	assert_true(emergency.is_visible_in_tree(), "the sloped route has emergency lighting")
	Events.blackout_started.emit(6)
	level.turn_power_on()
	assert_false(task_lens.is_visible_in_tree(), "powering up during a Blackout keeps work lamps dark")
	assert_false(work_light.is_visible_in_tree(), "the repair goes dark in a Blackout")
	assert_false(emergency.is_visible_in_tree(), "Blackout also cuts emergency lighting")
	Events.blackout_ended.emit(6)
	assert_true(task_lens.is_visible_in_tree(), "restoring power lights the diffuser")
	assert_true(work_light.is_visible_in_tree(), "restoring power lights the repair")
	assert_true(emergency.is_visible_in_tree(), "emergency housing stays lit")
