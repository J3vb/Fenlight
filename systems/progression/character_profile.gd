## One local character. Keeps unknown save fields and refuses to replace unreadable saves.
class_name CharacterProfile
extends RefCounted

const STABLE_DIRECTORY: String = "user://characters/"
## Test tags, main builds, the editor and tests save here so they never touch stable saves.
const TEST_DIRECTORY: String = "user://characters-test/"
const STASH_SIZE: int = 60
const NAME_MAX: int = 16
const DEFAULT_NAME: String = "Survivor"
## Save and network order. Screens keep their own display order.
const SLOTS: Array[StringName] = [
	&"primary", &"sidearm", &"vest", &"charm", &"implant", &"headgear", &"gloves", &"backpack", &"boots"
]
const GEAR_SLOTS: Array[StringName] = [&"vest", &"charm", &"implant", &"headgear", &"gloves", &"backpack", &"boots"]
const XP_RULES: XpRules = preload("res://content/progression/xp_rules.tres")

var id: StringName = &""
var display_name: String = DEFAULT_NAME
var total_xp: int = 0
var skill_ranks: Dictionary = {}
var stash: Array[Dictionary] = []
var loadout: Dictionary = {}
## Best run per map (the level folder name): {"round": int, "kills": int}.
var best_runs: Dictionary = {}
## The picked field ability id; empty brings the highest one the level unlocked.
var field_ability: String = ""
var level: int:
	get:
		return XP_RULES.level_for_total_xp(total_xp)

## True when the file was written by a newer game version; it stays untouched.
var saved_by_newer_version: bool = false

var _unknown: Dictionary = {}
var _can_save: bool = true


func _init() -> void:
	for slot: StringName in SLOTS:
		loadout[String(slot)] = {}
	for _slot: int in STASH_SIZE:
		stash.append({})


func free_stash_slots() -> int:
	return stash.count({})


func to_dict() -> Dictionary:
	var data: Dictionary = _unknown.duplicate(true)
	data["id"] = String(id)
	data["display_name"] = display_name
	data["total_xp"] = total_xp
	data["skill_ranks"] = skill_ranks.duplicate(true)
	data["stash"] = stash.duplicate(true)
	data["loadout"] = loadout.duplicate(true)
	data["best_runs"] = best_runs.duplicate(true)
	data["field_ability"] = field_ability
	return data


static func from_dict(data: Dictionary) -> CharacterProfile:
	var profile: CharacterProfile = CharacterProfile.new()
	profile.id = StringName(data.get("id", ""))
	profile.display_name = clean_name(str(data.get("display_name", DEFAULT_NAME)))
	profile.total_xp = int(data.get("total_xp", 0))
	profile.skill_ranks = data.get("skill_ranks", {}).duplicate(true)
	var saved_stash: Array = data.get("stash", [])
	for slot: int in mini(saved_stash.size(), STASH_SIZE):
		if saved_stash[slot] is Dictionary:
			profile.stash[slot] = saved_stash[slot].duplicate(true)
	var saved_loadout: Variant = data.get("loadout", {})
	if saved_loadout is Dictionary:
		for slot: String in profile.loadout:
			if saved_loadout.get(slot) is Dictionary:
				profile.loadout[slot] = saved_loadout[slot].duplicate(true)
	var saved_best: Variant = data.get("best_runs", {})
	if saved_best is Dictionary:
		profile.best_runs = saved_best.duplicate(true)
	var saved_ability: Variant = data.get("field_ability", "")
	profile.field_ability = saved_ability if saved_ability is String else ""
	profile._unknown = data.duplicate(true)
	for key: String in [
		"id", "display_name", "total_xp", "skill_ranks", "stash", "loadout", "best_runs", "field_ability"
	]:
		profile._unknown.erase(key)
	return profile


## A typed name cut to what every screen can show: Latin letters, digits, single
## spaces and - _ . ' up to NAME_MAX. Nothing left gives the default name.
static func clean_name(text: String) -> String:
	var kept: String = RegEx.create_from_string("[^\\p{Latin}0-9 _.'\\-]").sub(text, "", true)
	var cleaned: String = RegEx.create_from_string(" +").sub(kept, " ", true).strip_edges()
	cleaned = cleaned.left(NAME_MAX).strip_edges()
	return cleaned if not cleaned.is_empty() else DEFAULT_NAME


## Where characters are saved for this build. Stable releases use the stable
## folder; every other build uses the test folder, copied once from stable.
static func directory() -> String:
	if Build.is_stable():
		return STABLE_DIRECTORY
	prepare_test_directory(STABLE_DIRECTORY, TEST_DIRECTORY)
	return TEST_DIRECTORY


## Creates test_dir as a copy of stable_dir's files, only when test_dir is missing.
static func prepare_test_directory(stable_dir: String, test_dir: String) -> void:
	var test_path: String = ProjectSettings.globalize_path(test_dir)
	if DirAccess.dir_exists_absolute(test_path):
		return
	DirAccess.make_dir_recursive_absolute(test_path)
	var stable_path: String = ProjectSettings.globalize_path(stable_dir)
	if not DirAccess.dir_exists_absolute(stable_path):
		return
	for file: String in DirAccess.get_files_at(stable_path):
		DirAccess.copy_absolute(stable_path.path_join(file), test_path.path_join(file))


static func load_or_create(profile_id: StringName) -> CharacterProfile:
	var profile: CharacterProfile = CharacterProfile.new()
	profile.id = profile_id
	var path: String = directory() + String(profile_id) + ".json"
	if not FileAccess.file_exists(path):
		return profile
	var saved_version: int = SaveFile.saved_version(path)
	if saved_version > SaveFile.CURRENT_VERSION:
		profile._can_save = false
		profile.saved_by_newer_version = true
		Log.warn(&"save", &"profile_newer", {"id": String(profile_id), "path": path, "version": saved_version})
		return profile
	var data: Dictionary = SaveFile.read(path)
	var xp: Variant = data.get("total_xp", 0)
	var valid: bool = (
		not data.is_empty()
		and data.get("id", String(profile_id)) is String
		and data.get("display_name", "Survivor") is String
		and data.get("skill_ranks", {}) is Dictionary
		and _valid_inventory(data)
		and (xp is int or xp is float)
	)
	if valid:
		valid = is_finite(float(xp)) and float(xp) >= 0.0 and float(xp) == float(int(xp))
	if not valid:
		profile._can_save = false
		Log.warn(&"progression", &"profile_unreadable", {"id": String(profile_id), "path": path})
		return profile
	profile = from_dict(data)
	profile.id = profile_id
	return profile


static func _valid_inventory(data: Dictionary) -> bool:
	var saved_stash: Variant = data.get("stash", [])
	var saved_loadout: Variant = data.get("loadout", {})
	if saved_loadout is Array and saved_loadout.is_empty():
		saved_loadout = {}
	if not saved_stash is Array or not saved_loadout is Dictionary:
		return false
	if saved_stash.size() > STASH_SIZE:
		return false
	for item: Variant in saved_stash:
		if item != null and not item is Dictionary:
			return false
	for slot: StringName in SLOTS:
		var item: Variant = saved_loadout.get(String(slot))
		if item != null and not item is Dictionary:
			return false
	return true


## Keeps the highest round per map (more kills breaks a tie). Saves and
## returns true when this run is a new best.
func record_run(map: String, stats: Dictionary) -> bool:
	var run_round: int = int(stats.get("round", 0))
	var run_kills: int = int(stats.get("kills", 0))
	var best: Variant = best_runs.get(map, {})
	var best_round: int = int(best.get("round", 0)) if best is Dictionary else 0
	var best_kills: int = int(best.get("kills", 0)) if best is Dictionary else 0
	if run_round < best_round or (run_round == best_round and run_kills <= best_kills):
		return false
	best_runs[map] = {"round": run_round, "kills": run_kills}
	save()
	return true


func save() -> Error:
	if not _can_save:
		return ERR_UNAVAILABLE
	var folder: String = directory()
	var path: String = folder + String(id) + ".json"
	var error: Error = DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(folder))
	if error == OK:
		error = SaveFile.write(path, to_dict())
	if error != OK:
		Log.warn(&"progression", &"profile_save_failed", {"id": String(id), "path": path, "error": error})
	return error
