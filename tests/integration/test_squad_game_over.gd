## Two ENet peers run real GameSessions on an empty map: squad wipes and
## disconnects end only on the server, and both sides receive the same results.
extends GutTest

const SESSION: PackedScene = preload("res://systems/game/game_session.tscn")

var server_root: Node
var client_root: Node
var server: GameSession
var client: GameSession
var late_root: Node
var _port: int


func _make_session(root: Node) -> GameSession:
	var map: Level = Level.new()
	map.name = "Level"
	var scene: PackedScene = PackedScene.new()
	scene.pack(map)
	map.free()
	var session: GameSession = SESSION.instantiate() as GameSession
	session.level_scene = scene
	session.profile_id = &""
	session.rng_seed = 31
	session.restart_delay = 0.01
	session.wave_rules = session.wave_rules.duplicate(true) as WaveRules
	session.wave_rules.first_round_delay = 10000.0
	root.add_child(session)
	return session


func before_each() -> void:
	_port = TwoPeers.next_port()
	server_root = TwoPeers.make_side(self, "Server")
	client_root = TwoPeers.make_side(self, "Client")
	assert_eq(TwoPeers.host(server_root, _port, 2), OK)
	assert_eq(TwoPeers.join(client_root, _port), OK)
	client = _make_session(client_root)
	client.handshake._display_name = "Mara"
	server = _make_session(server_root)
	var joined: Callable = func() -> bool: return server.get_players().size() == 2 and client.get_players().size() == 2
	await wait_until(joined, 5.0, "both sessions have both players")
	for session: GameSession in [server, client]:
		for player: Player in session.get_players():
			player.set_physics_process(false)


func after_each() -> void:
	var roots: Array[Node] = [client_root, server_root]
	if is_instance_valid(late_root):
		roots.push_front(late_root)
	for root: Node in roots:
		TwoPeers.close_side(root)
	get_tree().paused = false


func _down(player: Player) -> void:
	player.health.take_damage(DamageInfo.create(1000.0, null))


func test_one_downed_player_keeps_the_match_running() -> void:
	_down(server.players.find_player(1))
	assert_false(server.is_over, "the teammate can still revive")
	assert_false(client.is_over, "clients do not independently end the match")
	assert_eq(server.get_players().size(), 2, "other session players are excluded")


func test_squad_wipe_freezes_both_peers_and_shows_identical_results() -> void:
	server.director.round_number = 4
	server.match_end.kills = 7
	server.match_end.headshots = 3
	server.players.find_player(1).wallet.earn(1234)
	server.players.find_player(client.multiplayer.get_unique_id()).wallet.earn(555)
	assert_true(server.economy.try_spend(server.players.find_player(1), 750))
	_down(server.players.find_player(1))
	_down(server.players.find_player(client.multiplayer.get_unique_id()))
	assert_true(server.is_over)
	await wait_until(func() -> bool: return client.is_over, 3.0, "server ended the client's match")
	for key: String in ["round", "kills", "headshots", "exfil"]:
		assert_eq(client.match_end.stats[key], server.match_end.stats[key], "shared results stay identical")
	assert_eq(client.match_end.stats["round"], 4)
	assert_eq(client.match_end.stats["kills"], 7)
	assert_eq(client.match_end.stats["headshots"], 3)
	assert_eq(server.match_end.stats["points"], 1234, "the host sees its own points")
	assert_eq(client.match_end.stats["points"], 555, "the client sees its own points, not the host's")
	assert_eq(server.level.process_mode, Node.PROCESS_MODE_DISABLED)
	assert_eq(client.level.process_mode, Node.PROCESS_MODE_DISABLED)
	await wait_until(func() -> bool: return _results_count() == 2, 3.0, "host and client both push results")


func _results_count() -> int:
	var count: int = 0
	for entry: Dictionary in UI._stack:
		count += 1 if entry["id"] == &"results" else 0
	return count


func test_squad_results_show_each_players_own_xp_and_totals() -> void:
	var host: Player = server.players.find_player(1)
	var client_id: int = client.multiplayer.get_unique_id()
	var owner: Player = client.players.find_player(client_id)
	server.start_total_xp = 100
	client.start_total_xp = 200
	server.progression.set_start_total(host, 100)
	client.progression.set_start_total(owner, 200)
	server.director.round_number = 4
	server.match_end.kills = 7
	server.progression.add_xp(host, 75)
	server.progression.add_xp(server.players.find_player(client_id), 25)
	_down(host)
	_down(server.players.find_player(client_id))
	await wait_until(func() -> bool: return client.is_over, 3.0, "client received its final results")
	assert_eq(server.match_end.stats["xp"], 75)
	assert_eq(server.match_end.stats["start_total_xp"], 100)
	assert_eq(server.match_end.stats["total_xp"], 175)
	assert_eq(client.match_end.stats["xp"], 25)
	assert_eq(client.match_end.stats["start_total_xp"], 200)
	assert_eq(client.match_end.stats["total_xp"], 225)
	assert_eq(client.match_end.stats["round"], 4)
	assert_eq(client.match_end.stats["kills"], 7)
	assert_false(client.match_end.stats["exfil"])
	for key: String in ["round", "kills", "exfil"]:
		assert_eq(client.match_end.stats[key], server.match_end.stats[key], "shared results stay identical")


func test_leaving_standing_teammate_does_not_prevent_game_over() -> void:
	_down(server.players.find_player(1))
	assert_false(server.is_over)
	client.level.process_mode = Node.PROCESS_MODE_DISABLED
	client_root.multiplayer.multiplayer_peer.close()
	client_root.multiplayer.multiplayer_peer = OfflineMultiplayerPeer.new()
	await wait_until(func() -> bool: return server.is_over, 5.0, "only the downed host remains")
	assert_eq(server.get_players().size(), 1)


func test_every_peer_has_match_end_at_the_same_path() -> void:
	for session: GameSession in [server, client]:
		var ending: MatchEnd = session.get_node("MatchEnd") as MatchEnd
		assert_eq(ending, session.match_end, "the results RPC needs one node path on every peer")
		assert_eq(ending.session, session)


func test_client_cannot_end_the_match_or_decide_a_wipe() -> void:
	client.match_end._end_match(false)
	client.match_end.check_squad()
	assert_false(client.is_over)
	assert_false(server.is_over)


func test_empty_dedicated_server_keeps_waiting() -> void:
	for player: Player in server.get_players():
		player.session = null
	server.match_end.check_squad()
	assert_false(server.is_over)


func test_dead_and_downed_members_also_end_the_match() -> void:
	var host: Player = server.players.find_player(1)
	_down(host)
	host.state_sync._physics_process(30.1)
	assert_true(host.is_dead)
	assert_false(server.is_over, "the standing teammate remains")
	_down(server.players.find_player(client.multiplayer.get_unique_id()))
	assert_true(server.is_over, "dead and downed leaves nobody standing")


func test_late_joiner_receives_an_ended_match() -> void:
	_down(server.players.find_player(1))
	_down(server.players.find_player(client.multiplayer.get_unique_id()))
	assert_true(server.is_over)
	late_root = TwoPeers.make_side(self, "LateClient")
	assert_eq(TwoPeers.join(late_root, _port), OK)
	var late_session: GameSession = _make_session(late_root)
	await wait_until(func() -> bool: return late_session.is_over, 5.0, "late join receives match results")
	assert_eq(late_session.match_end.stats, server.match_end.stats)
	assert_eq(late_session.level.process_mode, Node.PROCESS_MODE_DISABLED)


func _host_on_client() -> Player:
	return client.players.find_player(1)


func _card_text(cards: SquadCards, index: int) -> String:
	var card: VBoxContainer = cards.get_child(index) as VBoxContainer
	return "%s|%s" % [(card.get_child(0) as Label).text, (card.get_child(2) as Label).text]


func test_teammates_see_each_others_names_and_cards() -> void:
	var client_id: int = client.multiplayer.get_unique_id()
	assert_eq(server.players.find_player(client_id).display_name, "Mara", "the server keeps the hello name")
	server.players.find_player(client_id).state_sync.publish()
	await wait_until(func() -> bool: return client.players.find_player(client_id).display_name == "Mara", 3.0, "synced")
	var cards: SquadCards = SquadCards.new()
	add_child_autofree(cards)
	cards.local_player = client.players.find_player(client_id)
	cards.refresh()
	assert_true(cards.visible)
	assert_eq(cards.get_child_count(), 1, "one card: the host, not yourself")
	assert_eq(_card_text(cards, 0), "Survivor|")


func test_downed_teammate_card_counts_the_bleed_out_down() -> void:
	_down(server.players.find_player(1))
	await wait_until(func() -> bool: return _host_on_client().is_downed, 3.0, "downed state reached the client")
	var cards: SquadCards = SquadCards.new()
	add_child_autofree(cards)
	cards.local_player = client.players.find_player(client.multiplayer.get_unique_id())
	cards.refresh()
	assert_eq(_card_text(cards, 0), "Survivor|DOWN 0:30")
	_host_on_client().state_sync._physics_process(5.0)
	cards.refresh()
	assert_eq(_card_text(cards, 0), "Survivor|DOWN 0:25", "the client counts the bleed-out down between snapshots")
	var prompt: String = client.hud.coop_hud.get_prompt(cards.local_player, false)
	assert_eq(prompt, "Hold to revive Survivor [F]")


func test_solo_has_no_squad_cards() -> void:
	var cards: SquadCards = SquadCards.new()
	add_child_autofree(cards)
	cards.refresh()
	assert_false(cards.visible)
	assert_eq(cards.get_child_count(), 0)


## The client banks its run XP into its own character once, however many exits follow.
func test_client_banks_its_run_xp_once() -> void:
	var path: String = CharacterProfile.directory() + "test_coop_bank_once.json"
	client.profile = CharacterProfile.from_dict({"id": "test_coop_bank_once", "total_xp": 200})
	var client_id: int = client.multiplayer.get_unique_id()
	server.progression.add_xp(server.players.find_player(client_id), 25)
	_down(server.players.find_player(1))
	_down(server.players.find_player(client_id))
	await wait_until(func() -> bool: return client.is_over, 3.0, "client received the match end")
	assert_true(client.match_end.xp_banked)
	client.match_end.bank_run_xp()
	client.progression.run_xp_finalized.emit()
	assert_eq(client.profile.total_xp, 225, "the run's 25 XP is banked once")
	assert_eq(CharacterProfile.load_or_create(&"test_coop_bank_once").total_xp, 225, "the save holds it once")
	for leftover: String in [path, path + ".tmp"]:
		if FileAccess.file_exists(leftover):
			DirAccess.remove_absolute(ProjectSettings.globalize_path(leftover))
