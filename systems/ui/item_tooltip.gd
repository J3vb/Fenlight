## Shared item details, rolled bonuses and optional comparisons against an equipped item.
class_name ItemTooltip
extends PanelContainer

const DIM: Color = Color("8fa3a8")
const TEXT: Color = Color("e6ecec")
const BETTER: Color = Color("7fd6e0")
const WORSE: Color = Color("ff9f1c")
const SHAPES: Array[String] = ["●", "▲", "■", "◆", "⬟", "⚠"]
const STAT_NAMES: Array[String] = ["Damage", "Fire rate /m", "Magazine", "Handling"]
const STAT_LIMITS: Array[float] = [150.0, 1200.0, 100.0, 1.0]

static var _icons: Dictionary[StringName, Texture2D] = {}

var _item: Dictionary = {}
var _equipped: Dictionary = {}
var _comparing: bool = false

@onready var icon: TextureRect = $Box/Icon
@onready var item_name: Label = $Box/Name
@onready var rarity_label: Label = $Box/Identity/Rarity
@onready var level_label: Label = $Box/Identity/Level
@onready var stats: VBoxContainer = $Box/Stats
@onready var affixes: VBoxContainer = $Box/Affixes
@onready var comparison: Label = $Box/Comparison


func _ready() -> void:
	_refresh()


func show_item(item: Dictionary, equipped: Dictionary = {}) -> void:
	_item = item.duplicate(true)
	_equipped = equipped.duplicate(true)
	if is_node_ready():
		_refresh()


func set_comparing(enabled: bool) -> void:
	if _comparing == enabled:
		return
	_comparing = enabled
	if is_node_ready():
		_refresh()


func _refresh() -> void:
	for box: VBoxContainer in [stats, affixes]:
		for child: Node in box.get_children():
			child.free()
	_fill_header()
	_fill_stats()
	_add_trait()
	for line: Array in _item.get("aff", []):
		_add_affix(line, false)
	var implicit: Variant = _item.get("imp")
	if implicit is Array and not implicit.is_empty():
		_add_affix(implicit, true)
	comparison.text = "Hold Shift / X to compare"
	if _comparing:
		comparison.text = "Compared with %s (equipped)" % _display_name(_equipped)
		if _equipped.is_empty():
			comparison.text = "No item equipped in this slot"


## The rendered picture of the item's base (tools/render_item_icons.gd), or null for an empty or unknown item.
static func icon_for(item: Dictionary) -> Texture2D:
	var base: StringName = StringName(str(item.get("base", "")))
	if base == &"":
		return null
	if not _icons.has(base):
		var path: String = "res://assets/textures/ui/icons/%s.png" % base
		_icons[base] = load(path) as Texture2D if ResourceLoader.exists(path) else null
	return _icons[base]


func _fill_header() -> void:
	var rarity: StringName = StringName(_item.get("rar", "common"))
	var colour: Color = TEXT
	if Content.has(&"loot", rarity):
		var data: RarityData = Content.get_item(&"loot", rarity) as RarityData
		if data:
			colour = data.colour
	var border: StyleBoxFlat = get_theme_stylebox("panel").duplicate() as StyleBoxFlat
	border.border_color = colour if not _item.is_empty() else Color("2c3b44")
	add_theme_stylebox_override("panel", border)
	item_name.text = _display_name(_item) if not _item.is_empty() else "Select an item"
	icon.texture = icon_for(_item)
	icon.visible = icon.texture != null
	item_name.add_theme_color_override("font_color", colour)
	var rank: int = maxi(ItemRoller.RARITIES.find(rarity), 0)
	rarity_label.text = "%s %s %s" % [SHAPES[rank], String(rarity).capitalize(), "•".repeat(rank + 1)]
	rarity_label.add_theme_color_override("font_color", colour)
	rarity_label.visible = not _item.is_empty()
	level_label.text = "Item level %s" % _item.get("ilvl", 1) if not _item.is_empty() else ""


func _fill_stats() -> void:
	var values: Array[float] = _weapon_stats(_item)
	if values.is_empty():
		_fill_gear_slot()
		return
	var other: Array[float] = _weapon_stats(_equipped)
	for index: int in values.size():
		var row: HBoxContainer = HBoxContainer.new()
		var label: Label = Label.new()
		label.text = STAT_NAMES[index]
		label.custom_minimum_size.x = 135.0
		if index == 3:
			label.tooltip_text = "Aim-down-sights time in seconds. Lower is better."
		label.add_theme_constant_override("outline_size", 0)
		row.add_child(label)
		var bar: ProgressBar = ProgressBar.new()
		for key: String in ["background", "fill"]:
			var style: StyleBoxFlat = StyleBoxFlat.new()
			style.bg_color = Color("2c3b44") if key == "background" else TEXT
			bar.add_theme_stylebox_override(key, style)
		bar.show_percentage = false
		bar.max_value = STAT_LIMITS[index]
		bar.value = values[index]
		bar.custom_minimum_size = Vector2(50.0, 7.0)
		bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(bar)
		var value: Label = Label.new()
		value.theme_type_variation = &"LabelMono"
		value.custom_minimum_size.x = 80.0
		value.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		value.add_theme_constant_override("outline_size", 0)
		value.text = _number(values[index]) + (" s" if index == 3 else "")
		if _comparing and not other.is_empty():
			_mark_comparison(value, values[index], other[index], index == 3)
		row.add_child(value)
		stats.add_child(row)


func _fill_gear_slot() -> void:
	var gear: GearBaseData = _base(_item, &"loot") as GearBaseData
	var slot: StringName = &""
	if gear:
		slot = StringName(gear.slot)
	else:
		var visual: GearVisual = GearVisual.find(StringName(_item.get("base", "")))
		if visual:
			slot = visual.slot
	if not slot.is_empty():
		var label: Label = Label.new()
		label.text = "Slot: %s" % String(slot).capitalize()
		label.add_theme_constant_override("outline_size", 0)
		stats.add_child(label)


func _add_affix(line: Array, implicit: bool) -> void:
	var label: RichTextLabel = RichTextLabel.new()
	label.bbcode_enabled = true
	label.fit_content = true
	label.scroll_active = false
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var rolled: Dictionary = _rolled_affix(line, implicit, _item)
	if rolled.is_empty():
		label.text = "[color=#%s]Inactive bonus[/color]" % DIM.to_html(false)
	else:
		var affix: AffixData = rolled.data
		var text: String = affix.text.replace("{v}", _number(rolled.value))
		if _comparing and not _equipped.is_empty():
			var other: float = _equipped_affix_value(StringName(line[0]), implicit)
			text = _comparison_text(text, rolled.value, other)
		label.text = (
			"%s [color=#%s](%s-%s)[/color]" % [text, DIM.to_html(false), _number(rolled.low), _number(rolled.high)]
		)
	affixes.add_child(label)


## The Legendary trait: first line, in Legendary orange with a diamond, then its range.
func _add_trait() -> void:
	var legendary: LegendaryData = ItemInstance.legendary_of(_item)
	if legendary == null:
		return
	var label: RichTextLabel = RichTextLabel.new()
	label.name = "Trait"
	label.bbcode_enabled = true
	label.fit_content = true
	label.scroll_active = false
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var value: float = ItemRoller.trait_value(legendary, float(_item.trait[1]))
	var colour: Color = (Content.get_item(&"loot", &"legendary") as RarityData).colour
	var first: float = legendary.high if legendary.lower_is_better else legendary.low
	var last: float = legendary.low if legendary.lower_is_better else legendary.high
	label.text = (
		"[color=#%s]◆ %s[/color] [color=#%s](%s-%s)[/color]"
		% [
			colour.to_html(false),
			legendary.text.replace("{v}", _number(value)),
			DIM.to_html(false),
			_number(first),
			_number(last),
		]
	)
	affixes.add_child(label)


## Plain rolled bonuses for the compact picker used while a match is running.
static func bonus_summary(item: Dictionary) -> String:
	var parts: PackedStringArray = []
	var legendary: LegendaryData = ItemInstance.legendary_of(item)
	if legendary:
		parts.append(legendary.text.replace("{v}", _number(ItemRoller.trait_value(legendary, item.trait[1]))))
	var lines: Array = item.get("aff", []).duplicate()
	var implicit: Variant = item.get("imp")
	if implicit is Array and not implicit.is_empty():
		lines.append(implicit)
	for line: Array in lines:
		var rolled: Dictionary = _rolled_affix(line, line.size() == 2, item)
		if rolled.is_empty():
			parts.append("Inactive bonus")
		else:
			var affix: AffixData = rolled.data
			parts.append(affix.text.replace("{v}", _number(rolled.value)))
	return "\n".join(parts)


static func _rolled_affix(line: Array, implicit: bool, item: Dictionary) -> Dictionary:
	var required: int = 2 if implicit else 3
	if line.size() != required or not Content.has(&"loot", StringName(line[0])):
		return {}
	var data: AffixData = Content.get_item(&"loot", StringName(line[0])) as AffixData
	if data == null:
		return {}
	if implicit:
		var rarity: StringName = StringName(item.get("rar", "common"))
		if not data.rarity_ranges.has(rarity):
			return {}
		var limits: Vector2 = data.rarity_ranges[rarity]
		var value: float = snappedf(lerpf(limits.x, limits.y, float(line[1])), data.step)
		return {"data": data, "value": value, "low": limits.x, "high": limits.y}
	var tier: int = int(line[1])
	if tier < 1 or tier > data.tiers.size():
		return {}
	return {
		"data": data,
		"value": ItemRoller.affix_value(data.id, tier, float(line[2])),
		"low": data.tiers.front().low,
		"high": data.tiers.back().high,
	}


func _equipped_affix_value(id: StringName, implicit: bool) -> float:
	var lines: Array = _equipped.get("aff", [])
	if implicit:
		var ammo: Variant = _equipped.get("imp")
		lines = [ammo] if ammo is Array else []
	for line: Array in lines:
		if not line.is_empty() and StringName(line[0]) == id:
			var rolled: Dictionary = _rolled_affix(line, implicit, _equipped)
			return rolled.get("value", 0.0)
	return 0.0


func _mark_comparison(label: Label, value: float, other: float, lower_better: bool) -> void:
	if is_equal_approx(value, other):
		return
	var better: bool = value < other if lower_better else value > other
	label.text += " ↑" if better else " ↓"
	label.add_theme_color_override("font_color", BETTER if better else WORSE)


func _comparison_text(text: String, value: float, other: float) -> String:
	if is_equal_approx(value, other):
		return text
	return (
		"[color=#%s]%s %s[/color]"
		% [(BETTER if value > other else WORSE).to_html(false), text, "↑" if value > other else "↓"]
	)


func _weapon_stats(item: Dictionary) -> Array[float]:
	var weapon: WeaponData = _base(item, &"weapons") as WeaponData
	if weapon == null:
		return []
	var instance: ItemInstance = ItemInstance.new(item)
	var rolled: WeaponData = instance.weapon_data(weapon)
	var interval: float = instance.weapon_stat(&"fire_interval", weapon.get_fire_interval())
	return [
		rolled.damage,
		60.0 / interval,
		float(rolled.magazine_size),
		instance.weapon_stat(&"ads_time", weapon.ads_time),
	]


func _display_name(item: Dictionary) -> String:
	if _base(item, &"weapons") or _base(item, &"loot") is GearBaseData:
		return LootDrop.item_name(item)
	var visual: GearVisual = GearVisual.find(StringName(item.get("base", "")))
	return String(visual.id).capitalize() if visual else "Unknown item"


func _base(item: Dictionary, type: StringName) -> Resource:
	var id: StringName = StringName(item.get("base", ""))
	return Content.get_item(type, id) if Content.has(type, id) else null


static func _number(value: float) -> String:
	return ("%.2f" % value).trim_suffix("0").trim_suffix("0").trim_suffix(".")
