## Checks the code-built prop, dressing and large prop models (plans F-15, F-77): each
## loads as one mesh, imports as a static lightmapped piece with baked AO shading, every
## surface uses a shared prop_import.gd slot material (Tripo props keep their one baked
## material, ADR 0017), and monitors use the shared screen.
extends GutTest

const FOLDERS: Array[String] = [
	"res://assets/models/props/",
	"res://assets/models/dressing/",
	"res://assets/models/props_large/",
]
const IMPORTER: GDScript = preload("res://tools/assets/prop_import.gd")
const SCREEN: String = "res://systems/effects/monitor_screen.tres"
const WITH_SCREEN: Array[String] = [
	"res://assets/models/props/lab_bench.glb",
	"res://assets/models/props/guard_desk.glb",
	"res://assets/models/props/vending_machine.glb",
]


func _models() -> Array[String]:
	var out: Array[String] = []
	for folder: String in FOLDERS:
		if not DirAccess.dir_exists_absolute(folder):
			continue
		for file: String in DirAccess.get_files_at(folder):
			if file.ends_with(".glb"):
				out.append(folder + file)
	return out


func _meshes(path: String) -> Array[MeshInstance3D]:
	var scene: Node = (load(path) as PackedScene).instantiate()
	var out: Array[MeshInstance3D] = []
	for node: Node in scene.find_children("*", "MeshInstance3D", true, false):
		out.append(node as MeshInstance3D)
	autofree(scene)
	return out


func test_every_model_is_one_static_lightmapped_mesh() -> void:
	assert_gt(_models().size(), 0, "prop models exist")
	for path: String in _models():
		assert_eq(_meshes(path).size(), 1, path + " is one mesh (one draw per material)")
		var settings: ConfigFile = ConfigFile.new()
		assert_eq(settings.load(path + ".import"), OK)
		assert_eq(settings.get_value("params", "meshes/light_baking"), 2, path + " bakes into the lightmap")
		assert_eq(
			settings.get_value("params", "import_script/path"),
			"res://tools/assets/prop_import.gd",
			path + " uses its baked AO shading"
		)


func test_monitors_keep_a_screen_surface() -> void:
	for path: String in WITH_SCREEN:
		var paths: Array[String] = []
		for mesh: MeshInstance3D in _meshes(path):
			for i: int in mesh.mesh.get_surface_count():
				var mat: Material = mesh.mesh.surface_get_material(i)
				paths.append(mat.resource_path if mat else "")
		assert_has(paths, SCREEN, path + " shows the shared monitor screen")


func test_every_surface_uses_a_shared_slot() -> void:
	var shared: Array = IMPORTER.SHARED.values()
	for path: String in _models():
		for mesh: MeshInstance3D in _meshes(path):
			for i: int in mesh.mesh.get_surface_count():
				var mat: Material = mesh.mesh.surface_get_material(i)
				if _is_tripo_baked(mat):
					continue
				var where: String = mat.resource_path if mat else "no material"
				assert_has(shared, where, "%s surface %d uses a prop_import.gd SHARED slot" % [path, i])


func test_tripo_props_are_one_baked_material_with_its_maps() -> void:
	var tripo: int = 0
	for path: String in _models():
		var mesh: Mesh = _meshes(path)[0].mesh
		if not _is_tripo_baked(mesh.surface_get_material(0)):
			continue
		tripo += 1
		assert_eq(mesh.get_surface_count(), 1, path + " is one baked surface")
		var baked: StandardMaterial3D = mesh.surface_get_material(0) as StandardMaterial3D
		assert_not_null(baked.albedo_texture, path + " keeps its baked colour map")
		assert_not_null(baked.normal_texture, path + " keeps its baked normal map")
	assert_gte(tripo, 12, "the F-83 Halcyon room props are Tripo models")


func _is_tripo_baked(mat: Material) -> bool:
	return mat is StandardMaterial3D and mat.resource_name == "Baked"


func test_library_slots_load() -> void:
	for slot: String in ["Stone", "Tile", "Enamel", "Ice", "Burlap", "Beacon"]:
		assert_true(IMPORTER.SHARED.has(slot), slot + " is a shared slot")
		assert_true(load(IMPORTER.SHARED[slot]) is Material, slot + " loads as a material")


func test_intact_tank_keeps_its_specimen_visible_through_the_fluid() -> void:
	var mesh: Mesh = _meshes("res://assets/models/props/specimen_tank.glb")[0].mesh
	var fluid: StandardMaterial3D = load(IMPORTER.SHARED["IntactTankFluid"]) as StandardMaterial3D
	var surfaces: Array[Material] = []
	for i: int in mesh.get_surface_count():
		surfaces.append(mesh.surface_get_material(i))
	assert_has(surfaces, fluid, "the intact tank uses the translucent liquid")
	assert_eq(fluid.transparency, BaseMaterial3D.TRANSPARENCY_ALPHA)
	assert_between(fluid.albedo_color.a, 0.05, 0.5, "the host shows through tinted liquid")
