## Match end and results: counts kills, ends the match on a squad wipe or exfil (server only),
## sends every peer the results and banks the run's XP and loot into the local character once.
class_name MatchEnd
extends Node

var session: GameSession
var kills: int = 0
var headshots: int = 0
var stats: Dictionary = {}
var xp_banked: bool = false
var _squad_result: Dictionary = {}


func _init() -> void:
	name = "MatchEnd"


## Called by the session once it is ready; test sessions that skip it get no automatic match end.
func setup() -> void:
	session.progression.run_xp_finalized.connect(bank_run_xp)
	Events.player_died.connect(_on_player_died)
	Events.enemy_killed.connect(_on_enemy_killed)
	multiplayer.peer_disconnected.connect(_on_peer_left)


## All match exits share this guard, including a restart after game over.
func bank_run_xp() -> void:
	if xp_banked:
		return
	xp_banked = true
	var progression: ProgressionService = session.progression
	var transport: MultiplayerPeer = progression.multiplayer.multiplayer_peer
	if (
		is_inside_tree()
		and transport
		and transport.get_connection_status() == MultiplayerPeer.CONNECTION_CONNECTED
		and progression.multiplayer.is_server()
	):
		for player: Player in session.get_players():
			progression.finish_run(player)
		var peer: ENetMultiplayerPeer = progression.multiplayer.multiplayer_peer as ENetMultiplayerPeer
		if peer:
			peer.host.flush()
	if not session.has_local_player or session.profile == null or not is_instance_valid(session.profile_player):
		return
	session.profile.total_xp += progression.get_xp(session.profile_player)
	session.loot.bank(session.profile)
	session.profile.save()


## Ends the match as a successful exfil: +50% XP for the whole run.
func finish_exfil() -> void:
	if session.is_over or not multiplayer.is_server():
		return
	for player: Player in session.get_players():
		session.progression.add_xp(player, session.progression.get_xp(player) / 2)
	session.level.process_mode = Node.PROCESS_MODE_DISABLED
	_end_match(true)


## Only connected squad members count; an empty dedicated server waits for players.
## A client closing for a place change is offline (so "server") but ends nothing.
func check_squad() -> void:
	if not is_inside_tree() or session.is_over or Net.changing_place or not multiplayer.is_server():
		return
	var squad: Array[Player] = session.get_players()
	if squad.is_empty() or squad.any(func(p: Player) -> bool: return p.is_alive() or p.can_self_revive()):
		return
	_end_match(false)


## A player who joins an ended match gets its results.
func share_results(peer_id: int) -> void:
	if not _squad_result.is_empty() and multiplayer.is_server():
		_receive_match_end.rpc_id(peer_id, _results_for(peer_id))


func _results_for(peer_id: int) -> Dictionary:
	var player: Player = session.players.find_player(peer_id)
	return _squad_result.merged({"points": player.wallet.earned if player else 0})


func _on_enemy_killed(_enemy: Node3D, info: DamageInfo) -> void:
	kills += 1
	if info.is_headshot():
		headshots += 1


func _on_player_died(player: Player) -> void:
	if player.session == session:
		check_squad()


func _on_peer_left(_peer_id: int) -> void:
	check_squad.call_deferred()


func _end_match(exfiled: bool) -> void:
	if session.is_over or not multiplayer.is_server():
		return
	bank_run_xp()
	_squad_result = {
		"round": session.director.round_number,
		"kills": kills,
		"headshots": headshots,
		"exfil": exfiled,
	}
	for peer_id: int in multiplayer.get_peers():
		share_results(peer_id)
	_receive_match_end(_results_for(multiplayer.get_unique_id()))


@rpc("authority", "call_local", "reliable")
func _receive_match_end(shared: Dictionary) -> void:
	if session.is_over:
		return
	session.is_over = true
	bank_run_xp()
	stats = shared.duplicate()
	stats.merge(session.loot.results(), true)
	_add_own_results(shared)
	session.director.stop()
	if Net.is_coop(multiplayer):
		session.level.process_mode = Node.PROCESS_MODE_DISABLED
	await get_tree().create_timer(session.restart_delay).timeout
	Events.game_over.emit(stats)
	if session.has_local_player:
		var results: ResultsScreen = UI.push(&"results") as ResultsScreen
		results.show_results(stats, session.tick / Engine.physics_ticks_per_second, session.progression.rules)
		results.main_menu_requested.connect(session.return_to_menu)
		results.restart_requested.connect(session.restart)


## Each peer shows its own points and XP, not the host's.
func _add_own_results(shared: Dictionary) -> void:
	var player: Player = session.profile_player
	if not is_instance_valid(player):
		return
	stats["xp"] = session.progression.get_xp(player)
	stats["start_total_xp"] = session.start_total_xp
	stats["total_xp"] = session.progression.get_total_xp(player)
	if session.profile:
		var map: String = session.level_scene.resource_path.get_base_dir().get_file()
		stats["new_best"] = session.profile.record_run(map, shared)
