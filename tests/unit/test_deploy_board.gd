## The town Deploy board and vote panel: a client's press readies it on the server,
## the prompt and panel follow Events.deploy_vote_changed on every peer.
extends "res://tests/unit/coop_interaction_fixture.gd"

const BOARD: PackedScene = preload("res://systems/hub/deploy_board.tscn")
const PANEL: PackedScene = preload("res://systems/hub/deploy_vote_panel.tscn")
const TOWN: PackedScene = preload("res://levels/lantern_post/lantern_post.tscn")


func before_each() -> void:
	await super()
	server.is_hub = true
	server.has_local_player = false
	for session: GameSession in [server, client]:
		session.deploy_vote = DeployVote.new()
		session.deploy_vote.session = session
		session.add_child(session.deploy_vote)
		var made: DeployBoard = BOARD.instantiate() as DeployBoard
		made.name = "DeployBoard"
		made.place = &"match"
		made.label = "Halcyon Labs"
		made.position = Vector3(0, 0, -1)
		session.level.add_child(made)


func after_each() -> void:
	Net.place = &""
	super()


func board(session: GameSession) -> DeployBoard:
	return target(session, "DeployBoard") as DeployBoard


func test_town_board_points_at_a_known_place() -> void:
	var town: Node = TOWN.instantiate()
	var found: DeployBoard = town.get_node(^"Gate/DeployBoardSpot/DeployBoard") as DeployBoard
	assert_not_null(found)
	assert_true(Content.has(UI.TYPE, found.place), "place is a screens id")
	assert_false(found.label.is_empty())
	assert_not_null(town.get_node_or_null(^"DeployVotePanel"), "the town has the vote panel")
	town.free()


func test_a_client_press_readies_and_a_second_press_unreadies() -> void:
	assert_eq(board(client).get_prompt(on_client()), "Ready: Halcyon Labs [F]")
	client.interactions.request(on_client(), board(client))
	await wait_until(func() -> bool: return server.deploy_vote.is_ready(client_id), 3.0, "client ready")
	await wait_physics_frames(4)
	assert_eq(server.deploy_vote.place, &"match")
	assert_eq(board(client).get_prompt(on_client()), "Cancel ready [F]", "the client's prompt follows the vote")
	await wait_seconds(InteractionSync.REQUEST_GAP + 0.05)
	client.interactions.request(on_client(), board(client))
	await wait_until(func() -> bool: return server.deploy_vote.place == &"", 3.0, "vote over")
	await wait_physics_frames(4)
	assert_false(server.deploy_vote.is_ready(client_id))
	assert_eq(board(client).get_prompt(on_client()), "Ready: Halcyon Labs [F]")


func test_board_shows_the_local_characters_available_stash_space() -> void:
	client.profile = CharacterProfile.new()
	client.profile.stash[3] = {"uid": "stored"}
	assert_string_contains(board(client).get_prompt(on_client()), "59 free stash slots")


func test_any_ready_player_can_cancel_the_countdown() -> void:
	late = make_side("InteractLate")
	late.deploy_vote = DeployVote.new()
	late.deploy_vote.session = late
	late.add_child(late.deploy_vote)
	add_player(late, client_id)
	await join(late)
	var late_id: int = late.multiplayer.get_unique_id()
	add_player(server, late_id)
	await wait_physics_frames(4)
	board(server).interact(on_server(client_id))
	board(server).interact(on_server(late_id))
	await wait_physics_frames(4)
	assert_gt(server.deploy_vote.countdown_left(), 0.0, "everyone ready counts down")
	board(server).interact(on_server(client_id))
	await wait_physics_frames(4)
	assert_eq(server.deploy_vote.countdown_left(), 0.0, "the first player's second press stopped it")
	assert_eq(server.deploy_vote.place, &"match", "the other player is still ready")


func test_board_for_another_place_shows_no_prompt_while_a_vote_runs() -> void:
	board(client).place = &"hub"
	Events.deploy_vote_changed.emit(&"match", [] as Array[int], 0.0)
	assert_eq(board(client).get_prompt(on_client()), "")


func test_panel_shows_names_ticks_and_countdown_and_hides_without_a_vote() -> void:
	var panel: DeployVotePanel = PANEL.instantiate() as DeployVotePanel
	add_child_autofree(panel)
	var box: Control = panel.get_node(^"Box") as Control
	assert_false(box.visible, "hidden while no vote")
	on_client().display_name = "Wren"
	Events.deploy_vote_changed.emit(&"match", [client_id] as Array[int], 0.0)
	assert_true(box.visible)
	var names: String = (panel.get_node(^"Box/Rows/Names") as Label).text
	assert_string_contains(names, "[x]  Wren")
	assert_eq((panel.get_node(^"Box/Rows/Title") as Label).text, "Deploy: Halcyon Labs")
	assert_string_contains((panel.get_node(^"Box/Rows/Status") as Label).text, "ready")
	Events.deploy_vote_changed.emit(&"match", [client_id] as Array[int], 4.2)
	assert_eq((panel.get_node(^"Box/Rows/Status") as Label).text, "Deploying in 5")
	Events.deploy_vote_changed.emit(&"", [] as Array[int], 0.0)
	assert_false(box.visible, "hidden when the vote ends")
