## The local player chooses which item to give up before taking loot that would overflow their stash.
class_name StashExchange
extends ConfirmationDialog

var _drop: LootDrop
var _profile: CharacterProfile
var _choices: OptionButton = OptionButton.new()
var _detail: Label = Label.new()


func offer(drop: LootDrop, profile: CharacterProfile) -> void:
	_drop = drop
	_profile = profile
	theme = preload("res://systems/ui/theme.tres")
	title = "Choose what to keep"
	exclusive = true
	var box: VBoxContainer = VBoxContainer.new()
	add_child(box)
	var offer_label: Label = Label.new()
	offer_label.text = "Keep %s" % _describe(drop.item)
	box.add_child(offer_label)
	var bonuses: String = ItemTooltip.bonus_summary(drop.item)
	if not bonuses.is_empty():
		offer_label.text += "\n" + bonuses
	box.add_child(_choices)
	box.add_child(_detail)
	_choices.add_item("Choose an item to give up")
	_list_items(drop.pack.items, false)
	if not drop.pack.is_full():
		_list_items(profile.stash, true)
	_choices.item_selected.connect(_selected)
	_selected(0)
	ok_button_text = "Confirm exchange"
	confirmed.connect(_confirm)
	canceled.connect(queue_free)
	UI.hold_mouse(self, true)
	popup_centered()
	_choices.grab_focus()


func _list_items(items: Array[Dictionary], stored: bool) -> void:
	for index: int in items.size():
		var item: Dictionary = items[index]
		if item.is_empty():
			continue
		_choices.add_item("%s %d · %s" % ["Stash" if stored else "Pack", index + 1, _describe(item)])
		_choices.set_item_metadata(_choices.item_count - 1, {"stored": stored, "index": index, "item": item})


func _describe(item: Dictionary) -> String:
	return (
		"%s · %s · Lv %d" % [LootDrop.item_name(item), str(item.get("rar", "common")).capitalize(), item.get("ilvl", 1)]
	)


func _selected(index: int) -> void:
	get_ok_button().disabled = index == 0
	if index == 0:
		_detail.text = "Your Pack is full." if _drop.pack.is_full() else "Your stash has no unreserved space."
		return
	var choice: Dictionary = _choices.get_item_metadata(index)
	_detail.text = (
		"Permanently discard this item from your stash." if choice.stored else "Leave this Pack item on the ground."
	)
	var bonuses: String = ItemTooltip.bonus_summary(choice.item)
	if not bonuses.is_empty():
		_detail.text += "\n" + bonuses


func _confirm() -> void:
	if _choices.selected > 0 and _can_exchange():
		var choice: Dictionary = _choices.get_item_metadata(_choices.selected)
		_exchange(choice)
	queue_free()


func _exchange(choice: Dictionary) -> void:
	var pack: Pack = _drop.pack
	var index: int = choice.index
	if not pack.is_full() and pack.items.size() < _profile.free_stash_slots():
		_drop.interact(_drop.player)
		return
	if choice.stored:
		if _profile.stash[index] != choice.item or pack.is_full():
			return
		Inventory.remove(_profile, index)
		pack.add(_drop.item)
	else:
		var carried: Array[Dictionary] = pack.items
		if index >= carried.size() or carried[index] != choice.item:
			return
		pack.replace(index, _drop.item)
		_drop.player.session.loot._receive_drop(choice.item, _drop.global_position)
	_drop.player.focus = null
	_drop.queue_free()


func _can_exchange() -> bool:
	return is_instance_valid(_drop) and not _drop.is_queued_for_deletion() and _drop._can_reach(_drop.player)


func _process(_delta: float) -> void:
	if visible and not _can_exchange():
		queue_free()
