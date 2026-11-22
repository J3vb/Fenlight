## Server rolls personal loot; each owner alone presents drops and banks its Pack.
class_name LootService
extends Node

const DROP: PackedScene = preload("res://systems/loot/loot_drop.tscn")

var session: GameSession
var pack: Pack = Pack.new()
var player: Player
var taken: Array[Dictionary] = []
var lost: int = 0
## Test fixture override; negative uses the normal source chance.
var drop_chance_override: float = -1.0
var _banked: bool = false
var _queued_uid: String = ""
## Ammo left in each Pack gun this run, by uid, so re-equipping does not refill it.
var _run_weapons: Dictionary[String, WeaponInstance] = {}


func _init() -> void:
	name = "LootService"
	process_mode = Node.PROCESS_MODE_PAUSABLE


func _ready() -> void:
	Events.enemy_killed.connect(_on_enemy_killed)
	if multiplayer.is_server():
		Log.info(&"loot", &"seed_selected", {"seed": session.rng.seed})
		# Loads every loot base now, so the first drop mid-fight does not hitch (#181).
		eligible_bases(1, &"common")


func _physics_process(_delta: float) -> void:
	if _queued_uid.is_empty():
		return
	var uid: String = _queued_uid
	_queued_uid = ""
	_equip_from_pack(uid)


## The Pack overlay asks; the gun changes in the next physics tick.
func request_equip(uid: String) -> void:
	_queued_uid = uid


func _equip_from_pack(uid: String) -> void:
	if session.is_over or not is_instance_valid(player) or player.is_downed or not player.is_alive():
		return
	var index: int = _pack_index(uid)
	var item: Dictionary = pack.items[index] if index >= 0 else {}
	if Inventory.is_gear(item):
		_wear_from_pack(item, index)
		return
	if item.is_empty() or not Content.has(&"weapons", StringName(item.get("base", ""))):
		return
	for held: Weapon in player.weapons.weapons:
		if held.item and str(held.item.data.get("uid", "")) == uid:
			player.weapons.equip(player.weapons.weapons.find(held))
			return
	var weapon: Weapon = ItemLoadout.equip_weapon(player, ItemInstance.new(item), _run_weapons.get(uid))
	_run_weapons[uid] = weapon.instance
	player.loadout_sync.send_loadout()


func _pack_index(uid: String) -> int:
	var items: Array[Dictionary] = pack.items
	for index: int in items.size():
		if str(items[index].get("uid", "")) == uid:
			return index
	return -1


## The worn piece in that slot takes the item's Pack slot; the profile saves the swap when the run banks.
func _wear_from_pack(item: Dictionary, index: int) -> void:
	if _banked or session.profile == null:
		Log.warn(&"loot", &"gear_equip_refused", {"uid": item.get("uid"), "banked": _banked})
		return
	var slot: String = String(Inventory.slot_for(item))
	var worn: Dictionary = session.profile.loadout.get(slot, {})
	session.profile.loadout[slot] = item.duplicate(true)
	ItemLoadout.apply_gear(player, session.profile.loadout)
	pack.replace(index, worn)
	player.gear_rig.apply(LookBuilder.from_equipped(session.profile.loadout))
	player.loadout_sync.send_loadout()
	Log.info(&"loot", &"gear_worn", {"uid": item.get("uid"), "slot": slot})


func _on_enemy_killed(enemy: Node3D, info: DamageInfo) -> void:
	if not multiplayer.is_server() or session.is_over or session.match_end.xp_banked or info.attacker == null:
		return
	var zombie: Zombie = enemy as Zombie
	if zombie == null or zombie.data == null or not session.spawner.is_ancestor_of(zombie):
		return
	var at: Vector3 = zombie.drop_point()
	for owner_player: Player in session.get_players():
		var owner_id: int = owner_player.get_multiplayer_authority()
		var level: int = session.handshake.player_level(owner_id)
		var gear_luck: float = player_luck(owner_player, 1)
		var luck: float = clampf(gear_luck + maxf(session.director.round_number - 10, 0) * 0.02, 0, 1)
		var item: Dictionary = roll_drop(zombie.data, level, luck)
		if not item.is_empty():
			send_drop(owner_id, item, at)


static func player_luck(owner_player: Player, round_number: int) -> float:
	var luck: float = maxf(round_number - 10, 0) * 0.02
	for modifier: Modifier in owner_player.stats.modifiers:
		if modifier.stat == &"loot_luck":
			luck += modifier.value
	return clampf(luck, 0.0, 1.0)


func _round() -> int:
	return clampi(session.director.round_number, 1, 50)


func roll_drop(enemy: EnemyData, character_level: int, luck: float = 0.0) -> Dictionary:
	var chance: float = drop_chance(enemy, session.director.round_number)
	if drop_chance_override >= 0.0:
		chance = drop_chance_override
	if session.rng.randf() >= chance:
		return {}
	var rarity: StringName = _rarity(enemy, luck)
	var pool: Array[Resource] = eligible_bases(character_level, rarity)
	if pool.is_empty():
		return {}
	var total: float = 0.0
	for base: Resource in pool:
		total += _weight(base)
	var choice: float = session.rng.randf() * total
	var selected: Resource = pool.back()
	for base: Resource in pool:
		choice -= _weight(base)
		if choice < 0.0:
			selected = base
			break
	if selected is GearBaseData:
		return ItemRoller.roll_gear(session.rng, selected, rarity, _round())
	if rarity == &"prototype":
		return _prototype(selected as WeaponData)
	return ItemRoller.roll_weapon(session.rng, selected, rarity, _round(), character_level)


func _rarity(enemy: EnemyData, luck: float) -> StringName:
	var rarity: StringName = ItemRoller.roll_rarity(session.rng, false, luck)
	var floor_rank: int = ItemRoller.RARITIES.find(enemy.loot_min_rarity)
	while ItemRoller.RARITIES.find(rarity) < floor_rank:
		rarity = ItemRoller.roll_rarity(session.rng, false, luck)
	return rarity


## The enemy's own chance when it sets one, else the zombie round curve.
static func drop_chance(enemy: EnemyData, round_number: int) -> float:
	if enemy.loot_drop_chance >= 0.0:
		return enemy.loot_drop_chance
	return minf(0.015 + maxi(round_number, 1) * 0.001, 0.05)


static func eligible_bases(character_level: int, rarity: StringName) -> Array[Resource]:
	var pool: Array[Resource] = []
	for id: StringName in Content.sorted_ids(&"weapons"):
		var weapon: WeaponData = Content.weapon(id)
		if String(id).ends_with("_reforged") or weapon.loot_tags.has(&"prototype") != (rarity == &"prototype"):
			continue
		if character_level < int(weapon.get_meta(&"unlock_level", 1)) or _weight(weapon) <= 0.0:
			continue
		var floor_rank: int = ItemRoller.RARITIES.find(weapon.get_meta(&"min_rarity", &"common"))
		if ItemRoller.RARITIES.find(rarity) >= floor_rank:
			pool.append(weapon)
	if rarity == &"prototype":
		return pool
	for id: StringName in Content.sorted_ids(&"loot"):
		var gear: GearBaseData = Content.get_item(&"loot", id) as GearBaseData
		if gear and gear.unlock_level <= character_level and gear.drop_weight > 0.0:
			pool.append(gear)
	if rarity == &"legendary":
		return _with_legendary(pool)
	return pool


static func _with_legendary(pool: Array[Resource]) -> Array[Resource]:
	var kept: Array[Resource] = []
	for base: Resource in pool:
		var id: StringName = (base as WeaponData).id if base is WeaponData else (base as GearBaseData).id
		if not ItemRoller.legendaries_for(id).is_empty():
			kept.append(base)
	return kept


static func _weight(base: Resource) -> float:
	if base is GearBaseData:
		return (base as GearBaseData).drop_weight
	return float(base.get_meta(&"drop_weight", (base as WeaponData).crate_weight * 100.0))


func _prototype(base: WeaponData) -> Dictionary:
	return {
		"v": 1,
		"uid":
		"%08x-%08x-%08x-%08x" % [session.rng.randi(), session.rng.randi(), session.rng.randi(), session.rng.randi()],
		"base": String(base.id),
		"rar": "prototype",
		"ilvl": _round(),
		"aff": [],
		"imp": ["fabricator", 1.0],
		"trait": null,
		"set": null,
		"craft": {},
	}


func send_drop(owner_id: int, item: Dictionary, at: Vector3) -> void:
	if not multiplayer.is_server():
		return
	if owner_id == multiplayer.get_unique_id():
		_receive_drop(item, at)
	elif multiplayer.get_peers().has(owner_id):
		_receive_drop.rpc_id(owner_id, item, at)


@rpc("authority", "call_remote", "reliable")
func _receive_drop(item: Dictionary, at: Vector3) -> void:
	if _banked or session.is_over or not session.has_local_player or not is_instance_valid(player):
		return
	var drop: LootDrop = DROP.instantiate() as LootDrop
	drop.item = item.duplicate(true)
	drop.pack = pack
	drop.player = player
	add_child(drop)
	drop.global_position = at
	Events.loot_dropped.emit(player, drop.item)
	Log.info(&"loot", &"drop_received", {"uid": item.get("uid"), "base": item.get("base")})


## Called alongside XP banking before the owning profile saves. Dedicated servers never call this.
func bank(profile: CharacterProfile) -> void:
	if _banked:
		return
	_banked = true
	taken = pack.items
	for item: Dictionary in taken:
		if Inventory.add_to_stash(profile, item) < 0:
			lost += 1
			Log.info(&"loot", &"stash_item_lost", {"uid": item.get("uid"), "base": item.get("base")})
	while not pack.items.is_empty():
		pack.remove(0)


func results() -> Dictionary:
	return {"loot": taken.duplicate(true), "loot_lost": lost}
