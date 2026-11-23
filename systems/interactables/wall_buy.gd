## A gun on the wall. Buys the gun at its WeaponData cost, or refills its ammo
## for half that when the player already owns it (a fixed price once Reforged).
## Decides from the owner's facts about its guns; the gun or ammo is a grant.
## A once_per_player rack (the secret Cryo Lance) gives its gun free, once per
## player, and sells no ammo; who took it syncs to clients. The gun hangs on
## the rack at Board/GunMount (its WeaponData.world_model).
class_name WallBuy
extends Interactable

@export var weapon: WeaponData
@export var reforged_ammo_cost: int = 4000
@export var once_per_player: bool = false

## net ids of players who took the gun from a once_per_player rack.
var taken_by: Array[int] = []


func _ready() -> void:
	super()
	var mount: Node3D = get_node_or_null(^"Board/GunMount") as Node3D
	if mount and weapon and weapon.world_model:
		mount.add_child(weapon.world_model.instantiate())


func get_prompt(player: Player) -> String:
	var owned: Weapon = _owned(player)
	if once_per_player:
		return "" if owned or taken_by.has(player.net_id) else "Take %s [F]" % weapon.display_name
	if owned:
		return "Buy ammo for %s [F]  %d" % [owned.data.display_name, ammo_cost(owned.data.id)]
	if player.weapons.weapons.size() >= player.weapons.max_slots and player.weapons.current:
		return "Swap %s for %s [F]  %d" % [player.weapons.current.data.display_name, weapon.display_name, weapon.cost]
	return "Buy %s [F]  %d" % [weapon.display_name, weapon.cost]


func ammo_cost(owned_id: StringName) -> int:
	return int(weapon.cost * 0.5) if owned_id == weapon.id else reforged_ammo_cost


func interact(player: Player, facts: Dictionary = {}) -> void:
	if facts.is_empty():
		facts = owner_facts(player)
	var owned: StringName = facts.owned
	if once_per_player:
		_take(player, owned, facts.slot)
	elif owned == &"":
		if _pay(player, weapon.cost):
			_grant(player, InteractionSync.Grant.GIVE, weapon, &"", facts.slot)
	elif not facts.full and _pay(player, ammo_cost(owned)):
		_grant(player, InteractionSync.Grant.REFILL, weapon, owned, facts.slot)


func _take(player: Player, owned: StringName, slot: int) -> void:
	if owned != &"" or taken_by.has(player.net_id):
		return
	taken_by.append(player.net_id)
	state_changed.emit()
	_grant(player, InteractionSync.Grant.GIVE, weapon, &"", slot)


func net_state() -> Dictionary:
	return {"taken_by": taken_by.duplicate()} if once_per_player else {}


func apply_net_state(state: Dictionary) -> void:
	taken_by.assign(state.get("taken_by", []))


## owned: held id of this gun or its Reforged tier (or empty); slot: that gun, or the gun in hand.
func owner_facts(player: Player) -> Dictionary:
	var owned: Weapon = _owned(player)
	var holder: WeaponHolder = player.weapons
	return {
		"owned": owned.data.id if owned else &"",
		"slot": holder.weapons.find(owned if owned else holder.current),
		"full": owned != null and owned.instance.ammo_reserve >= owned.data.max_reserve,
	}


func check_facts(facts: Dictionary) -> bool:
	if not (facts.get("owned") is StringName and facts.get("slot") is int and facts.get("full") is bool):
		return false
	var owned: StringName = facts.owned
	return owned == &"" or owned == weapon.id or (weapon.upgraded != null and owned == weapon.upgraded.id)


func _owned(player: Player) -> Weapon:
	for owned: Weapon in player.weapons.weapons:
		if owned.data.id == weapon.id or (weapon.upgraded != null and owned.data.id == weapon.upgraded.id):
			return owned
	return null
