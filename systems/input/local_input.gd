## Turns this machine's keyboard and mouse into InputFrames for one player.
## Mouse movement is gathered between ticks and handed over once per tick.
class_name LocalInput
extends Node

## Actions read as one-tick presses from input events.
const PRESS_BITS: Dictionary[StringName, int] = {
	&"weapon_next": InputFrame.NEXT_WEAPON,
	&"weapon_prev": InputFrame.PREV_WEAPON,
	&"weapon_slot_1": InputFrame.SLOT_1,
	&"weapon_slot_2": InputFrame.SLOT_2,
	&"weapon_slot_3": InputFrame.SLOT_3,
	&"melee": InputFrame.MELEE,
	&"field_ability": InputFrame.FIELD_ABILITY,
}

var mouse_sensitivity: float = 0.0022
var invert_y: bool = false
## Look scale at full aim, from the ADS sensitivity setting.
var ads_multiplier: float = 0.8

var enabled: bool = true
## Set by the owner each tick; scales look while aiming.
var sensitivity_scale: float = 1.0

var _look_accum: Vector2 = Vector2.ZERO
var _pressed: int = 0
var _input_dialog: Window
var _dismissed_buttons: int = 0
var _crouch_on: bool = false
var _ads_on: bool = false
var _sprint_on: bool = false
## Accessibility hold or toggle per action; crouch toggles by default (its original behaviour).
var _toggles: Dictionary[StringName, bool] = {&"ads": false, &"sprint": false, &"crouch": true}


func _ready() -> void:
	_update_controls()
	_update_toggles()
	Settings.changed.connect(_on_settings_changed)


func _update_controls() -> void:
	mouse_sensitivity = Settings.get_value(&"aim", &"mouse_sensitivity")
	invert_y = Settings.get_value(&"aim", &"invert_y")
	ads_multiplier = Settings.get_value(&"aim", &"ads_sensitivity_multiplier")


func _update_toggles() -> void:
	for action: StringName in _toggles:
		_toggles[action] = Settings.get_value(&"accessibility", StringName("toggle_" + action))
	_clear_toggles()


func _clear_toggles() -> void:
	_crouch_on = false
	_ads_on = false
	_sprint_on = false


func _on_settings_changed(section: StringName, _key: StringName, _value: Variant) -> void:
	if section == &"aim":
		_update_controls()
	elif section == &"accessibility":
		_update_toggles()


## Exclusive in-match dialogs also own held actions, which Godot polls outside GUI event dispatch.
func block_for_dialog(dialog: Window) -> void:
	_input_dialog = dialog
	dialog.tree_exiting.connect(_dialog_closed.bind(dialog), CONNECT_ONE_SHOT)


func _dialog_closed(dialog: Window) -> void:
	if _input_dialog != dialog:
		return
	_input_dialog = null
	_clear_toggles()
	_pressed = 0
	_look_accum = Vector2.ZERO
	var actions: int = (
		InputFrame.FIRE | InputFrame.ALT_FIRE | InputFrame.ADS | InputFrame.LETHAL | InputFrame.INTERACT_HELD
	)
	_dismissed_buttons = (_held_buttons() & actions) | _just_pressed_buttons()


## The HUD may tick before the player. Read current revive intent through the same dialog filter.
func interact_held() -> bool:
	return (
		enabled
		and _input_dialog == null
		and (_dismissed_buttons & InputFrame.INTERACT_HELD) == 0
		and Input.is_action_pressed(&"interact")
	)


func _unhandled_input(event: InputEvent) -> void:
	if not enabled or _input_dialog != null:
		return
	var motion: InputEventMouseMotion = event as InputEventMouseMotion
	if motion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		_look_accum += motion.relative
		return
	for action: StringName in PRESS_BITS:
		if event.is_action_pressed(action):
			_pressed |= PRESS_BITS[action]
	if event.is_action_pressed(&"ads"):
		_ads_on = not _ads_on
		_sprint_on = false
	if event.is_action_pressed(&"sprint"):
		_sprint_on = not _sprint_on
	if event.is_action_pressed(&"crouch"):
		_sprint_on = false
		_crouch_on = not _crouch_on
	elif event.is_action_pressed(&"sprint") or event.is_action_pressed(&"jump"):
		_crouch_on = false


## Builds the frame for this tick and clears the accumulators.
func sample(tick: int) -> InputFrame:
	var f: InputFrame = InputFrame.new()
	f.tick = tick
	if not enabled or UI.top() != &"" or _input_dialog != null:
		_look_accum = Vector2.ZERO
		_pressed = 0
		_clear_toggles()
		return f
	f.move = Input.get_vector(&"move_left", &"move_right", &"move_forward", &"move_back")
	if f.move.y > -0.4:  # Toggle sprint ends when the player stops running forward.
		_sprint_on = false
	f.look = _look_accum * mouse_sensitivity * sensitivity_scale
	if invert_y:
		f.look.y = -f.look.y
	_look_accum = Vector2.ZERO
	var buttons: int = _pressed | _held_buttons() | _just_pressed_buttons()
	_pressed = 0
	_dismissed_buttons &= buttons
	f.buttons = buttons & ~_dismissed_buttons
	return f


func _just_pressed_buttons() -> int:
	var b: int = 0
	if Input.is_action_just_pressed(&"jump"):
		b |= InputFrame.JUMP
	if Input.is_action_just_pressed(&"reload"):
		b |= InputFrame.RELOAD
	if Input.is_action_just_pressed(&"interact"):
		b |= InputFrame.INTERACT
	return b


func _held_buttons() -> int:
	var b: int = 0
	if Input.is_action_pressed(&"alt_fire"):
		b |= InputFrame.ALT_FIRE
	if Input.is_action_pressed(&"fire"):
		b |= InputFrame.FIRE
	if Input.is_action_pressed(&"interact"):
		b |= InputFrame.INTERACT_HELD
	if Input.is_action_pressed(&"lethal"):
		b |= InputFrame.LETHAL
	if _active(&"ads", _ads_on):
		b |= InputFrame.ADS
	if _active(&"sprint", _sprint_on):
		b |= InputFrame.SPRINT
	# Toggle crouch: a press flips it, a sprint or jump press stands up.
	if _active(&"crouch", _crouch_on):
		b |= InputFrame.CROUCH
	return b


## In toggle mode the flipped state counts; in hold mode the key must be down.
func _active(action: StringName, toggled_on: bool) -> bool:
	return toggled_on if _toggles[action] else Input.is_action_pressed(action)
