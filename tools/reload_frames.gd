## Renders first-person reload key frames for a look check: screenshots/reload/<gun>_<kind>_<t>.png.
##   xvfb-run -s "-screen 0 1280x720x24" godot --path . --rendering-driver opengl3 res://tools/reload_frames.tscn
##   -- --guns=rifle_ar,kestrel_smg --old (old = the dip from before F-85)
## --clip renders whole reloads at 30 fps in real time instead: screenshots/reload/clip/<gun>_<kind>/0000.png.
extends Node

const PLAYER: PackedScene = preload("res://systems/player/player.tscn")
const STAGE: Script = preload("res://tools/lineup_stage.gd")
const LOOK: String = "res://levels/looks/halcyon_interior.tres"
const TACTICAL: Array[float] = [0.0, 0.12, 0.22, 0.3, 0.42, 0.6, 0.7, 0.77, 0.9]
const EMPTY: Array[float] = [0.2, 0.4, 0.52, 0.66, 0.76, 0.9]


func _ready() -> void:
	var args: Dictionary[String, String] = {}
	for arg: String in OS.get_cmdline_user_args():
		var parts: PackedStringArray = arg.trim_prefix("--").split("=")
		args[parts[0]] = parts[1] if parts.size() > 1 else "1"
	var guns: PackedStringArray = args.get("guns", "rifle_ar,kestrel_smg,talon_dmr").split(",")
	var stage: Node3D = STAGE.build(LOOK)
	add_child(stage)
	var wall: MeshInstance3D = MeshInstance3D.new()
	var plane: PlaneMesh = PlaneMesh.new()
	plane.size = Vector2(8, 8)
	wall.mesh = plane
	wall.rotation.x = PI / 2.0
	wall.position = Vector3(0, 1.5, -3)
	stage.add_child(wall)
	STAGE.light(stage, Vector3(0.6, 2.2, 0.6), 2.0, Color("#E8F6F2"), 6.0)
	STAGE.light(stage, Vector3(-0.8, 1.2, -0.4), 1.2, Color("#CDEEE8"), 6.0)
	if args.has("clip"):
		await _clips(guns, args.has("old"))
	else:
		await _render(guns, args.has("old"))
	get_tree().quit()


func _render(guns: PackedStringArray, old: bool) -> void:
	for id: String in guns:
		var player: Player = PLAYER.instantiate() as Player
		add_child(player)
		player.set_physics_process(false)
		player.weapons.set_process(false)
		var weapon: Weapon = player.weapons.give(Content.weapon(StringName(id)))
		weapon.set_process(false)
		player.weapons.arm_view.set_process(false)
		if old:
			weapon.pose.motion = null
		for empty: bool in [false, true]:
			for t: float in EMPTY if empty else TACTICAL:
				weapon.state = Weapon.State.RELOADING
				weapon._empty_reload = empty
				weapon._reload_duration = 1.0
				weapon._first_round_duration = 1.0
				weapon._reload_timer = 1.0 - t
				weapon.pose.update(1.0)
				weapon.reset_physics_interpolation()
				player.weapons.arm_view.update_pose()
				var kind: String = ("old_" if old else "") + ("empty" if empty else "tactical")
				await STAGE.save(get_tree(), "res://screenshots/reload/%s_%s_%03d.png" % [id, kind, roundi(t * 100)])
		player.queue_free()
		await get_tree().process_frame


func _clips(guns: PackedStringArray, old: bool) -> void:
	for id: String in guns:
		for empty: bool in [false, true]:
			var player: Player = PLAYER.instantiate() as Player
			add_child(player)
			player.set_physics_process(false)
			player.weapons.set_process(false)
			var weapon: Weapon = player.weapons.give(Content.weapon(StringName(id)))
			weapon.set_process(false)
			player.weapons.arm_view.set_process(false)
			if old:
				weapon.pose.motion = null
			weapon.instance.ammo_in_mag = 0 if empty else maxi(weapon.data.magazine_size - 3, 1)
			weapon.instance.ammo_reserve = 999
			var kind: String = ("old_" if old else "") + ("empty" if empty else "tactical")
			await _clip(player, "res://screenshots/reload/clip/%s_%s/" % [id, kind])
			player.queue_free()
			await get_tree().process_frame


func _clip(player: Player, folder: String) -> void:
	var weapon: Weapon = player.weapons.current
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(folder))
	var dt: float = 1.0 / 30.0
	var frame: int = 0
	var tail: int = 12
	for _i: int in 8:
		weapon.pose.update(1.0)
		weapon.reset_physics_interpolation()
	weapon.start_reload()
	while tail > 0:
		weapon.tick(dt)
		weapon.pose.update(dt)
		player.weapons.arm_view.update_pose()
		weapon.reset_physics_interpolation()
		await get_tree().process_frame
		await get_tree().process_frame
		get_tree().root.get_texture().get_image().save_png(folder + "%04d.png" % frame)
		frame += 1
		if not weapon.is_reloading():
			tail -= 1
