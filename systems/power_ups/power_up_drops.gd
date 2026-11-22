## Rolls a power-up drop for every kill by a player: drop_chance each, at most
## max_per_round a round. Types come from a shuffled deck, so every type drops
## once before any repeats; a type with deck_chance below 1 sits out some decks.
## Kills by a player with Scavenger can also drop an ammo pack, and Chain Supply
## kills a second, different power-up (neither counted in the cap). Lives in the
## GameSession. The server spawns pickups and Supply Crates through a
## MultiplayerSpawner, so every peer and late joiner sees them; ammo effects reach
## the PCs that own the guns. Timed power-ups (Payday, Overkill, Stasis) run on a
## team-wide server timer; every peer hears when one starts, late joiners ask for
## the time left. Clearing a Blackout round drops its reward where the last zombie
## died (outside the cap).
class_name PowerUpDrops
extends Node

const SCENE: PackedScene = preload("res://systems/power_ups/power_up.tscn")
const CRATE_SCENE: PackedScene = preload("res://systems/power_ups/supply_crate.tscn")
## Spawn data kinds: one MultiplayerSpawner makes pickups and Supply Crates.
const KIND_PICKUP: int = 0
const KIND_CRATE: int = 1
## Chain Supply: chance that a drop brings a second, different power-up, and how far apart they land.
const CHAIN_CHANCE: float = 0.25
const CHAIN_OFFSET: Vector3 = Vector3(0.8, 0.0, 0.0)

@export var drop_chance: float = 0.05
@export var max_per_round: int = 4
@export var power_ups: Array[PowerUpData] = []
@export var ammo_pack: PowerUpData
@export var ammo_pack_chance: float = 0.05

var session: GameSession
var dropped_this_round: int = 0
var _deck: Array[PowerUpData] = []
var _net: MultiplayerSpawner
var _next_id: int = 0
var _last_kill: Vector3 = Vector3.ZERO
## Server: seconds left per running timed power-up.
var _timers: Dictionary[PowerUpData, float] = {}


func _ready() -> void:
	Events.enemy_killed.connect(_on_enemy_killed)
	Events.round_started.connect(func(_round: int, _count: int) -> void: dropped_this_round = 0)
	Events.round_ended.connect(_on_round_ended)
	multiplayer.connected_to_server.connect(_ask_timers)
	if not multiplayer.is_server():
		_ask_timers.call_deferred()


func _physics_process(delta: float) -> void:
	if _timers.is_empty() or not multiplayer.is_server():
		return
	var ended: PowerUpData = null
	for data: PowerUpData in _timers:
		_timers[data] -= delta
		if _timers[data] <= 0.0:
			ended = data
	if ended:
		_timers.erase(ended)
		if ended.effect == PowerUpData.Effect.STASIS:
			PowerUpEffects.set_stasis(session.spawner, false)


## Server: starts data's timer for the whole team, or resets it to full time on a re-pickup.
## extra: the collector's power_up_duration seconds (Overtime, gear).
func start_timer(data: PowerUpData, extra: float = 0.0) -> void:
	if not multiplayer.is_server():
		return
	var duration: float = data.duration + maxf(extra, 0.0)
	_timers[data] = duration
	if data.effect == PowerUpData.Effect.STASIS:
		PowerUpEffects.set_stasis(session.spawner, true)
	Events.power_up_timer_started.emit(data, duration)
	if not multiplayer.get_peers().is_empty():
		_receive_timer.rpc(data.id, duration)


## Server: true while a timed power-up with this effect runs.
func is_active(effect: PowerUpData.Effect) -> bool:
	for data: PowerUpData in _timers:
		if data.effect == effect:
			return true
	return false


## Server: seconds left on data's timer, 0 when it is not running.
func time_left(data: PowerUpData) -> float:
	return _timers.get(data, 0.0)


## Called once the level exists, on every peer, so spawns have the same path everywhere.
func setup(level: Node3D) -> void:
	_net = MultiplayerSpawner.new()
	_net.name = "Net"
	_net.spawn_function = _create
	add_child(_net)
	_net.spawn_path = _net.get_path_to(level)


func drop(data: PowerUpData, at: Vector3) -> PowerUp:
	dropped_this_round += 1
	return _spawn(data, at)


func _spawn(data: PowerUpData, at: Vector3) -> PowerUp:
	return _spawn_kind(KIND_PICKUP, data, at + Vector3.UP * 0.8) as PowerUp


## Server: a Supply Crate standing at `at`.
func spawn_crate(data: PowerUpData, at: Vector3) -> SupplyCrate:
	return _spawn_kind(KIND_CRATE, data, at) as SupplyCrate


func _spawn_kind(kind: int, data: PowerUpData, at: Vector3) -> Node:
	_next_id += 1
	var spawn_data: Array = [_next_id, data.id, at, kind]
	if _net:
		return _net.spawn(spawn_data)
	var node: Node = _create(spawn_data)
	session.level.add_child(node)
	return node


## Runs on the server and on every client with the same data.
func _create(spawn_data: Array) -> Node:
	if int(spawn_data[3]) == KIND_CRATE:
		return _create_crate(spawn_data)
	var pickup: PowerUp = SCENE.instantiate() as PowerUp
	pickup.name = "PowerUp%d" % int(spawn_data[0])
	pickup.data = Content.get_item(&"power_ups", spawn_data[1]) as PowerUpData
	pickup.drops = self
	pickup.position = spawn_data[2]
	var sync: MultiplayerSynchronizer = MultiplayerSynchronizer.new()
	var config: SceneReplicationConfig = SceneReplicationConfig.new()
	config.add_property(^".:age")
	config.property_set_replication_mode(^".:age", SceneReplicationConfig.REPLICATION_MODE_NEVER)
	sync.replication_config = config
	pickup.add_child(sync)
	return pickup


## The crate's pool is the level Vault's, so it rolls the same guns.
func _create_crate(spawn_data: Array) -> SupplyCrate:
	var crate: SupplyCrate = CRATE_SCENE.instantiate() as SupplyCrate
	crate.name = "SupplyCrate%d" % int(spawn_data[0])
	crate.position = spawn_data[2]
	crate.session = session
	for node: Node in get_tree().get_nodes_in_group(&"specimen_vault"):
		if session.level.is_ancestor_of(node):
			crate.pool = (node as SpecimenVault).pool
	if session.interactions:
		session.interactions.watch(crate)
	return crate


## Server: runs the effect, then everyone hears and sees the pickup go.
func on_collected(pickup: PowerUp, collector: Player) -> void:
	match pickup.data.effect:
		PowerUpData.Effect.RESUPPLY, PowerUpData.Effect.AMMO_PACK:
			_grant_ammo(pickup.data, collector)
		PowerUpData.Effect.PURGE:
			PowerUpEffects.purge(session.spawner)
		PowerUpData.Effect.SCRAP_KIT:
			PowerUpEffects.rebuild_barriers(session.level)
		PowerUpData.Effect.SUPPLY_CRATE:
			spawn_crate(pickup.data, pickup.position - Vector3.UP * 0.8)
	if pickup.data.duration > 0.0:
		start_timer(pickup.data, collector.get_stat(&"power_up_duration", 0.0))
	for player: Player in session.get_players() if pickup.data.team_points > 0 else []:
		player.wallet.add(pickup.data.team_points)
	if not multiplayer.get_peers().is_empty():
		_receive_collected.rpc(pickup.name, pickup.data.id, collector.net_id)


## Server: the ammo goes to every PC whose guns it changes.
func _grant_ammo(data: PowerUpData, collector: Player) -> void:
	var targets: Array[Player] = [collector]
	if data.effect == PowerUpData.Effect.RESUPPLY:
		targets = session.get_players()
	for player: Player in targets:
		if data.effect == PowerUpData.Effect.RESUPPLY:
			player.grenades.refill()
		if player.net_id == multiplayer.get_unique_id():
			PowerUp.apply_effect(player, data)
		elif multiplayer.get_peers().has(player.net_id):
			_receive_effect.rpc_id(player.net_id, data.id)


@rpc("authority", "call_remote", "reliable")
func _receive_effect(data_id: StringName) -> void:
	var data: PowerUpData = Content.get_item(&"power_ups", data_id) as PowerUpData
	var player: Player = session.players.find_player(multiplayer.get_unique_id()) if session.players else null
	if data and player:
		PowerUp.apply_effect(player, data)


@rpc("authority", "call_remote", "reliable")
func _receive_collected(pickup_name: String, data_id: StringName, collector_id: int) -> void:
	var data: PowerUpData = Content.get_item(&"power_ups", data_id) as PowerUpData
	if data == null:
		return
	var pickup: PowerUp = session.level.get_node_or_null(pickup_name) as PowerUp
	if pickup:
		pickup.play_collect_sound()
		pickup.hide()
	Events.power_up_collected.emit(session.players.find_player(collector_id) if session.players else null, data)


@rpc("authority", "call_remote", "reliable")
func _receive_timer(data_id: StringName, seconds: float) -> void:
	if multiplayer.get_remote_sender_id() != 1 or multiplayer.is_server():
		Log.warn(&"power_ups", &"timer_ignored", {"sender": multiplayer.get_remote_sender_id()})
		return
	var data: PowerUpData = Content.get_item(&"power_ups", data_id) as PowerUpData
	if data:
		Events.power_up_timer_started.emit(data, seconds)


func _ask_timers() -> void:
	var peer: MultiplayerPeer = multiplayer.multiplayer_peer
	if is_inside_tree() and peer and peer.get_connection_status() == MultiplayerPeer.CONNECTION_CONNECTED:
		_request_timers.rpc_id(1)


@rpc("any_peer", "call_remote", "reliable")
func _request_timers() -> void:
	if not multiplayer.is_server():
		return
	var sender: int = multiplayer.get_remote_sender_id()
	for data: PowerUpData in _timers:
		_receive_timer.rpc_id(sender, data.id, _timers[data])


func _on_enemy_killed(enemy: Node3D, info: DamageInfo) -> void:
	_last_kill = enemy.global_position
	var killer: Player = info.attacker as Player
	if not multiplayer.is_server() or killer == null:
		return
	if killer.has_serum(&"scavenger") and session.rng.randf() < ammo_pack_chance:
		_spawn(ammo_pack, enemy.global_position)
	if dropped_this_round >= max_per_round or power_ups.is_empty():
		return
	if session.rng.randf() < drop_chance:
		var first: PowerUpData = _next()
		drop(first, enemy.global_position)
		if killer.skill_rules.has(SkillNodeData.Rule.CHAIN_SUPPLY) and session.rng.randf() < CHAIN_CHANCE:
			_chain(first, enemy.global_position + CHAIN_OFFSET)


## A second power-up of another kind, outside the round cap; none when the deck has one kind.
func _chain(first: PowerUpData, at: Vector3) -> void:
	var others: Array[PowerUpData] = []
	for data: PowerUpData in power_ups:
		if data.id != first.id and not others.has(data):
			others.append(data)
	if not others.is_empty():
		_spawn(others[session.rng.randi_range(0, others.size() - 1)], at)


## Server: the round ends while the lights are still out, so this is a cleared Blackout round.
func _on_round_ended(_round_number: int) -> void:
	if not multiplayer.is_server() or session == null or not session.director.blackout_round:
		return
	var reward: PowerUpData = session.wave_rules.blackout_reward
	if reward:
		_spawn(reward, _last_kill)


func _next() -> PowerUpData:
	while _deck.is_empty():
		for data: PowerUpData in power_ups:
			if data.deck_chance >= 1.0 or session.rng.randf() < data.deck_chance:
				_deck.append(data)
		for i: int in range(_deck.size() - 1, 0, -1):
			var j: int = session.rng.randi_range(0, i)
			var swap: PowerUpData = _deck[i]
			_deck[i] = _deck[j]
			_deck[j] = swap
	return _deck.pop_back()
