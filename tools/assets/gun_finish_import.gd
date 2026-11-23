## Post-import script for the code-built guns: swaps each glTF material for the
## shared gun finish shader, keeping its colour, metal and roughness. The finish
## comes from the Blender material name; a "Knurled" suffix adds the knurl pattern and a
## "Worn" suffix (after Knurled) the heavy chips and grime of the concept guns.
## "Markings" prints the shared markings atlas through UV2.
## "Baked" (ADR 0014) turns on the shader's baked mode with the maps that
## tools/assets/gun_bake.py wrote for this glb: assets/textures/weapons/<glb name>_*.png.
## Optic glass keeps its opaque, non-emissive standard material; red-dot sight glass
## stays a standard material too, but see-through.
@tool
extends EditorScenePostImport

const SHADER: Shader = preload("res://assets/materials/gun_finish.gdshader")
const SURFACE_DETAIL: Texture2D = preload("res://assets/textures/weapons/surface_detail.png")
const FINISHES: Dictionary[String, int] = {
	"GunMetal": 0,
	"Brass": 0,
	"MatteBlack": 1,
	"OliveCoat": 1,
	"Tan": 2,
	"OlivePolymer": 2,
	"GreyPolymer": 2,
	"Wood": 3,
	"Markings": 2,
	"FactoryPrint": 2,
}
const KNURLED: String = "Knurled"
const WORN: String = "Worn"
const MARKINGS: String = "Markings"
const MARKINGS_MAP: String = "res://assets/textures/gun_markings.png"
## Concept-gun wear: chips past the edges, and grime in creases.
const WORN_WEAR: float = 1.6
const WORN_GRIME: float = 0.8
const BAKED: String = "Baked"
const BAKED_MAPS: String = "res://assets/textures/weapons/%s_%s.png"
const STANDARD: Array[String] = ["OpticGlass", "SightGlass"]
const SIGHT_GLASS: String = "SightGlass"
const SIGHT_GLASS_ALPHA: float = 0.18


func _post_import(scene: Node) -> Object:
	for node: Node in scene.find_children("*", "MeshInstance3D", true, false):
		var mesh: Mesh = (node as MeshInstance3D).mesh
		for i: int in mesh.get_surface_count():
			var source: BaseMaterial3D = mesh.surface_get_material(i) as BaseMaterial3D
			if source == null:
				continue
			if source.resource_name in STANDARD:
				source.vertex_color_use_as_albedo = true
				source.emission_enabled = false
				if source.resource_name == SIGHT_GLASS:
					source.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
					source.albedo_color.a = SIGHT_GLASS_ALPHA
					source.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
				continue
			if source.resource_name == BAKED:
				mesh.surface_set_material(i, baked_material(get_source_file().get_file().get_basename()))
			else:
				mesh.surface_set_material(i, finish_material(source))
	return scene


static func finish_material(source: BaseMaterial3D) -> Material:
	var mat_name: String = source.resource_name
	var worn: bool = mat_name.ends_with(WORN)
	var knurled: bool = mat_name.trim_suffix(WORN).ends_with(KNURLED)
	var base: String = mat_name.trim_suffix(WORN).trim_suffix(KNURLED)
	if not FINISHES.has(base):
		push_error("gun material '%s' has no finish; add it to FINISHES" % mat_name)
		return source
	var material: ShaderMaterial = ShaderMaterial.new()
	material.resource_name = mat_name
	material.shader = SHADER
	material.set_shader_parameter(&"albedo", source.albedo_color)
	material.set_shader_parameter(&"metallic", source.metallic)
	material.set_shader_parameter(&"roughness", source.roughness)
	material.set_shader_parameter(&"finish", FINISHES[base])
	material.set_shader_parameter(&"surface_detail", SURFACE_DETAIL)
	material.set_shader_parameter(&"knurled", knurled)
	if worn or base == MARKINGS:
		material.set_shader_parameter(&"wear", WORN_WEAR)
		material.set_shader_parameter(&"grime", WORN_GRIME)
	if base == MARKINGS or base == "FactoryPrint":
		material.set_shader_parameter(&"marked", true)
		material.set_shader_parameter(&"markings_map", load(MARKINGS_MAP) as Texture2D)
	return material


static func baked_material(gun: String) -> Material:
	var material: ShaderMaterial = ShaderMaterial.new()
	material.resource_name = BAKED
	material.shader = SHADER
	material.set_shader_parameter(&"baked", true)
	for kind: String in ["albedo", "normal", "orm"]:
		var path: String = BAKED_MAPS % [gun, kind]
		if not ResourceLoader.exists(path):
			push_error("baked gun '%s' has no %s map; run tools/assets/gun_bake.py" % [gun, kind])
			continue
		material.set_shader_parameter(StringName(kind + "_map"), load(path) as Texture2D)
	return material
