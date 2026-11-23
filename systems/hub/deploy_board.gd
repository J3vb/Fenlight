## The Deploy board at the town gate. Pressing interact readies you for its place
## (or cancels your ready) through the hub's DeployVote. The prompt follows the
## last Events.deploy_vote_changed, so it is right on every peer.
class_name DeployBoard
extends Interactable

## A content/screens id: where the squad goes.
@export var place: StringName = &""
@export var label: String = ""

var _vote_place: StringName = &""
var _ready_ids: Array[int] = []


func _ready() -> void:
	super()
	add_to_group(&"deploy_board")
	($Title as Label3D).text = label.to_upper()
	Events.deploy_vote_changed.connect(_on_vote_changed)


func get_prompt(player: Player) -> String:
	if not _vote_place.is_empty() and _vote_place != place:
		return ""
	if _ready_ids.has(player.net_id):
		return "Cancel ready [F]"
	if player.session and player.session.profile:
		return "Ready: %s · %d free stash slots [F]" % [label, player.session.profile.free_stash_slots()]
	return "Ready: %s [F]" % label


func interact(player: Player, _facts: Dictionary = {}) -> void:
	if player.session and player.session.deploy_vote:
		player.session.deploy_vote.toggle_ready(player, place)


func _on_vote_changed(vote_place: StringName, ready_ids: Array[int], _countdown_left: float) -> void:
	_vote_place = vote_place
	_ready_ids = ready_ids
