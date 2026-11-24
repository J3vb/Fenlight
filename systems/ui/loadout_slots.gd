## The nine loadout slot buttons in two columns beside the character turntable, with their gamepad focus.
class_name LoadoutSlots
extends HBoxContainer

## Armour in body order on the left; guns and small gear on the right.
const LEFT: Array[StringName] = [&"headgear", &"vest", &"gloves", &"backpack", &"boots"]
const RIGHT: Array[StringName] = [&"primary", &"sidearm", &"charm", &"implant"]

## LEFT then RIGHT, one button per slot.
var buttons: Array[Button] = []


func _ready() -> void:
	var armour: VBoxContainer = $ArmourSlots
	var kit: VBoxContainer = $KitSlots
	for slot: StringName in LEFT + RIGHT:
		var button: Button = Button.new()
		button.set_meta("slot", slot)
		button.custom_minimum_size = Vector2(124, 0)
		button.size_flags_vertical = Control.SIZE_EXPAND_FILL
		button.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		button.vertical_icon_alignment = VERTICAL_ALIGNMENT_TOP
		button.clip_text = true
		button.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		button.add_theme_font_size_override("font_size", 16)
		(armour if LEFT.has(slot) else kit).add_child(button)
		buttons.append(button)


func slot_of(button: Button) -> StringName:
	return StringName(button.get_meta("slot", &""))


func label(button: Button, item_name: String) -> void:
	var slot: StringName = slot_of(button)
	var heading: String = "Primary · stored" if slot == &"primary" else String(slot).capitalize()
	button.text = "%s\n%s" % [heading, item_name]
	if slot == &"primary":
		button.tooltip_text = "Stored only. This Primary cannot be claimed during a run in this build."


## The right-column slot a stash row's first cell steps left to.
func beside_stash(row: int) -> Button:
	return buttons[LEFT.size() + mini(row, RIGHT.size() - 1)]


func wire_focus(stash: Array[Button], columns: int, above: Control) -> void:
	var left: Array[Button] = buttons.slice(0, LEFT.size())
	var right: Array[Button] = buttons.slice(LEFT.size())
	for column: Array[Button] in [left, right]:
		for index: int in column.size():
			var button: Button = column[index]
			button.focus_neighbor_top = button.get_path_to(above if index == 0 else column[index - 1])
			var below: Button = stash[0] if index == column.size() - 1 else column[index + 1]
			button.focus_neighbor_bottom = button.get_path_to(below)
	for index: int in left.size():
		left[index].focus_neighbor_right = left[index].get_path_to(right[mini(index, right.size() - 1)])
	for index: int in right.size():
		right[index].focus_neighbor_left = right[index].get_path_to(left[index])
		right[index].focus_neighbor_right = right[index].get_path_to(stash[index * columns])
