## Pays players for hits and kills and is the only way to spend points.
## Lives in the GameSession. Hit and kill points double while Payday runs.
class_name Economy
extends Node

const PAYDAY_MULTIPLIER: int = 2

@export var rules: EconomyRules

## Set by the GameSession; tells whether Payday runs.
var drops: PowerUpDrops

var _repair_points: Dictionary[Player, int] = {}
## Each player's unpaid fraction of a point, so a small points_earned bonus is not lost to rounding.
var _point_fraction: Dictionary[Player, float] = {}
var _local_player: Player


func _ready() -> void:
	Events.player_spawned.connect(_on_player_spawned)
	Events.enemy_damaged.connect(_on_enemy_damaged)
	Events.enemy_killed.connect(_on_enemy_killed)
	Events.round_ended.connect(_on_round_ended)


func try_spend(player: Player, cost: int) -> bool:
	if not multiplayer.is_server() or player.wallet.points < cost:
		return false
	player.wallet.add(-cost)
	return true


## Pays a barrier repair, up to the per-round cap.
func pay_repair(player: Player) -> void:
	if not multiplayer.is_server():
		return
	var earned: int = _repair_points.get(player, 0)
	var amount: int = mini(_boosted(player, rules.points_per_plank), rules.max_repair_points_per_round - earned)
	if amount <= 0:
		return
	_repair_points[player] = earned + amount
	player.wallet.earn(amount)


func _on_player_spawned(player: Player) -> void:
	if player.multiplayer != multiplayer:
		return
	if multiplayer.is_server():
		player.wallet.points_changed.connect(_sync_points.bind(player))
		player.wallet.set_points(rules.starting_points)
	elif player.is_multiplayer_authority():
		_local_player = player
		_request_points.rpc_id(1)


func _on_enemy_damaged(_enemy: Node3D, info: DamageInfo) -> void:
	var player: Player = info.attacker as Player
	if multiplayer.is_server() and player and player.multiplayer == multiplayer:
		player.wallet.earn(_boosted(player, rules.points_per_hit * _multiplier()))


func _on_enemy_killed(_enemy: Node3D, info: DamageInfo) -> void:
	var player: Player = info.attacker as Player
	if not multiplayer.is_server() or player == null or player.multiplayer != multiplayer:
		return
	var amount: int = rules.points_per_kill
	if info.is_headshot():
		amount += rules.headshot_kill_bonus
	elif info.damage_type == DamageInfo.Type.MELEE:
		amount += rules.melee_kill_bonus
	player.wallet.earn(_boosted(player, amount * _multiplier()))


func _multiplier() -> int:
	return PAYDAY_MULTIPLIER if drops and drops.is_active(PowerUpData.Effect.PAYDAY) else 1


func _on_round_ended(_round_number: int) -> void:
	if not multiplayer.is_server():
		return
	_repair_points.clear()
	if rules.round_clear_bonus <= 0:
		return
	for node: Node in get_tree().get_nodes_in_group(&"players"):
		if node.multiplayer == multiplayer:
			(node as Player).wallet.earn(_boosted(node as Player, rules.round_clear_bonus))


## Earned points times the player's points_earned stat (Scrounger, gear), carrying the fraction.
func _boosted(player: Player, amount: int) -> int:
	var exact: float = amount * player.get_stat(&"points_earned") + _point_fraction.get(player, 0.0)
	var paid: int = floori(exact)
	_point_fraction[player] = exact - paid
	return paid


func _sync_points(total: int, _delta: int, player: Player) -> void:
	if player.net_id != 1 and multiplayer.get_peers().has(player.net_id):
		_receive_points.rpc_id(player.net_id, total)


@rpc("any_peer", "call_remote", "reliable")
func _request_points() -> void:
	if not multiplayer.is_server():
		return
	var sender: int = multiplayer.get_remote_sender_id()
	for node: Node in get_tree().get_nodes_in_group(&"players"):
		var player: Player = node as Player
		if player.multiplayer == multiplayer and player.net_id == sender:
			_sync_points(player.wallet.points, 0, player)
			return


@rpc("authority", "call_remote", "reliable")
func _receive_points(total: int) -> void:
	if multiplayer.get_remote_sender_id() == 1 and is_instance_valid(_local_player):
		_local_player.wallet.set_points(total)
