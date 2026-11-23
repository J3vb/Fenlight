## Post-import script for props, dressing and Lantern Post buildings: maps each named glb
## slot to the shared textured material in levels/materials (SHARED), after the
## embedded materials take the baked AO vertex colour (grime reads it too).
@tool
extends "res://tools/assets/vertex_shading_import.gd"

const SHARED: Dictionary = {
	"Steel": "res://levels/materials/steel.tres",
	"Dark": "res://levels/materials/rubber.tres",
	"Paint": "res://levels/materials/panel_paint.tres",
	"Laminate": "res://levels/materials/panel_trim.tres",
	"Olive": "res://levels/materials/rust.tres",
	"Wood": "res://levels/materials/wood.tres",
	"Glass": "res://levels/materials/glass.tres",
	"Fluid": "res://levels/materials/specimen_tank.tres",
	"IntactTankFluid": "res://levels/materials/intact_tank_fluid.tres",
	"JarFluid": "res://levels/materials/jar_fluid.tres",
	"FacilityFinish": "res://levels/materials/facility_finish.tres",
	"GeneratorFinish": "res://levels/materials/generator_finish.tres",
	"CordonPrint": "res://levels/materials/cordon_print.tres",
	"Paper": "res://levels/materials/paper.tres",
	"Alarm": "res://levels/materials/alarm_paint.tres",
	"SodiumPaint": "res://levels/materials/sodium_paint.tres",
	"Hazard": "res://levels/materials/hazard_paint.tres",
	"Concrete": "res://levels/materials/raw_concrete.tres",
	"Vine": "res://levels/materials/fenlight_vine.tres",
	"Screen": "res://systems/effects/monitor_screen.tres",
	"Logs": "res://levels/materials/town_logs.tres",
	"Planks": "res://levels/materials/town_planks.tres",
	"DarkWood": "res://levels/materials/town_dark_wood.tres",
	"RoofSnow": "res://levels/materials/town_slate.tres",
	"Snow": "res://levels/materials/town_snow.tres",
	"Iron": "res://levels/materials/iron.tres",
	"WindowGlow": "res://levels/materials/lit_window.tres",
	"Canvas": "res://levels/materials/town_canvas.tres",
	"SignPaint": "res://levels/materials/town_sign_paint.tres",
	"TownHazard": "res://levels/materials/town_hazard.tres",
	"Banner": "res://levels/materials/town_banner.tres",
	"Beacon": "res://levels/materials/beacon_red.tres",
	"Bulb": "res://levels/materials/sodium_lamp.tres",
	"Pine": "res://levels/materials/pine.tres",
	"Stone": "res://levels/materials/stone.tres",
	"Tile": "res://levels/materials/clinic_tile.tres",
	"Enamel": "res://levels/materials/enamel.tres",
	"Ice": "res://levels/materials/ice.tres",
	"Burlap": "res://levels/materials/burlap.tres",
}


func _post_import(scene: Node) -> Object:
	super._post_import(scene)
	for node: Node in scene.find_children("*", "MeshInstance3D", true, false):
		var mesh: Mesh = (node as MeshInstance3D).mesh
		for i: int in mesh.get_surface_count():
			var material: Material = mesh.surface_get_material(i)
			if material and SHARED.has(material.resource_name):
				mesh.surface_set_material(i, load(SHARED[material.resource_name]) as Material)
	return scene
