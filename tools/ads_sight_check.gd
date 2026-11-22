## Solo match render check of every gun with an optic: aims each one and saves the screen to
## user://ads_sight_check/<id>.png, printing the scope and reticle state and the centre pixel.
## Needs a GPU or software Vulkan and a display:
##   xvfb-run -a godot --path . --rendering-driver vulkan res://tools/ads_sight_check.tscn
extends Node

const GUNS: Array[String] = ["talon_dmr", "rifle_ar", "kestrel_smg", "brenner_trench", "corvid_338", "ironwood_50"]
const OUT: String = "user://ads_sight_check"


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	var session: GameSession = (
		(load("res://systems/game/game_session.tscn") as PackedScene).instantiate() as GameSession
	)
	session.rng_seed = 7
	add_child(session)
	await _seconds(8.0)
	var player: Player = session.get_players()[0]
	for id: String in GUNS:
		var weapon: Weapon = player.weapons.give(Content.weapon(StringName(id)))
		await _seconds(1.0)
		Input.action_press(&"ads")
		await _seconds(1.5)
		_report(id, weapon)
		Input.action_release(&"ads")
		await _seconds(0.5)
	get_tree().quit()


func _report(id: String, weapon: Weapon) -> void:
	var image: Image = get_viewport().get_texture().get_image()
	image.save_png("%s/%s.png" % [OUT, id])
	var centre: Color = image.get_pixel(image.get_width() / 2, image.get_height() / 2)
	print("%s ads=%.2f fov=%.1f centre=%s" % [id, weapon.ads_progress, get_viewport().get_camera_3d().fov, centre])
	for node: Node in get_tree().root.find_children("*", "MeshInstance3D", true, false):
		if node is ScopeLens:
			var lens: ScopeLens = node as ScopeLens
			print("  lens %s live=%s visible=%s" % [lens.get_path(), lens.is_rendering(), lens.is_visible_in_tree()])
		elif node.name == "Reticle":
			print("  reticle %s visible=%s" % [node.get_path(), (node as Node3D).is_visible_in_tree()])


func _seconds(t: float) -> void:
	await get_tree().create_timer(t).timeout
