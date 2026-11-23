## LoadoutSlots on the Character screen: nine slots in two columns, their gamepad focus and equipping a new slot.
extends GutTest

const SCREEN: PackedScene = preload("res://systems/ui/character_screen.tscn")

var screen: CharacterScreen
var profile: CharacterProfile


func before_each() -> void:
	profile = CharacterProfile.new()
	profile.id = &"test_loadout_slots"
	screen = SCREEN.instantiate() as CharacterScreen
	add_child_autofree(screen)
	screen.open(profile)


func test_nine_slots_show_armour_left_and_kit_right_with_slot_names() -> void:
	var order: Array[StringName] = []
	for button: Button in screen.slots.buttons:
		order.append(screen.slots.slot_of(button))
	assert_eq(
		order, [&"headgear", &"vest", &"gloves", &"backpack", &"boots", &"primary", &"sidearm", &"charm", &"implant"]
	)
	var sorted_order: PackedStringArray = PackedStringArray(order)
	var profile_slots: PackedStringArray = PackedStringArray(CharacterProfile.SLOTS)
	sorted_order.sort()
	profile_slots.sort()
	assert_eq(sorted_order, profile_slots, "Every save slot has exactly one button")
	assert_eq(_slot_button(&"headgear").get_parent().name, &"ArmourSlots")
	assert_eq(_slot_button(&"implant").get_parent().name, &"KitSlots")
	assert_eq(_slot_button(&"backpack").text, "Backpack\nEmpty")
	assert_string_contains(_slot_button(&"primary").text, "stored")


func test_gamepad_focus_moves_between_slot_columns_and_into_the_stash() -> void:
	var stash_first: Button = screen.stash_buttons[0]
	for slot: StringName in [&"boots", &"implant"]:
		var button: Button = _slot_button(slot)
		assert_eq(button.get_node(button.focus_neighbor_bottom), stash_first, "Down from %s" % slot)
	var headgear: Button = _slot_button(&"headgear")
	assert_eq(headgear.get_node(headgear.focus_neighbor_right), _slot_button(&"primary"))
	assert_eq(headgear.get_node(headgear.focus_neighbor_bottom), _slot_button(&"vest"))
	var boots: Button = _slot_button(&"boots")
	assert_eq(boots.get_node(boots.focus_neighbor_right), _slot_button(&"implant"))
	var charm: Button = _slot_button(&"charm")
	assert_eq(charm.get_node(charm.focus_neighbor_left), _slot_button(&"gloves"))
	assert_eq(charm.get_node(charm.focus_neighbor_right), screen.stash_buttons[2 * CharacterScreen.STASH_COLUMNS])
	var last_row: Button = screen.stash_buttons[CharacterProfile.STASH_SIZE - CharacterScreen.STASH_COLUMNS]
	assert_eq(last_row.get_node(last_row.focus_neighbor_left), _slot_button(&"implant"))


func test_equipping_a_backpack_updates_its_button_and_rebuilds_the_rig() -> void:
	var pack: Dictionary = _item("backpack_pack", "pack", "rare", 12)
	profile.stash[30] = pack
	screen.open(profile)
	screen.select_tab(&"field_gear")
	watch_signals(screen.rig)
	_stash_button(30).grab_focus()
	screen._input(_key(KEY_E))
	assert_eq(profile.loadout[&"backpack"], pack)
	var base: GearBaseData = Content.get_item(&"loot", &"backpack_pack") as GearBaseData
	assert_string_contains(_slot_button(&"backpack").text, base.display_name)
	assert_signal_emitted(screen.rig, "look_changed", "Equipping rebuilds the rig from the new loadout")
	_slot_button(&"backpack").grab_focus()
	screen._input(_key(KEY_E))
	assert_eq(profile.loadout[&"backpack"], {})
	assert_string_contains(_slot_button(&"backpack").text, "Empty")


func _slot_button(slot: StringName) -> Button:
	for button: Button in screen.slots.buttons:
		if screen.slots.slot_of(button) == slot:
			return button
	return null


func _stash_button(index: int) -> Button:
	for button: Button in screen.stash_buttons:
		if button.get_meta("stash_index", -1) == index:
			return button
	return null


func _item(base: String, uid: String, rarity: String, level: int) -> Dictionary:
	return {"v": 1, "uid": uid, "base": base, "rar": rarity, "ilvl": level, "aff": [], "imp": []}


func _key(code: Key) -> InputEventKey:
	var event: InputEventKey = InputEventKey.new()
	event.physical_keycode = code
	event.keycode = code
	event.pressed = true
	return event
