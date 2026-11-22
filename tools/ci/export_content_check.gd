## Run with an exported build: checks that content data survives export (choice rows keep their
## options, screens keep their tips, gun viewmodels keep their muzzle flash, scope lens and red dot).
## Exported .tres lost typed packed arrays once (2026-11-19); exported viewmodels lost every node
## added inside the gun model once (2026-11-22, v0.1.2: black scope, no red dot, no muzzle flash).
extends SceneTree


func _init() -> void:
	var problems: PackedStringArray = []
	for path: String in _tres("res://content/settings"):
		var row: Resource = load(path)
		if row.get("kind") == &"choice" and (row.get("options") as Array).is_empty():
			problems.append("%s: choice row has no options" % path)
	for path: String in _tres("res://content/screens"):
		var screen: Resource = load(path)
		if not str(screen.get("loading_screen")).is_empty() and (screen.get("tips") as Array).is_empty():
			problems.append("%s: no loading tips" % path)
	problems.append_array(_viewmodel_problems())
	for line: String in problems:
		printerr(line)
	print("Export content check: %s" % ("OK" if problems.is_empty() else "%d problems" % problems.size()))
	quit(0 if problems.is_empty() else 1)


## Each gun's sight and flash nodes sit inside the imported model; export must keep them.
func _viewmodel_problems() -> PackedStringArray:
	var out: PackedStringArray = []
	var needs: Dictionary[String, String] = {
		"Muzzle": "FlashMesh", "ScopeLensMount": "ScopeLens", "ReticleMount": "Reticle"
	}
	for path: String in _tres("res://content/weapons"):
		var data: Resource = load(path)
		var scene: PackedScene = data.get("viewmodel_scene") as PackedScene
		if scene == null:
			continue
		var viewmodel: Node = scene.instantiate()
		for mount: String in needs:
			var holder: Node = viewmodel.find_child(mount, true, false)
			if holder and holder.get_node_or_null(needs[mount]) == null:
				out.append("%s: viewmodel lost %s/%s" % [path, mount, needs[mount]])
		viewmodel.free()
	return out


func _tres(folder: String) -> PackedStringArray:
	var out: PackedStringArray = []
	for file: String in DirAccess.get_files_at(folder):
		var clean: String = file.trim_suffix(".remap")
		if clean.get_extension() == "tres":
			out.append(folder.path_join(clean))
	return out
