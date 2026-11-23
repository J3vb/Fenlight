## Applies equipped gear and the spawn Sidearm, equips item guns, and runs their on-hit effects on the server.
class_name ItemLoadout
extends RefCounted


static func apply(player: Player, loadout: Dictionary) -> void:
	var gear: Array[Dictionary] = worn_gear(loadout)
	player.loadout_sync.gear = gear
	player.equip_gear(gear)
	refit_guns(player, true)
	var sidearm: Variant = loadout.get("sidearm")
	if not sidearm is Dictionary:
		return
	var base: StringName = StringName(sidearm.get("base", ""))
	if not Content.has(&"weapons", base):
		return
	var base_data: WeaponData = Content.weapon(base)
	if not (base_data.loot_tags.has(&"pistol") or base_data.loot_tags.has(&"sidearm")):
		return
	var starter: int = _pistol_slot(player)
	var replacing: Weapon = player.weapons.weapons[starter] if starter >= 0 else null
	equip_weapon(player, ItemInstance.new(sidearm), null, replacing)


## Mid-run swap: new gear stats without a heal, then held guns pick up the new numbers.
static func apply_gear(player: Player, loadout: Dictionary) -> void:
	var gear: Array[Dictionary] = worn_gear(loadout)
	player.loadout_sync.gear = gear
	player.equip_gear(gear, false)
	refit_guns(player)


static func worn_gear(loadout: Dictionary) -> Array[Dictionary]:
	var gear: Array[Dictionary] = []
	for slot: StringName in CharacterProfile.GEAR_SLOTS:
		var equipped: Variant = loadout.get(String(slot))
		if equipped is Dictionary and not equipped.is_empty():
			gear.append(equipped)
	return gear


## Rebuilds each held gun's numbers in place: same gun in hand, ammo kept (capped), no new pickup.
## Item guns refit from their item; other guns get the player's damage, recoil and reserve stats.
## fresh (spawn): reserve restarts at the refitted starting reserve.
static func refit_guns(player: Player, fresh: bool = false) -> void:
	for weapon: Weapon in player.weapons.weapons:
		if weapon.item:
			var base: WeaponData = Content.weapon(StringName(weapon.item.data.get("base", "")))
			weapon.instance.data = weapon.item.weapon_data(base, player.stats)
		elif Content.has(&"weapons", weapon.data.id):
			weapon.instance.data = ItemInstance.fit_player_gun(Content.weapon(weapon.data.id), player.stats)
		else:
			continue
		if fresh:
			weapon.instance.ammo_reserve = weapon.instance.data.starting_reserve
		weapon.instance.ammo_in_mag = mini(weapon.instance.ammo_in_mag, weapon.instance.data.magazine_size)
		weapon.instance.ammo_reserve = mini(weapon.instance.ammo_reserve, weapon.instance.data.max_reserve)
		weapon.ammo_changed.emit(weapon.instance.ammo_in_mag, weapon.instance.ammo_reserve)


## Gives an item gun (or swaps it in for replacing), carries its run ammo and records it as an item gun.
static func equip_weapon(
	player: Player, item: ItemInstance, carried: WeaponInstance, replacing: Weapon = null
) -> Weapon:
	var base: WeaponData = Content.weapon(StringName(item.data.get("base", "")))
	var data: WeaponData = item.weapon_data(base, player.stats)
	if replacing:
		player.weapons.equip(player.weapons.weapons.find(replacing))
	var weapon: Weapon = (
		player.weapons.replace(replacing, data, false) if replacing else player.weapons.give(data, false)
	)
	if carried:
		weapon.instance.ammo_in_mag = mini(carried.ammo_in_mag, data.magazine_size)
		weapon.instance.ammo_reserve = mini(carried.ammo_reserve, data.max_reserve)
	weapon.ammo_changed.emit(weapon.instance.ammo_in_mag, weapon.instance.ammo_reserve)
	weapon.item = item
	player.item_guns[str(item.data.get("uid", ""))] = item
	return weapon


static func _pistol_slot(player: Player) -> int:
	for index: int in player.weapons.weapons.size():
		if (
			player.weapons.weapons[index].data.loot_tags.has(&"pistol")
			or player.weapons.weapons[index].data.loot_tags.has(&"sidearm")
		):
			return index
	return -1


## Server: an item gun's on-hit effects for one applied hit.
static func apply_hit(player: Player, item: ItemInstance, info: DamageInfo) -> void:
	player.wallet.earn(roundi(item.stats.value(&"points_per_hit", 0.0, player.stats)))
	player.health.heal(item.stats.value(&"leech", 0.0, player.stats))
	LegendaryTraits.bloodline(player, item, info)
