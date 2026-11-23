## Fixed zombie captures in the unchanged gear booth, plus silhouette and fog checks.
## Run zombie_review.tscn with -- <output-directory> for before or after captures.
## Append --hands for close-ups of both hands in rest, walk and both attack extremes.
extends Node3D

const TYPES: Array[String] = ["shambler", "shambler_guard", "bloater", "glower", "crawler"]
const LINEUP: Array[String] = ["shambler", "crawler", "bloater"]
const LOOK: String = "res://levels/looks/halcyon_interior.tres"
const POSES: Array[String] = ["front", "booth", "walk", "windup", "strike"]
const WARMUP_FRAMES: int = 12

var _out: String = "res://screenshots/zombie_review"
var _actors: Node3D
var _camera: Camera3D
var _environment: Environment
var _ground: MeshInstance3D
var _caption: Label
var _booth: Node3D
var _hands_only: bool = false


func _ready() -> void:
	var arguments: PackedStringArray = OS.get_cmdline_user_args()
	if not arguments.is_empty():
		_out = arguments[0]
	_hands_only = "--hands" in arguments
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(_out))
	get_window().size = Vector2i(1600, 900)
	get_window().content_scale_size = Vector2i(1600, 900)
	physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF
	_setup_booth()
	_actors = Node3D.new()
	add_child(_actors)
	_run.call_deferred()


func _setup_booth() -> void:
	_booth = (load("res://tools/gear_booth.tscn") as PackedScene).instantiate() as Node3D
	# Reuse the booth's authored light/floor/environment without its player assembly.
	_booth.set_script(null)
	add_child(_booth)
	var world: WorldEnvironment = _booth.get_node("WorldEnvironment") as WorldEnvironment
	_environment = world.environment.duplicate() as Environment
	world.environment = _environment
	_ground = _booth.get_node("Floor") as MeshInstance3D
	_camera = _booth.get_node("Turntable/Camera3D") as Camera3D
	_caption = _booth.get_node("Caption/Label") as Label


func _clear() -> void:
	for child: Node in _actors.get_children():
		child.free()


func _place(kind: String, at: Vector3, angle: float = 0.0) -> ZombieRig:
	var rig: ZombieRig = ZombieRig.new()
	rig.model = load("res://assets/models/zombies/%s.glb" % kind) as PackedScene
	_actors.add_child(rig)
	rig.position = at
	# ZombieRig turns its model toward -Z; these review cameras stand on +Z.
	rig.rotation.y = PI + angle
	return rig


func _run() -> void:
	_environment.volumetric_fog_enabled = false
	for kind: String in TYPES:
		if _hands_only:
			await _hand_shots(kind)
		else:
			await _model_shots(kind)
	if not _hands_only:
		await _silhouettes()
		await _distances()
	get_tree().quit()


func _set_pose(rig: ZombieRig, kind: String, pose: String) -> void:
	if pose == "walk":
		rig.pose_walk(2.0, 0.5, PI / 13.0)
	elif pose == "windup":
		rig.pose_attack(1.0 if kind == "crawler" else ZombieRig.ATTACK_DRAW)
	elif pose == "strike":
		rig.pose_attack(2.0 if kind == "crawler" else 1.0)


func _model_shots(kind: String) -> void:
	for pose: String in POSES:
		_clear()
		var angle: float = 0.0 if pose == "front" else -0.5
		var rig: ZombieRig = _place(kind, Vector3.ZERO, angle)
		_set_pose(rig, kind, pose)
		_camera.fov = 40.0
		_camera.look_at_from_position(Vector3(0, 1.15, 3.2), Vector3(0, 0.85, 0))
		if pose == "windup":
			_camera.look_at_from_position(Vector3(0, 1.4, 4.4), Vector3(0, 1.25, 0))
		await _capture(kind + "_" + pose, kind + " | " + pose + " | gear booth / runtime rig")


func _hand_shots(kind: String) -> void:
	for pose: String in ["rest", "walk", "windup", "strike"]:
		_clear()
		var rig: ZombieRig = _place(kind, Vector3.ZERO)
		_set_pose(rig, kind, pose)
		await get_tree().process_frame
		var skeleton: Skeleton3D = rig.find_children("*", "Skeleton3D", true, false)[0] as Skeleton3D
		_camera.projection = Camera3D.PROJECTION_ORTHOGONAL
		_camera.size = 0.40
		for side: String in ["L", "R"]:
			var bone: int = skeleton.find_bone("hand_" + side)
			var frame: Transform3D = skeleton.global_transform * skeleton.get_bone_global_pose(bone)
			var target: Vector3 = frame.origin + frame.basis.y * 0.045
			var angle: float = 0.25 if side == "L" else -0.25
			_camera.look_at_from_position(target + Vector3(angle, 0.14, 0.6), target)
			await _capture(kind + "_hand_" + side + "_" + pose, kind + " | hand " + side + " | " + pose)


func _lineup() -> void:
	_clear()
	for index: int in LINEUP.size():
		_place(LINEUP[index], Vector3((index - 1) * 1.6, 0, 0))


func _silhouettes() -> void:
	_lineup()
	var black: StandardMaterial3D = StandardMaterial3D.new()
	black.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	black.albedo_color = Color.BLACK
	for node: Node in _actors.find_children("*", "MeshInstance3D", true, false):
		(node as MeshInstance3D).material_override = black
	_ground.visible = false
	_environment.background_color = Color("#CDEEE8")
	_camera.fov = 40.0
	_camera.look_at_from_position(Vector3(0, 1.1, 6.5), Vector3(0, 0.85, 0))
	await _capture("silhouettes", "SHAMBLER / CRAWLER / BLOATER | black-only silhouettes")
	_ground.visible = true
	_environment.background_color = Color("#0A1416")


func _distances() -> void:
	_lineup()
	_environment = (load(LOOK) as Environment).duplicate() as Environment
	(_booth.get_node("WorldEnvironment") as WorldEnvironment).environment = _environment
	(_booth.get_node("Key") as DirectionalLight3D).light_color = Color("#CDEEE8")
	# Compatibility has no volumetric fog: expose the substitute in every caption.
	var compatibility: bool = RenderingServer.get_current_rendering_method() == "gl_compatibility"
	var fog_label: String = "volumetric fog 0.03"
	if compatibility:
		_environment.fog_enabled = true
		_environment.fog_density = 0.03
		_environment.fog_light_color = Color(0.6, 0.7, 0.7)
		_environment.fog_light_energy = 0.2
		fog_label = "regular-fog preview 0.03 (Compatibility)"
	else:
		_environment.volumetric_fog_enabled = true
	_camera.fov = rad_to_deg(2.0 * atan(tan(deg_to_rad(110.0) / 2.0) * 9.0 / 16.0))
	for distance: int in [2, 10, 30]:
		_camera.look_at_from_position(Vector3(0, 1.62, distance), Vector3(0, 1.62, 0))
		await _capture("distance_%dm" % distance, "%d m | horizontal FOV 110 | %s" % [distance, fog_label])
	_clear()
	for index: int in 24:
		var at: Vector3 = Vector3((index % 6 - 2.5) * 1.2, 0, -floori(index / 6.0) * 1.5)
		var rig: ZombieRig = _place(LINEUP[index % LINEUP.size()], at)
		rig.pose_walk(2.0, 0.5, (index % 4 + 1) * PI / 13.0)
	for distance: int in [10, 30]:
		_camera.look_at_from_position(Vector3(0, 1.62, distance), Vector3(0, 1.62, 0))
		await _capture("horde_%dm" % distance, "24 zombies | front row %d m | hFOV 110 | %s" % [distance, fog_label])


func _capture(file_name: String, caption: String) -> void:
	_caption.text = caption
	for _frame: int in WARMUP_FRAMES:
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var path: String = _out.path_join(file_name + ".png")
	var result: Error = get_viewport().get_texture().get_image().save_png(path)
	if result != OK:
		push_error("Could not save zombie review capture: " + path)
		get_tree().quit(1)
	print("saved ", path)
