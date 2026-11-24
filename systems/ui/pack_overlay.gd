## Quick Pack inspection over the live HUD; mouse look stops while movement continues.
class_name PackOverlay
extends Control

const TOOLTIP: PackedScene = preload("res://systems/ui/item_tooltip.tscn")
const CHARACTER: PackedScene = preload("res://systems/ui/pack_character.tscn")

var service: LootService
var stash_hint: Label
var count: Label
var panel: PanelContainer
var slots: Array[Button] = []
var tooltip: ItemTooltip
var character: PackCharacter
var feed: Label
var equip_button: Button
var drop_button: Button
var close_button: Button
var _feed_left: float = 0.0
var _selected: int = 0
var _previous_items: int = 0


func _ready() -> void:
	theme = preload("res://systems/ui/theme.tres")
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	count = Label.new()
	count.position = Vector2(48, -190)
	count.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)
	count.position = Vector2(48, size.y - 190)
	add_child(count)
	feed = Label.new()
	feed.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	feed.position = Vector2(size.x * 0.38, size.y - 150)
	add_child(feed)
	_build_panel()
	var background: StyleBoxFlat = StyleBoxFlat.new()
	background.bg_color = Color("0b1014", 0.97)
	background.content_margin_left = 24
	background.content_margin_right = 24
	background.content_margin_top = 64
	background.content_margin_bottom = 24
	panel.add_theme_stylebox_override("panel", background)
	resized.connect(_layout)
	Settings.changed.connect(_on_setting_changed)
	_layout()


func setup(loot: LootService) -> void:
	if loot == null:
		return
	service = loot
	character.setup(loot)
	service.pack.changed.connect(_refresh)
	_refresh()


func _build_panel() -> void:
	panel = PanelContainer.new()
	panel.hide()
	add_child(panel)
	var box: VBoxContainer = VBoxContainer.new()
	box.add_theme_constant_override("separation", 16)
	panel.add_child(box)
	var title: Label = Label.new()
	title.text = "Pack · 6 slots"
	title.add_theme_font_size_override("font_size", 36)
	box.add_child(title)
	stash_hint = Label.new()
	stash_hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(stash_hint)
	character = CHARACTER.instantiate() as PackCharacter
	character.slot_selected.connect(_show_worn)
	box.add_child(character)
	var picked: Label = Label.new()
	picked.text = "Picked up this run"
	box.add_child(picked)
	var grid: GridContainer = GridContainer.new()
	grid.columns = 3
	box.add_child(grid)
	for index: int in Pack.CAPACITY:
		slots.append(_slot_button(index))
		grid.add_child(slots[index])
	var spacer: Control = Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	box.add_child(spacer)
	var actions: HBoxContainer = HBoxContainer.new()
	box.add_child(actions)
	equip_button = Button.new()
	equip_button.pressed.connect(_equip)
	actions.add_child(equip_button)
	drop_button = Button.new()
	drop_button.pressed.connect(_drop)
	actions.add_child(drop_button)
	close_button = Button.new()
	close_button.pressed.connect(set_open.bind(false))
	actions.add_child(close_button)
	_update_key_labels()
	tooltip = TOOLTIP.instantiate() as ItemTooltip
	tooltip.hide()
	add_child(tooltip)


func _slot_button(index: int) -> Button:
	var button: Button = Button.new()
	button.custom_minimum_size = Vector2(180, 90)
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	button.expand_icon = true
	button.add_theme_constant_override("icon_max_width", 72)
	button.pressed.connect(_select.bind(index))
	button.focus_entered.connect(_select.bind(index))
	return button


func _update_key_labels() -> void:
	_update_equip_label()
	drop_button.text = "%s · Drop" % Settings.key_name(&"pack_drop")
	close_button.text = "%s · Close" % Settings.key_name(&"pack_toggle")


## Gear is worn; guns go into your hands.
func _update_equip_label() -> void:
	var gear: bool = false
	if service and _selected < service.pack.items.size():
		gear = Inventory.is_gear(service.pack.items[_selected])
	equip_button.text = "%s · %s" % [Settings.key_name(&"pack_equip"), "Wear" if gear else "Into hands"]


func _on_setting_changed(section: StringName, _key_name: StringName, _value: Variant) -> void:
	if section != &"bindings":
		return
	_update_key_labels()
	if service:
		_refresh()


func _layout() -> void:
	count.position = Vector2(48, size.y - 190)
	feed.position = Vector2(size.x * 0.38, size.y - 150)
	panel.position = Vector2.ZERO
	panel.size = Vector2(size.x * 0.5, size.y)
	tooltip.position = Vector2(size.x * 0.5 + 16, size.y * 0.14)
	tooltip.size = Vector2(size.x * 0.45, 0)


func _refresh() -> void:
	var items: Array[Dictionary] = service.pack.items
	if service.session and service.session.profile:
		var free: int = service.session.profile.free_stash_slots()
		stash_hint.text = (
			"Stash · %d reserved for this Pack · %d still free" % [items.size(), maxi(free - items.size(), 0)]
		)
	else:
		stash_hint.text = "The match keeps running."
	if panel.visible:
		character.refresh()
	count.text = "Pack %d / 6 [%s]" % [items.size(), Settings.key_name(&"pack_toggle")]
	if items.size() > _previous_items:
		var item: Dictionary = items.back()
		feed.text = "%s %s" % [String(item.get("rar", "common")).capitalize(), LootDrop.item_name(item)]
		feed.modulate = _colour(item)
		_feed_left = 4.0
	_previous_items = items.size()
	for index: int in slots.size():
		var item: Dictionary = items[index] if index < items.size() else {}
		var rarity: String = item.get("rar", "common")
		var rank: int = maxi(ItemRoller.RARITIES.find(StringName(rarity)), 0)
		slots[index].text = (
			(
				"%s\n%s %s · %d"
				% [LootDrop.item_name(item), ItemTooltip.SHAPES[rank], rarity.capitalize(), item.get("ilvl", 1)]
			)
			if not item.is_empty()
			else "Empty"
		)
		var style: StyleBoxFlat = StyleBoxFlat.new()
		style.bg_color = Color("121a20", 0.94)
		style.set_border_width_all(1)
		style.border_color = _colour(item) if not item.is_empty() else Color("2c3b44")
		slots[index].add_theme_stylebox_override("normal", style)
		slots[index].add_theme_color_override("font_color", _colour(item))
		slots[index].icon = ItemTooltip.icon_for(item)
	_select(mini(_selected, maxi(items.size() - 1, 0)))


## An unknown rarity (a save from a newer build) shows as common.
static func _colour(item: Dictionary) -> Color:
	var rarity: StringName = StringName(item.get("rar", "common"))
	if not Content.has(&"loot", rarity):
		rarity = ItemRoller.RARITIES[0]
	return (Content.get_item(&"loot", rarity) as RarityData).colour


func _select(index: int) -> void:
	_selected = index
	var items: Array[Dictionary] = service.pack.items
	var item: Dictionary = items[index] if index < items.size() else {}
	var gear: bool = Inventory.is_gear(item)
	tooltip.show_item(item, character.worn(Inventory.slot_for(item)) if gear else {})
	tooltip.set_comparing(gear)
	_update_equip_label()


func _show_worn(item: Dictionary) -> void:
	tooltip.show_item(item)
	tooltip.set_comparing(false)


func set_open(open: bool) -> void:
	panel.visible = open
	tooltip.visible = open
	character.set_rendering(open)
	mouse_filter = Control.MOUSE_FILTER_STOP if open else Control.MOUSE_FILTER_IGNORE
	UI.hold_mouse(self, open)
	if open:
		Input.action_release(&"fire")
		Input.action_release(&"ads")
		character.refresh()
		slots[_selected].grab_focus()


func _input(event: InputEvent) -> void:
	if service == null or not is_instance_valid(service.player):
		return
	if panel.visible and event is InputEventMouseButton:
		Input.action_release(&"fire")
		Input.action_release(&"ads")
	# In co-op the tree never pauses, so a pushed screen (Pause, Settings) owns the keys instead.
	if service.session.is_over or get_tree().paused or UI.top() != &"":
		if panel.visible:
			set_open(false)
		return
	var key_press: bool = event is InputEventKey and not event.echo
	var click: InputEventMouseButton = event as InputEventMouseButton
	# Left clicks on the open Pack belong to its buttons, whatever is bound to them.
	var shortcut_click: bool = click != null and not (panel.visible and click.button_index == MOUSE_BUTTON_LEFT)
	if (key_press or shortcut_click) and event.pressed:
		_on_action_event(event)
	elif panel.visible and event is InputEventMouseMotion:
		get_viewport().set_input_as_handled()


func _on_action_event(event: InputEvent) -> void:
	if event.is_action_pressed(&"pack_toggle"):
		set_open(not panel.visible)
	elif not panel.visible:
		return
	elif event.is_action_pressed(&"pause"):
		set_open(false)
	elif event.is_action_pressed(&"pack_drop"):
		_drop()
	elif event.is_action_pressed(&"pack_equip"):
		_equip()
	else:
		return
	get_viewport().set_input_as_handled()


func _process(delta: float) -> void:
	_feed_left = maxf(_feed_left - delta, 0.0)
	feed.modulate.a = minf(_feed_left, 1.0)
	if panel.visible and service and service.session.is_over:
		set_open(false)


func _drop() -> void:
	var item: Dictionary = service.pack.remove(_selected)
	if item.is_empty():
		return
	service._receive_drop(item, service.player.global_position - service.player.global_basis.z)


## Only asks; LootService equips in its next physics tick.
func _equip() -> void:
	var items: Array[Dictionary] = service.pack.items
	if _selected < items.size():
		service.request_equip(str(items[_selected].get("uid", "")))
