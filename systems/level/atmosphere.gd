## Root of a map's atmosphere scene (cosmetic lights, particles, fog). It sits
## directly under the Level and swaps two groups with the power: "after_power"
## nodes (steam, hums) show once the power is on, "before_power" nodes hide;
## sound players inside those nodes start and stop with them.
## Monitor screens anywhere under the Level (any mesh using MONITOR_SCREEN, like
## the props' "Screen" surfaces) get their "powered" instance uniform set too.
## Reading Level.power_on at ready covers late joiners in co-op.
class_name Atmosphere
extends Node3D

const AFTER_POWER: StringName = &"after_power"
const BEFORE_POWER: StringName = &"before_power"
const MAINS_LIGHT: StringName = &"mains_light"
const EMERGENCY_LIGHT: StringName = &"emergency_light"
const MONITOR_SCREEN: Material = preload("res://systems/effects/monitor_screen.tres")

var powered: bool = false
var _blackout: bool = false
var _mains_lights: Array[Node3D] = []
var _emergency_lights: Array[Node3D] = []
var _after: Array[Node3D] = []
var _before: Array[Node3D] = []
var _screens: Array[GeometryInstance3D] = []
var _after_sounds: Array[AudioStreamPlayer3D] = []
var _before_sounds: Array[AudioStreamPlayer3D] = []


func _ready() -> void:
	for node: Node in find_children("*", "Node3D", true, false):
		if node.is_in_group(MAINS_LIGHT):
			_mains_lights.append(node as Node3D)
		elif node.is_in_group(EMERGENCY_LIGHT):
			_emergency_lights.append(node as Node3D)
		elif node.is_in_group(AFTER_POWER):
			_after.append(node as Node3D)
			_collect_sounds(node, _after_sounds)
		elif node.is_in_group(BEFORE_POWER):
			_before.append(node as Node3D)
			_collect_sounds(node, _before_sounds)
	Events.blackout_started.connect(_set_blackout.bind(true).unbind(1))
	Events.blackout_ended.connect(_set_blackout.bind(false).unbind(1))
	var level: Level = get_parent() as Level
	var scan_root: Node = self
	if level:
		scan_root = level
	_find_screens(scan_root)
	set_powered(level != null and level.power_on)
	if level and not level.power_on:
		level.power_turned_on.connect(set_powered.bind(true), CONNECT_ONE_SHOT)


func set_powered(on: bool) -> void:
	powered = on
	_refresh_lights()
	for node: Node3D in _after:
		node.visible = on
	for node: Node3D in _before:
		node.visible = not on
	for sound: AudioStreamPlayer3D in _after_sounds:
		sound.playing = on
	for sound: AudioStreamPlayer3D in _before_sounds:
		sound.playing = not on
	for screen: GeometryInstance3D in _screens:
		screen.set_instance_shader_parameter(&"powered", 1.0 if on else 0.0)


func _set_blackout(dark: bool) -> void:
	_blackout = dark
	_refresh_lights()


func _refresh_lights() -> void:
	for light: Node3D in _mains_lights:
		light.visible = powered and not _blackout
	for light: Node3D in _emergency_lights:
		light.visible = not _blackout


func screens() -> Array[GeometryInstance3D]:
	return _screens


func _collect_sounds(root: Node, into: Array[AudioStreamPlayer3D]) -> void:
	for node: Node in root.find_children("*", "AudioStreamPlayer3D", true, false):
		into.append(node as AudioStreamPlayer3D)


func _find_screens(root: Node) -> void:
	for node: Node in root.find_children("*", "MeshInstance3D", true, false):
		var mesh: MeshInstance3D = node as MeshInstance3D
		if mesh.material_override == MONITOR_SCREEN:
			_screens.append(mesh)
			continue
		var count: int = mesh.mesh.get_surface_count() if mesh.mesh else 0
		for surface: int in count:
			if mesh.get_active_material(surface) == MONITOR_SCREEN:
				_screens.append(mesh)
				break
