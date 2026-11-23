## Renders one picture per Halcyon Labs room into screenshots/rooms/ for look checks of
## materials and props, and prints the draw calls of each shot. Needs a display:
##   xvfb-run -s "-screen 0 1600x900x24" godot --path . --rendering-driver opengl3 res://tools/room_shots.tscn
## Pass -- --concepts for the eleven paintover cameras, with the player flashlight at 62 degrees FOV.
extends Node

const MAP: String = "res://levels/halcyon_labs/map.tscn"
const ROOM_DIR: String = "res://screenshots/rooms"
const CONCEPT_DIR: String = "res://screenshots/room-concepts"
## name, camera position, look-at point (map coordinates, metres).
const SHOTS: Array = [
	["loading_dock", Vector3(24, 1.7, 58), Vector3(44, 1.2, 48)],
	["guard_post", Vector3(12, 1.7, 48), Vector3(20, 1.0, 32)],
	["mess_hall", Vector3(40, 1.7, 44), Vector3(56, 1.5, 32)],
	["main_corridor", Vector3(19, 1.7, 28), Vector3(47, 1.4, 28)],
	["generator_hall", Vector3(10, 1.7, 24), Vector3(26, 1.5, 8)],
	["labs", Vector3(37, 1.7, 25), Vector3(51, 1.0, 11)],
	["coolant_tunnel", Vector3(28.5, 1.7, 12.5), Vector3(36, 1.4, 12.5)],
	["containment_wing", Vector3(62, -1.3, 30), Vector3(74, -2.0, 6)],
	["signs_mess_hall", Vector3(44, 1.7, 40), Vector3(40, 1.6, 30)],
	["signs_vent_ledge", Vector3(50, 1.7, 44), Vector3(58, 2.2, 45)],
	["signs_main_corridor", Vector3(31, 1.7, 29.5), Vector3(31, 1.6, 26)],
	["signs_generator_hall", Vector3(20, 1.7, 14), Vector3(20.3, 1.8, 6)],
	["signs_labs", Vector3(46, 1.7, 17), Vector3(46.5, 1.9, 26)],
	["signs_containment_wing", Vector3(64, -1.3, 14), Vector3(64, -1.0, 4)],
	["signs_loading_dock", Vector3(27, 1.7, 52), Vector3(30, 2.2, 46)],
	["signs_guard_post", Vector3(15, 1.7, 40), Vector3(14, 1.8, 30)],
]

const CONCEPT_SHOTS: Array = [
	["loading_dock", Vector3(34.9, 1.7, 59.55), Vector3(29, 1.4, 54)],
	SHOTS[1],
	SHOTS[2],
	SHOTS[3],
	SHOTS[4],
	SHOTS[5],
	["coolant_tunnel", Vector3(33.75, 1.65, 13.35), Vector3(30.3, 2.35, 11.65)],
	SHOTS[7],
	["containment_ramp", Vector3(52.3, 1.6, 17), Vector3(60.4, -1.7, 18.2)],
	["vent_route", Vector3(62.7, 2.74, 43), Vector3(62.4, -0.95, 34)],
	["cold_room", Vector3(51.25, 1.65, 46.8), Vector3(55.6, 1.05, 49.4)],
]


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	var concepts: bool = OS.get_cmdline_user_args().has("--concepts")
	var directory: String = CONCEPT_DIR if concepts else ROOM_DIR
	var error: Error = DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(directory))
	if error != OK:
		push_error("Cannot create %s (%s)" % [directory, error_string(error)])
		get_tree().quit(1)
		return
	var map: Node = (load(MAP) as PackedScene).instantiate()
	add_child(map)
	(map as Level).turn_power_on()
	# Lights come back in a wave after power-on; shooting earlier swings room brightness by about 40 %.
	await get_tree().create_timer(3.0).timeout
	var camera: Camera3D = Camera3D.new()
	camera.fov = 62.0 if concepts else 75.0
	if concepts:
		_attach_flashlight(camera)
	add_child(camera)
	camera.make_current()
	var shots: Array = CONCEPT_SHOTS if concepts else SHOTS
	for shot: Array in shots:
		camera.look_at_from_position(shot[1], shot[2])
		for _i: int in 12:
			await get_tree().process_frame
		var path: String = directory.path_join("%s.png" % shot[0])
		error = get_viewport().get_texture().get_image().save_png(path)
		if error != OK:
			push_error("Cannot save %s (%s)" % [path, error_string(error)])
			get_tree().quit(1)
			return
		var draws: int = RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)
		print("saved %s, draw calls %d" % [shot[0], draws])
	map.queue_free()
	camera.queue_free()
	await get_tree().process_frame
	get_tree().quit()


func _attach_flashlight(camera: Camera3D) -> void:
	var player: Node = (load("res://systems/player/player.tscn") as PackedScene).instantiate()
	var light: SpotLight3D = player.get_node("Head/RecoilPivot/Camera3D/Flashlight") as SpotLight3D
	light.owner = null
	light.reparent(camera, false)
	light.visible = true
	player.free()
