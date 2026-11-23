## Lantern Post market row from tools/assets/town_market.py (plan F-74 step 3, asset list S1-S7): one static
## lightmapped mesh each on the origin, the listed width, shared town materials only, and the stall awning in
## Canvas and the sign board in SignPaint.
extends GutTest

const FOLDER: String = "res://assets/models/town/%s.glb"
const MATERIALS: String = "res://levels/materials/"
## Model id -> width from the asset list.
const MARKET: Dictionary = {
	"stall_frame": 4.0,
	"stall_sign": 3.6,
	"missions_board": 3.0,
	"trader_goods": 2.0,
	"gun_wall": 3.0,
	"workbench": 2.0,
	"tech_desk": 2.0,
}
const SIZE_TOLERANCE: float = 0.2
const SHARED_SCREEN: String = "res://systems/effects/monitor_screen.tres"


func _mesh(id: String) -> MeshInstance3D:
	var packed: PackedScene = load(FOLDER % id) as PackedScene
	assert_not_null(packed, id + " imports as a scene")
	var scene: Node = packed.instantiate()
	add_child_autofree(scene)
	var meshes: Array[Node] = scene.find_children("*", "MeshInstance3D", true, false)
	assert_eq(meshes.size(), 1, id + " is one mesh")
	return meshes[0] as MeshInstance3D


func _material_paths(id: String) -> Array[String]:
	var mesh: Mesh = _mesh(id).mesh
	var paths: Array[String] = []
	for i: int in mesh.get_surface_count():
		paths.append(mesh.surface_get_material(i).resource_path)
	return paths


func test_market_models_are_static_lightmapped_with_shared_materials() -> void:
	for id: String in MARKET:
		var settings: ConfigFile = ConfigFile.new()
		assert_eq(settings.load(FOLDER % id + ".import"), OK)
		assert_eq(settings.get_value("params", "meshes/light_baking"), 2, id + " bakes into the lightmap")
		assert_eq(settings.get_value("params", "import_script/path"), "res://tools/assets/prop_import.gd", id)
		for path: String in _material_paths(id):
			var shared: bool = path.begins_with(MATERIALS) or path == SHARED_SCREEN
			assert_true(shared, "%s uses a shared material: %s" % [id, path])


func test_market_models_stand_on_the_origin_at_their_listed_width() -> void:
	for id: String in MARKET:
		var box: AABB = _mesh(id).get_aabb()
		assert_almost_eq(box.position.y, 0.0, 0.01, id + " bottom on the ground")
		assert_lt(Vector2(box.get_center().x, box.get_center().z).length(), 0.05, id + " origin under the middle")
		assert_between(box.size.x / MARKET[id], 1.0 - SIZE_TOLERANCE, 1.0 + SIZE_TOLERANCE, id + " width")


func test_awning_is_canvas_and_sign_is_painted() -> void:
	assert_has(_material_paths("stall_frame"), MATERIALS + "town_canvas.tres", "stall awning uses Canvas")
	assert_has(_material_paths("stall_sign"), MATERIALS + "town_sign_paint.tres", "sign board uses SignPaint")
	assert_has(_material_paths("tech_desk"), SHARED_SCREEN, "tech desk monitors glow like the lab screens")


func test_missions_board_uses_the_printed_survey_atlas() -> void:
	var print_path: String = MATERIALS + "cordon_print.tres"
	assert_has(_material_paths("missions_board"), print_path)
	var paper: StandardMaterial3D = load(print_path) as StandardMaterial3D
	assert_not_null(paper.albedo_texture, "the chart and notices have their printed ink")
