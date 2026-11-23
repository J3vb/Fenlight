## Checks the gun finish from tools/assets/gun_finish_import.gd: every gun surface
## except optic glass uses the shared gun shader with the colour, finish and knurl
## its Blender material asked for, and the shader multiplies in the baked shading.
## Baked guns (ADR 0014) get the same shader in baked mode with their three maps.
extends GutTest

const GUNS: Array[String] = [
	"rifle_ar",
	"kestrel_smg",
	"talon_dmr",
	"shotgun_brenner",
	"hollis_44",
	"mako_pdw",
	"atlas_auto",
	"halberd_lmg",
	"corvid_338",
	"siphon"
]
const SHADER: String = "res://assets/materials/gun_finish.gdshader"
const IMPORTER: GDScript = preload("res://tools/assets/gun_finish_import.gd")
const BAKED_GUNS: Array[String] = ["rifle_ar"]
const KNURLED: Dictionary[String, String] = {
	"kestrel_smg": "MatteBlackKnurledWorn",
	"talon_dmr": "GunMetalKnurledWorn",
	"hollis_44": "WoodKnurled",
}


func _materials(id: String) -> Dictionary[String, Material]:
	var gun: Node3D = (load("res://assets/models/weapons/%s.glb" % id) as PackedScene).instantiate() as Node3D
	var out: Dictionary[String, Material] = {}
	for node: Node in gun.find_children("*", "MeshInstance3D", true, false):
		var mesh: Mesh = (node as MeshInstance3D).mesh
		for i: int in mesh.get_surface_count():
			var material: Material = mesh.surface_get_material(i)
			out[material.resource_name] = material
	gun.free()
	return out


func test_every_gun_surface_uses_the_finish_shader() -> void:
	for file: String in ResourceLoader.list_directory("res://assets/models/weapons"):
		if not file.ends_with(".glb"):
			continue
		var id: String = file.get_basename()
		var materials: Dictionary[String, Material] = _materials(id)
		for mat_name: String in materials:
			var material: Material = materials[mat_name]
			if mat_name in IMPORTER.STANDARD:
				assert_true(material is BaseMaterial3D, id + " optic glass keeps its standard material")
				continue
			assert_true(material is ShaderMaterial, "%s %s uses the finish shader" % [id, mat_name])
			if material is ShaderMaterial:
				assert_eq((material as ShaderMaterial).shader.resource_path, SHADER, "%s %s shader" % [id, mat_name])
				if mat_name != "Baked":
					var tile: Texture2D = _param(material, "surface_detail") as Texture2D
					assert_not_null(tile, "%s %s has a surface detail tile" % [id, mat_name])


func test_finish_follows_the_material_name() -> void:
	var coachman: Dictionary[String, Material] = _materials("coachman_2b")
	assert_eq(_param(coachman["Wood"], "finish"), 3, "walnut gets the wood grain")
	assert_eq(_param(coachman["GunMetal"], "finish"), 0, "bare metal parts")
	assert_eq(_param(coachman["MatteBlack"], "finish"), 1, "black parts are a coating")
	var nightjar: Dictionary[String, Material] = _materials("nightjar_sd")
	assert_eq(_param(nightjar["GreyPolymer"], "finish"), 2, "grey stock is polymer")
	for id: String in KNURLED:
		var materials: Dictionary[String, Material] = _materials(id)
		assert_true(materials.has(KNURLED[id]), id + " has knurled parts")
		if materials.has(KNURLED[id]):
			assert_true(_param(materials[KNURLED[id]], "knurled"), id + " knurl pattern is on")
		var plain: String = "GunMetalWorn" if materials.has("GunMetalWorn") else "GunMetal"
		assert_false(_param(materials[plain], "knurled"), id + " plain metal stays smooth")


func test_colour_metal_and_roughness_come_from_blender() -> void:
	var rifle: Dictionary[String, Material] = _materials("kestrel_smg")
	var tan_color: Color = _param(rifle["TanWorn"], "albedo")
	assert_gt(tan_color.r, tan_color.b, "tan stays warm")
	assert_almost_eq(_param(rifle["GunMetalWorn"], "metallic"), 0.8, 0.01, "gunmetal stays metallic")
	assert_almost_eq(_param(rifle["MatteBlackWorn"], "roughness"), 0.75, 0.01, "black stays matte")


func test_worn_suffix_adds_heavy_wear_and_grime_only_to_concept_guns() -> void:
	var rifle: Dictionary[String, Material] = _materials("kestrel_smg")
	assert_eq(_param(rifle["MatteBlackWorn"], "finish"), 1, "worn black is still a coating")
	assert_gt(_param(rifle["MatteBlackWorn"], "wear"), 1.0, "worn paint chips past the edges")
	assert_gt(_param(rifle["MatteBlackWorn"], "grime"), 0.0, "worn guns collect grime")
	assert_true(_param(rifle["MatteBlackKnurledWorn"], "knurled"), "Knurled still works before Worn")
	var hollis: Dictionary[String, Material] = _materials("hollis_44")
	for mat_name: String in hollis:
		if hollis[mat_name] is ShaderMaterial:
			assert_null(_param(hollis[mat_name], "wear"), "other guns keep the shader's default wear")
			assert_null(_param(hollis[mat_name], "grime"), "other guns stay clean")


func test_markings_print_the_shared_atlas() -> void:
	var markings: Material = _materials("kestrel_smg")["Markings"]
	assert_true(_param(markings, "marked"), "markings read the atlas")
	var atlas: Texture2D = _param(markings, "markings_map")
	assert_not_null(atlas, "atlas is set")
	if atlas:
		assert_eq(atlas.resource_path, IMPORTER.MARKINGS_MAP, "the one shared atlas")
	assert_string_contains((load(SHADER) as Shader).code, "texture(markings_map, UV2)")


func test_baked_guns_use_their_three_maps() -> void:
	for id: String in BAKED_GUNS:
		var materials: Dictionary[String, Material] = _materials(id)
		assert_eq(materials.keys().filter(func(n: String) -> bool: return not n in IMPORTER.STANDARD), ["Baked"])
		var baked: Material = materials.get("Baked")
		assert_true(_param(baked, "baked"), id + " shader runs in baked mode")
		for kind: String in ["albedo", "normal", "orm"]:
			var map: Texture2D = _param(baked, kind + "_map")
			assert_not_null(map, "%s %s map" % [id, kind])
			if map:
				assert_eq(map.resource_path, IMPORTER.BAKED_MAPS % [id, kind])
				assert_eq(map.get_size(), Vector2(2048, 2048), "%s %s map is full size" % [id, kind])


func test_baked_mode_keeps_the_rarity_inlay() -> void:
	var code: String = (load(SHADER) as Shader).code
	var tail: String = code.substr(code.find("if (baked)"))
	assert_string_contains(tail, "NORMAL_MAP = texture(normal_map, UV)")
	assert_string_contains(tail, "color = mix(color, rarity_color.rgb, inlay)", "inlay comes after both modes")


func test_missing_baked_map_is_reported() -> void:
	var material: ShaderMaterial = IMPORTER.baked_material("no_such_gun") as ShaderMaterial
	assert_true(material.get_shader_parameter(&"baked"))
	assert_push_error("has no albedo map")
	assert_push_error("has no normal map")
	assert_push_error("has no orm map")


func test_unknown_material_keeps_its_standard_material() -> void:
	var source: StandardMaterial3D = StandardMaterial3D.new()
	source.resource_name = "Chrome"
	assert_eq(IMPORTER.finish_material(source), source, "an unmapped name is left alone")
	assert_push_error("has no finish")


func test_shader_multiplies_in_the_baked_shading() -> void:
	var code: String = (load(SHADER) as Shader).code
	assert_string_contains(code, "ALBEDO = color * ao")
	assert_string_contains(code, "ao = COLOR.r")


func test_rarity_overrides_are_local_to_each_mesh() -> void:
	var shared: ShaderMaterial = ShaderMaterial.new()
	shared.shader = load(SHADER) as Shader
	var common: MeshInstance3D = MeshInstance3D.new()
	var legendary: MeshInstance3D = MeshInstance3D.new()
	for part: MeshInstance3D in [common, legendary]:
		part.mesh = BoxMesh.new()
		part.material_override = shared
		add_child_autofree(part)
	common.set_instance_shader_parameter(&"rarity_color", Color("#D9D9D2"))
	legendary.set_instance_shader_parameter(&"rarity_color", Color("#FF8A1C"))
	assert_eq(common.get_instance_shader_parameter(&"rarity_color"), Color("#D9D9D2"))
	assert_eq(legendary.get_instance_shader_parameter(&"rarity_color"), Color("#FF8A1C"))
	assert_same(common.material_override, legendary.material_override, "rarity does not duplicate the finish")


func test_imported_rarity_masks_cover_only_a_thin_inlay() -> void:
	for id: String in GUNS:
		var gun: Node3D = (load("res://assets/models/weapons/%s.glb" % id) as PackedScene).instantiate() as Node3D
		var areas: Vector2 = Vector2.ZERO
		for node: Node in gun.find_children("*", "MeshInstance3D", true, false):
			var mesh: Mesh = (node as MeshInstance3D).mesh
			for surface: int in mesh.get_surface_count():
				areas += _inlay_area(mesh.surface_get_arrays(surface))
		assert_gt(areas.x, 0.0, id + " exports a rarity inlay")
		assert_lt(areas.x / areas.y, 0.02, id + " rarity stays below two percent of surface area")
		gun.free()


func test_red_dot_glass_is_see_through_and_non_emissive() -> void:
	var glass: BaseMaterial3D = _materials("kestrel_smg")["SightGlass"] as BaseMaterial3D
	assert_false(glass.emission_enabled, "red dot glass does not glow")
	assert_eq(glass.transparency, BaseMaterial3D.TRANSPARENCY_ALPHA, "you aim through the red dot glass")
	assert_lt(glass.albedo_color.a, 0.5, "the glass is mostly clear")


func test_optic_glass_stays_opaque_and_non_emissive() -> void:
	for id: String in ["talon_dmr", "corvid_338"]:
		var materials: Dictionary[String, Material] = _materials(id)
		var glass: BaseMaterial3D = materials["OpticGlass"] as BaseMaterial3D
		assert_false(glass.emission_enabled, id + " optic does not glow")
		assert_eq(glass.transparency, BaseMaterial3D.TRANSPARENCY_DISABLED, id + " optic keeps depth writing")


func test_existing_guns_leave_the_prototype_glow_zone_unused() -> void:
	for id: String in GUNS:
		var gun: Node3D = (load("res://assets/models/weapons/%s.glb" % id) as PackedScene).instantiate() as Node3D
		var glow_vertices: int = 0
		for node: Node in gun.find_children("*", "MeshInstance3D", true, false):
			var mesh: Mesh = (node as MeshInstance3D).mesh
			for surface: int in mesh.get_surface_count():
				var colors: PackedColorArray = mesh.surface_get_arrays(surface)[Mesh.ARRAY_COLOR]
				for color: Color in colors:
					if color.a > 0.15 and color.a < 0.5:
						glow_vertices += 1
		assert_eq(glow_vertices, 0, id + " keeps its existing inlay without emission")
		gun.free()


func _inlay_area(arrays: Array) -> Vector2:
	var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var colors: PackedColorArray = arrays[Mesh.ARRAY_COLOR]
	var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
	var areas: Vector2 = Vector2.ZERO
	for index: int in range(0, indices.size(), 3):
		var a: int = indices[index]
		var b: int = indices[index + 1]
		var c: int = indices[index + 2]
		var area: float = (vertices[b] - vertices[a]).cross(vertices[c] - vertices[a]).length() * 0.5
		areas.y += area
		if colors[a].a < 0.5 or colors[b].a < 0.5 or colors[c].a < 0.5:
			areas.x += area
	return areas


func _param(material: Material, param: String) -> Variant:
	return (material as ShaderMaterial).get_shader_parameter(param)
