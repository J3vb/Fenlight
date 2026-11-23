## Holds a nearby teammate's revive on the server; owners send only start/cancel intent.
## Also the server's going-down rules: Second Wind, Undying's charge and Last Stand, and the
## player Legendary traits: Quarantine Shell, Iron Lung and Last Rites.
class_name Revive
extends Node

const RANGE: float = 1.5
const HOLD_TIME: float = 3.0
const REWARD: int = 50
## Last Stand: a killing blow leaves this much health, then damage is ignored for IMMUNE_TIME.
const LAST_STAND_HEALTH: float = 1.0
const LAST_STAND_IMMUNE_TIME: float = 2.0

var progress: float = 0.0
var _player: Player
var _requested: Player
var _active: Player
var _elapsed: float = 0.0
var _local_elapsed: float = 0.0
var _last_stand_used: bool = false
var _immune_left: float = 0.0
var _undying_used: bool = false
var _shell_left: float = 0.0
var _kill_streak: int = 0
var _rites_kills: int = 0
var _rites_used: bool = false


func _init() -> void:
	name = "Revive"
	set_multiplayer_authority(1)


func _ready() -> void:
	_player = get_parent() as Player
	Events.round_started.connect(_on_round_started)
	Events.enemy_killed.connect(_on_enemy_killed)
	Events.player_damaged.connect(_on_player_damaged)


## Server: true when this hit is ignored (Last Stand immunity). A killing blow with
## Last Stand unused this round is cut to leave LAST_STAND_HEALTH.
func absorbs(info: DamageInfo) -> bool:
	if _immune_left > 0.0:
		return true
	var shell: float = _player.stats.value(&"quarantine_shell", 0.0)
	if shell > 0.0 and _shell_left <= 0.0 and info.amount > 0.0:
		_shell_left = shell
		return true
	var rule: bool = _player.skill_rules.has(SkillNodeData.Rule.LAST_STAND)
	if rule and not _last_stand_used and info.amount >= _player.health.current:
		_last_stand_used = true
		_immune_left = LAST_STAND_IMMUNE_TIME
		info.amount = maxf(_player.health.current - LAST_STAND_HEALTH, 0.0)
	return false


## Undying: one self-revive per run when Second Wind is not held.
func has_undying_charge() -> bool:
	return _player.skill_rules.has(SkillNodeData.Rule.UNDYING) and not _undying_used


## Undying's charge or an unused Last Rites can still get a downed player up.
func can_get_up() -> bool:
	return has_undying_charge() or (not _rites_used and _last_rites_needed() > 0)


## Kills Last Rites needs while downed: the lowest value among the player's item guns, 0 without one.
func _last_rites_needed() -> int:
	var needed: int = 0
	for item: ItemInstance in _player.item_guns.values():
		var kills: int = roundi(item.stats.value(&"last_rites", 0.0))
		if kills > 0 and (needed == 0 or kills < needed):
			needed = kills
	return needed


## Server: Iron Lung counts kills in a row without taking damage; Last Rites counts kills while downed.
func _on_enemy_killed(_enemy: Node3D, info: DamageInfo) -> void:
	if not multiplayer.is_server() or info.attacker != _player:
		return
	var lung: float = _player.stats.value(&"iron_lung", 0.0)
	_kill_streak += 1
	if lung > 0.0 and _kill_streak >= roundi(lung):
		_kill_streak = 0
		_player.health.start_regen_now()
	var item: ItemInstance = _player.item_guns.get(info.item_uid) if not info.item_uid.is_empty() else null
	var needed: float = item.stats.value(&"last_rites", 0.0) if item else 0.0
	if not _player.is_downed or _player.is_dead or _rites_used or needed <= 0.0:
		return
	_rites_kills += 1
	if _rites_kills >= roundi(needed):
		_rites_used = true
		_rites_kills = 0
		_player.state_sync.revive_player()


func _on_player_damaged(player: Player, _info: DamageInfo) -> void:
	if player == _player:
		_kill_streak = 0


func _on_round_started(_round_number: int, _count: int) -> void:
	_last_stand_used = false
	_rites_used = false
	_rites_kills = 0


## Server: Second Wind keeps the player down for second_wind_time, then gets them up.
## It uses up Second Wind only; without it, Undying's charge is used and every Serum is lost.
## In co-op the player is already downed by PlayerStateSync.
func second_wind() -> void:
	var coop: bool = _player.state_sync.is_coop()
	if not coop:
		_player.is_downed = true
		_player.is_crouching = true
		_player.camera_rig.tilt_down(true)
	await get_tree().create_timer(_player.second_wind_time, false, true).timeout
	if not _player.is_downed or _player.is_dead:
		return
	var held: int = _player.serums.size()
	_player.lose_serums(true)
	if _player.serums.size() == held:
		_undying_used = true
		_player.lose_serums()
	if coop:
		_player.state_sync.revive_player()
		return
	_player.is_downed = false
	_player.is_crouching = false
	_player.input_enabled = true
	_player.health.reset(_player.health.max_health)
	_player.camera_rig.tilt_down(false)
	_player.state_sync.publish()
	Events.player_revived.emit(_player)


## The HUD supplies held interact intent through the existing InputFrame seam.
func apply_frame(frame: InputFrame, delta: float) -> void:
	set_held(frame.has(InputFrame.INTERACT))
	if is_instance_valid(_requested) and can_revive(_requested):
		_local_elapsed += delta
		progress = minf(_local_elapsed / hold_time(), 1.0)
	else:
		progress = 0.0


## Seconds this player needs to revive someone; Undying and the Fast revive affix shorten it.
func hold_time() -> float:
	return HOLD_TIME / maxf(_player.get_stat(&"fast_revive"), 0.01)


func set_held(held: bool) -> void:
	if not _player.is_multiplayer_authority():
		return
	var candidate: Player = nearest_target() if held else null
	if candidate == _requested:
		return
	_requested = candidate
	_local_elapsed = 0.0
	progress = 0.0
	if multiplayer.is_server():
		_begin(candidate)
	else:
		_request.rpc_id(1, candidate.net_id if candidate else 0)


func nearest_target() -> Player:
	var nearest: Player
	var distance: float = RANGE * RANGE
	if not is_inside_tree() or not is_instance_valid(_player):
		return null
	for node: Node in get_tree().get_nodes_in_group(&"players"):
		var candidate: Player = node as Player
		if not can_revive(candidate):
			continue
		var squared: float = _player.global_position.distance_squared_to(candidate.global_position)
		if squared <= distance:
			distance = squared
			nearest = candidate
	return nearest


func can_revive(target: Player) -> bool:
	if not Net.is_coop(multiplayer) or not is_instance_valid(target) or target == _player:
		return false
	if target.get_multiplayer() != multiplayer or target.is_queued_for_deletion():
		return false
	if _player.session and _player.session.is_over:
		return false
	if not _player.is_alive() or _player.is_downed or _player.is_dead:
		return false
	return (
		target.is_downed
		and not target.is_dead
		and _player.global_position.distance_squared_to(target.global_position) <= RANGE * RANGE
	)


func _physics_process(delta: float) -> void:
	_immune_left = maxf(_immune_left - delta, 0.0)
	_shell_left = maxf(_shell_left - delta, 0.0)
	if multiplayer.multiplayer_peer.get_connection_status() == MultiplayerPeer.CONNECTION_DISCONNECTED:
		return
	if not multiplayer.is_server() or not is_instance_valid(_active):
		return
	if not can_revive(_active) or not _connected(_player) or not _connected(_active):
		var target_id: int = _active.net_id
		_begin(null)
		_notify_rejected(target_id)
		return
	_elapsed += delta
	if _elapsed < hold_time():
		return
	var revived: Player = _active
	_begin(null)
	revived.state_sync.revive_player()
	_player.wallet.earn(REWARD)


@rpc("any_peer", "call_remote", "reliable")
func _request(target_id: int) -> void:
	if not multiplayer.is_server() or multiplayer.get_remote_sender_id() != _player.get_multiplayer_authority():
		return
	var target: Player
	for node: Node in get_tree().get_nodes_in_group(&"players"):
		var candidate: Player = node as Player
		if candidate.net_id == target_id and candidate.get_multiplayer() == multiplayer:
			target = candidate
			break
	_begin(target)
	if target_id != 0 and _active == null:
		_notify_rejected(target_id)


func _notify_rejected(target_id: int) -> void:
	if _player.is_multiplayer_authority():
		_rejected(target_id)
	elif _connected(_player):
		_rejected.rpc_id(_player.get_multiplayer_authority(), target_id)


@rpc("authority", "call_remote", "reliable")
func _rejected(target_id: int) -> void:
	if is_instance_valid(_requested) and _requested.net_id == target_id:
		_requested = null
		_local_elapsed = 0.0
		progress = 0.0


func _begin(target: Player) -> void:
	_active = target if can_revive(target) else null
	_elapsed = 0.0


func _connected(player: Player) -> bool:
	var peer: int = player.get_multiplayer_authority()
	return not player.is_queued_for_deletion() and (peer == 1 or multiplayer.get_peers().has(peer))
