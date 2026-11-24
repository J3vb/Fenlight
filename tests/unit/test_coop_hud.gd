## Revive prompts and progress follow replicated player state; pause releases held intent.
extends GutTest

const HUD: PackedScene = preload("res://systems/ui/hud.tscn")
const PLAYER: PackedScene = preload("res://systems/player/player.tscn")
const COOP_HUD: GDScript = preload("res://systems/net/coop_hud.gd")

var hud: Hud
var player: Player
var teammate: Player
var friend: Node


func before_each() -> void:
	assert_eq(Net.host(24645, 2), OK)
	friend = await TwoPeers.add_friend(self, 24645)
	hud = HUD.instantiate() as Hud
	add_child_autofree(hud)
	hud.set_process(false)
	hud.coop_hud.set_physics_process(false)
	player = _make_player("Local")
	teammate = _make_player("Rook")
	teammate.display_name = "Rook"
	teammate.position.x = 1.0
	Events.player_spawned.emit(player)


func after_each() -> void:
	while UI.top() != &"":
		UI.pop()
	Input.action_release(&"interact")
	TwoPeers.remove_friend(friend)
	Net.leave()


func _make_player(player_name: String) -> Player:
	var result: Player = PLAYER.instantiate() as Player
	result.name = player_name
	add_child_autofree(result)
	result.set_physics_process(false)
	result.state_sync.set_physics_process(false)
	result.revive.set_physics_process(false)
	return result


func test_prompt_names_nearby_teammate_and_bar_tracks_hold() -> void:
	assert_eq(hud.coop_hud.get_script(), COOP_HUD)
	teammate.is_downed = true
	player.revive.progress = 0.5
	hud._process(0.0)
	assert_eq(hud.prompt_label.text, "Hold to revive Rook")
	assert_true(hud.coop_hud.hold_bar.visible)
	assert_almost_eq(hud.coop_hud.hold_bar.value, 0.5, 0.001)
	teammate.position.x = 2.0
	hud._process(0.0)
	assert_false(hud.prompt_box.visible)
	assert_false(hud.coop_hud.hold_bar.visible)


func test_down_and_dead_messages_follow_synced_flags() -> void:
	player.is_downed = true
	hud._process(0.0)
	assert_eq(hud.prompt_label.text, "You are down · Waiting for a revive")
	assert_false(hud.coop_hud.hold_bar.visible)
	player.is_downed = false
	player.is_dead = true
	hud._process(0.0)
	assert_eq(hud.prompt_label.text, "Spectating · Gear kept · Respawn next round")


func test_held_input_uses_frames_and_pause_cancels() -> void:
	teammate.is_downed = true
	hud._process(0.0)
	Input.action_press(&"interact")
	player.last_frame = player.local_input.sample(1)
	hud._physics_process(0.3)
	assert_almost_eq(player.revive.progress, 0.1, 0.001)
	UI.push(&"pause")
	hud._process(0.0)
	hud._physics_process(0.3)
	assert_almost_eq(player.revive.progress, 0.0, 0.001)
	assert_false(hud.prompt_box.visible)
	assert_false(hud.coop_hud.hold_bar.visible)


func test_prompt_and_frames_skip_a_player_that_left_the_tree() -> void:
	var gone: Player = _make_player("Gone")
	gone.get_parent().remove_child(gone)
	assert_eq(hud.coop_hud.get_prompt(gone, false), "", "the server went away and took the player out")
	hud.coop_hud.apply_frame(InputFrame.new(), 0.016)
	assert_null(gone.revive.nearest_target())
	hud._player = gone
	gone.free()
	hud._process(0.016)
	hud._physics_process(0.016)
	assert_eq(hud.prompt_label.text, "", "a freed local player shows no prompt and raises no error")


func test_dialog_cancels_a_held_revive_until_the_interact_key_is_released() -> void:
	teammate.is_downed = true
	hud._process(0.0)
	Input.action_press(&"interact")
	player.last_frame = player.local_input.sample(1)
	hud._physics_process(0.3)
	assert_gt(player.revive.progress, 0.0)
	var dialog: ConfirmationDialog = ConfirmationDialog.new()
	add_child(dialog)
	player.local_input.block_for_dialog(dialog)
	hud._physics_process(Revive.HOLD_TIME)
	assert_eq(player.revive.progress, 0.0)
	dialog.free()
	player.last_frame = player.local_input.sample(2)
	hud._physics_process(Revive.HOLD_TIME)
	assert_eq(player.revive.progress, 0.0)
	Input.action_release(&"interact")
	player.local_input.sample(3)
	Input.action_press(&"interact")
	player.last_frame = player.local_input.sample(4)
	hud._physics_process(0.3)
	assert_gt(player.revive.progress, 0.0)
	player.revive._elapsed = player.revive.hold_time() - 0.01
	var balance: int = player.wallet.points
	Input.action_release(&"interact")
	hud._physics_process(0.02)
	player.revive._physics_process(0.02)
	assert_eq(player.revive.progress, 0.0, "the HUD sees release before the next player sample")
	assert_true(teammate.is_downed)
	assert_eq(player.wallet.points, balance)
