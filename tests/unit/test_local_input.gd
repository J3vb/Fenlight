## Hold or toggle for aim, sprint and crouch: toggles flip on press, holds follow the key, both clear when input stops.
extends GutTest

const PATH: String = "user://test_local_input.cfg"

var _local: LocalInput
var _old_path: String
var _old_values: Dictionary


func before_each() -> void:
	_old_path = Settings.config_path
	_old_values = Settings._values.duplicate(true)
	Settings.config_path = PATH
	Settings.reset_to_defaults()
	_local = LocalInput.new()
	add_child_autofree(_local)


func after_each() -> void:
	for action: StringName in [&"ads", &"sprint", &"crouch", &"move_forward"]:
		Input.action_release(action)
	Settings._values = _old_values
	Settings._apply_all()
	Settings.config_path = _old_path
	if FileAccess.file_exists(PATH):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(PATH))


func _press(action: StringName) -> void:
	var event: InputEventAction = InputEventAction.new()
	event.action = action
	event.pressed = true
	Input.action_press(action)
	_local._unhandled_input(event)


func test_toggle_aim_stays_aimed_after_release_and_drops_on_second_press() -> void:
	Settings.set_value(&"accessibility", &"toggle_ads", true)
	_press(&"ads")
	Input.action_release(&"ads")
	assert_true(_local.sample(1).has(InputFrame.ADS), "still aiming after release")
	assert_true(_local.sample(2).has(InputFrame.ADS))
	_press(&"ads")
	Input.action_release(&"ads")
	assert_false(_local.sample(3).has(InputFrame.ADS))


func test_hold_aim_is_unchanged() -> void:
	_press(&"ads")
	assert_true(_local.sample(1).has(InputFrame.ADS))
	Input.action_release(&"ads")
	assert_false(_local.sample(2).has(InputFrame.ADS), "hold mode stops on release")


func test_toggle_sprint_and_hold_crouch() -> void:
	Settings.set_value(&"accessibility", &"toggle_sprint", true)
	Settings.set_value(&"accessibility", &"toggle_crouch", false)
	Input.action_press(&"move_forward")
	_press(&"sprint")
	Input.action_release(&"sprint")
	assert_true(_local.sample(1).has(InputFrame.SPRINT))
	_press(&"crouch")
	assert_true(_local.sample(2).has(InputFrame.CROUCH))
	Input.action_release(&"crouch")
	assert_false(_local.sample(3).has(InputFrame.CROUCH), "hold crouch stops on release")


func test_crouch_toggles_by_default() -> void:
	_press(&"crouch")
	Input.action_release(&"crouch")
	assert_true(_local.sample(1).has(InputFrame.CROUCH))
	_press(&"jump")
	Input.action_release(&"jump")
	assert_false(_local.sample(2).has(InputFrame.CROUCH), "jump stands up")


func test_toggles_clear_when_input_is_disabled() -> void:
	Settings.set_value(&"accessibility", &"toggle_ads", true)
	_press(&"ads")
	Input.action_release(&"ads")
	_local.enabled = false
	_local.sample(1)
	_local.enabled = true
	assert_false(_local.sample(2).has(InputFrame.ADS), "death or match end drops a toggled aim")


func test_toggle_sprint_ends_when_running_stops_or_aiming() -> void:
	Settings.set_value(&"accessibility", &"toggle_sprint", true)
	Input.action_press(&"move_forward")
	_press(&"sprint")
	Input.action_release(&"sprint")
	assert_true(_local.sample(1).has(InputFrame.SPRINT))
	Input.action_release(&"move_forward")
	assert_false(_local.sample(2).has(InputFrame.SPRINT), "stopping ends the sprint")
	Input.action_press(&"move_forward")
	assert_false(_local.sample(3).has(InputFrame.SPRINT), "walking again does not sprint by itself")
	_press(&"sprint")
	assert_true(_local.sample(4).has(InputFrame.SPRINT))
	_press(&"ads")
	assert_false(_local.sample(5).has(InputFrame.SPRINT), "aiming ends the sprint")
	Input.action_release(&"move_forward")


func test_gameplay_actions_wait_for_the_dialog_and_its_held_click_to_clear() -> void:
	var dialog: ConfirmationDialog = ConfirmationDialog.new()
	add_child(dialog)
	_local.block_for_dialog(dialog)
	Input.action_press(&"fire")
	Input.action_press(&"lethal")
	Input.action_press(&"interact")
	assert_eq(_local.sample(1).buttons, 0)
	var action: InputEventAction = InputEventAction.new()
	action.action = &"melee"
	action.pressed = true
	_local._unhandled_input(action)
	dialog.free()
	Input.action_press(&"move_forward")
	Input.action_press(&"ads")
	var resumed: InputFrame = _local.sample(2)
	assert_lt(resumed.move.y, 0.0, "movement resumes with interact still held")
	assert_true(resumed.has(InputFrame.ADS), "fresh actions work immediately")
	assert_false(
		resumed.has(
			InputFrame.FIRE | InputFrame.LETHAL | InputFrame.INTERACT_HELD | InputFrame.INTERACT | InputFrame.MELEE
		)
	)
	Input.action_release(&"ads")
	Input.action_release(&"move_forward")
	Input.action_release(&"interact")
	Input.action_release(&"fire")
	Input.action_release(&"lethal")
	assert_eq(_local.sample(3).buttons, 0)
	await wait_physics_frames(2)
	assert_false(_local.sample(4).has(InputFrame.MELEE), "the queued melee press was discarded")
	Input.action_press(&"fire")
	assert_true(_local.sample(5).has(InputFrame.FIRE))
	Input.action_release(&"fire")
