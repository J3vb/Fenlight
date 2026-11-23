## Checks the double-barrel silhouettes, bored tubes, animation pivots and dynamic gun imports.
extends GutTest

const MODEL: String = "res://assets/models/weapons/%s.glb"
const GUNS: Dictionary = {
	&"coachman_2b": [0.98, 1.08, "Stock", 0.044, -0.58, -0.12, 0.018],
	&"grubber_sawnoff": [0.44, 0.54, "Grip", 0.032, -0.32, -0.1, 0.015],
}


func _load_gun(id: StringName) -> Node3D:
	var scene: PackedScene = load(MODEL % id) as PackedScene
	assert_not_null(scene, String(id) + " imports as a scene")
	return scene.instantiate() as Node3D if scene else null


func _bounds(node: Node, transform: Transform3D, out: Array[AABB]) -> void:
	var here: Transform3D = transform * (node as Node3D).transform if node is Node3D else transform
	if node is MeshInstance3D:
		var box: AABB = here * (node as MeshInstance3D).get_aabb()
		out[0] = box if out[0].size == Vector3.ZERO else out[0].merge(box)
	for child: Node in node.get_children():
		_bounds(child, here, out)


func test_models_have_two_barrels_and_independent_action_parts() -> void:
	for id: StringName in GUNS:
		var gun: Node3D = _load_gun(id)
		if gun == null:
			continue
		var receiver: Node3D = gun.find_child("Receiver", true, false) as Node3D
		assert_true(receiver is MeshInstance3D, String(id) + " static action is joined")
		var hinge: Node3D = receiver.get_node("Hinge") as Node3D
		for part: String in ["Hinge", "Bolt", "Trigger", GUNS[id][2]]:
			var node: Node3D = gun.find_child(part, true, false) as Node3D
			assert_not_null(node, "%s has %s" % [id, part])
			if node:
				assert_eq(node.get_parent(), receiver, "%s %s has an independent pivot" % [id, part])
		for part: String in ["BarrelL", "BarrelR", "Muzzle", "Foregrip"]:
			assert_true(hinge.has_node(part), "%s carries %s as the gun opens" % [id, part])
		assert_null(gun.find_child("Magazine", true, false), "break action loads shells by hand")
		var muzzle: Node3D = gun.find_child("Muzzle", true, false) as Node3D
		assert_lt((hinge.transform * muzzle.position).z, -0.28, String(id) + " fires down Godot -Z")
		assert_true(gun.scale.is_equal_approx(Vector3.ONE), "imports in metres")
		var box: Array[AABB] = [AABB()]
		_bounds(gun, Transform3D.IDENTITY, box)
		assert_between(box[0].size.z, GUNS[id][0], GUNS[id][1], String(id) + " length fits its role")
		assert_lt(box[0].size.x, 0.09, String(id) + " barrels fit a narrow side-by-side action")
		gun.free()


func test_both_muzzles_are_open_bores() -> void:
	for id: StringName in GUNS:
		var gun: Node3D = _load_gun(id)
		for side: float in [-1.0, 1.0]:
			var start: Vector3 = Vector3(side * GUNS[id][6], GUNS[id][3], GUNS[id][4])
			var end: Vector3 = Vector3(start.x, start.y, GUNS[id][5])
			assert_false(MeshChecks.blocks_segment(gun, start, end), "%s barrel %s is hollow" % [id, side])
		gun.free()


func test_models_keep_gun_geometry_and_material_budgets() -> void:
	var rifle: Node3D = _load_gun(&"rifle_ar")
	var rifle_triangles: int = 0
	for node: Node in rifle.find_children("*", "MeshInstance3D", true, false):
		rifle_triangles += int((node as MeshInstance3D).mesh.get_faces().size() / 3.0)
	rifle.free()
	for id: StringName in GUNS:
		var gun: Node3D = _load_gun(id)
		var meshes: Array[Node] = gun.find_children("*", "MeshInstance3D", true, false)
		var triangles: int = 0
		var finishes: Array[String] = []
		for node: Node in meshes:
			var mesh: Mesh = (node as MeshInstance3D).mesh
			triangles += int(mesh.get_faces().size() / 3.0)
			for surface: int in mesh.get_surface_count():
				var material: Material = mesh.surface_get_material(surface)
				assert_not_null(material, String(id) + " each surface has a finish")
				if material and not finishes.has(material.resource_name):
					finishes.append(material.resource_name)
		assert_gt(triangles, 0)
		assert_lte(triangles, 8000, String(id) + " stays in the weapon triangle budget")
		assert_lte(triangles, int(rifle_triangles * 1.5), String(id) + " stays below 1.5x rifle triangles")
		assert_between(finishes.size(), 3, 6, String(id) + " distinct restrained finishes")
		assert_lte(meshes.size(), 12, String(id) + " bounds draw calls")
		gun.free()


func test_bead_sight_lines_are_clear_at_the_content_ads_height() -> void:
	for id: StringName in GUNS:
		var gun: Node3D = _load_gun(id)
		var height: float = -Content.weapon(id).ads_position.y
		var eye: Vector3 = Vector3(0, height + 0.003, 0.6)
		assert_false(
			MeshChecks.blocks_segment(gun, eye, Vector3(0, eye.y, -0.8)), String(id) + " bead sight picture stays open"
		)
		eye.y = height - 0.004
		assert_true(
			MeshChecks.blocks_segment(gun, eye, Vector3(0, eye.y, -0.8)),
			String(id) + " bead sits just below the aiming line"
		)
		gun.free()


func test_imports_use_dynamic_lighting_and_gun_finish() -> void:
	for id: StringName in GUNS:
		var settings: ConfigFile = ConfigFile.new()
		assert_eq(settings.load((MODEL % id) + ".import"), OK, "import settings are committed")
		assert_eq(settings.get_value("params", "meshes/light_baking"), 3, "gun gets dynamic lighting")
		assert_true(settings.get_value("params", "meshes/generate_lods"), "gun generates LODs")
		assert_eq(settings.get_value("params", "import_script/path"), "res://tools/assets/gun_finish_import.gd")
