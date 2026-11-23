## A personal, silent interactable. Only its owner can move the item into their Pack.
class_name LootDrop
extends Interactable

const LIFETIME: float = 60.0
const HEIGHTS: Array[float] = [0.0, 1.0, 1.5, 2.0, 2.5, 3.0]
## Emission above 1 so the ring and pillar bloom; unshaded drops ignored emission (play-test: too dim).
const GLOW: float = 4.0
const LAND_FLASH: float = 6.0
const STEADY_LIGHT: float = 1.2

## One glow material per rarity colour, shared by every drop.
static var _glows: Dictionary[Color, StandardMaterial3D] = {}

var item: Dictionary = {}
var pack: Pack
var player: Player

@onready var lifetime: Timer = $Lifetime


func _ready() -> void:
	super()
	lifetime.start(LIFETIME)
	lifetime.timeout.connect(queue_free)
	var rarity: StringName = StringName(item.get("rar", "common"))
	var data: RarityData = Content.get_item(&"loot", rarity) as RarityData
	var rank: int = maxi(ItemRoller.RARITIES.find(rarity), 0)
	var material: StandardMaterial3D = glow_material(data.colour)
	($Ring as MeshInstance3D).material_override = material
	var pillar: MeshInstance3D = $Pillar
	pillar.visible = rank > 0
	pillar.scale.y = maxf(HEIGHTS[rank], 0.01)
	pillar.position.y = HEIGHTS[rank] / 2.0
	pillar.material_override = material
	_light_up(data.colour)


static func glow_material(colour: Color) -> StandardMaterial3D:
	if not _glows.has(colour):
		var material: StandardMaterial3D = StandardMaterial3D.new()
		material.albedo_color = colour
		material.emission_enabled = true
		material.emission = colour
		material.emission_energy_multiplier = GLOW
		_glows[colour] = material
	return _glows[colour]


## Shared meshes, for ShaderWarmUp to draw once at match start.
static func warm_up_meshes() -> Array[Mesh]:
	var mesh: BoxMesh = BoxMesh.new()
	mesh.material = glow_material(Color.WHITE)
	return [mesh]


## A rarity-coloured light that flashes when the item lands, then settles to a steady glow.
func _light_up(colour: Color) -> void:
	var light: OmniLight3D = $Glow as OmniLight3D
	light.light_color = colour
	light.light_energy = LAND_FLASH
	create_tween().tween_property(light, ^"light_energy", STEADY_LIGHT, 1.2).set_ease(Tween.EASE_OUT)


func get_prompt(viewer: Player) -> String:
	if viewer != player or not _can_reach(viewer):
		return ""
	if pack.is_full():
		return "Pack full"
	return (
		"%s · %s · iLvl %d [F]" % [item_name(item), String(item.get("rar", "common")).capitalize(), item.get("ilvl", 1)]
	)


func interact(viewer: Player, _facts: Dictionary = {}) -> void:
	if viewer != player or is_queued_for_deletion() or not _can_reach(viewer):
		return
	if pack.is_full():
		return
	var profile: CharacterProfile = viewer.session.profile if viewer.session else null
	if profile and pack.items.size() >= profile.free_stash_slots():
		if not has_node(^"StashExchange"):
			var exchange: StashExchange = StashExchange.new()
			exchange.name = "StashExchange"
			add_child(exchange)
			exchange.offer(self, profile)
		return
	if pack.add(item):
		viewer.focus = null
		queue_free()


func is_local() -> bool:
	return true


func _can_reach(viewer: Player) -> bool:
	return (
		is_instance_valid(viewer)
		and viewer.is_alive()
		and not viewer.is_downed
		and viewer.global_position.distance_to(global_position) <= viewer.interact_range
		and (viewer.session == null or not viewer.session.is_over)
		and (viewer.session == null or viewer.session.match_end == null or not viewer.session.match_end.xp_banked)
	)


static func item_name(data: Dictionary) -> String:
	var legendary: LegendaryData = ItemInstance.legendary_of(data)
	if legendary:
		return legendary.display_name
	var base: StringName = StringName(data.get("base", ""))
	if Content.has(&"weapons", base):
		return Content.weapon(base).display_name
	if Content.has(&"loot", base):
		var gear: GearBaseData = Content.get_item(&"loot", base) as GearBaseData
		if gear:
			return gear.display_name
	return String(base).capitalize()
