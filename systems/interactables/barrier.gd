## A boarded window. Zombies spawned behind it tear the planks off from
## outside (+Z faces into the room), then climb through. Players hold interact
## inside to repair a plank every HOLD_INTERVAL for points. The Blocker keeps players in; it
## sits on the barrier layer, which zombies and the navmesh bake ignore.
## Three attack slots line the window; extra zombies wait at queue points
## further back, and only one zombie vaults through at a time. Planks reach
## clients through net_state(); clients play the tear or repair sound.
class_name Barrier
extends Interactable

const PLANKS: int = 6
const REPAIR_TIME: float = 0.5
## A little longer than REPAIR_TIME, so a held key never lands on the cooldown's last tick.
const HOLD_INTERVAL: float = REPAIR_TIME + 0.1
## Where a zombie stands to tear planks, and where it lands after climbing in.
const OUTSIDE_DEPTH: float = 0.8
const INSIDE_DEPTH: float = 1.0
const SLOTS: int = 3
const SLOT_SPACING: float = 0.55
## How far back from the wall the waiting zombies stand, and how far apart.
const QUEUE_DEPTH: float = 2.0
const QUEUE_SPACING: float = 0.7

var planks: int = PLANKS
var _repair_cooldown: float = 0.0
var _slots: Array[Node3D] = []
var _vaulter: Node3D

@onready var _boards: Array[Node] = $Planks.get_children()


func _ready() -> void:
	super()
	add_to_group(&"barriers")
	_slots.resize(SLOTS)
	($Blocker as StaticBody3D).collision_layer = Layers.BARRIER
	($Blocker as StaticBody3D).collision_mask = 0


func _physics_process(delta: float) -> void:
	_repair_cooldown = maxf(_repair_cooldown - delta, 0.0)


func get_prompt(_player: Player) -> String:
	return "Hold to repair barrier [F]" if planks < PLANKS else ""


## Carpenter's repair_speed shortens both the hold and the server's cooldown.
func hold_interval(player: Player) -> float:
	return HOLD_INTERVAL / _repair_speed(player)


func _repair_speed(player: Player) -> float:
	return maxf(player.get_stat(&"repair_speed"), 0.01)


func interact(player: Player, _facts: Dictionary = {}) -> void:
	if planks >= PLANKS or _repair_cooldown > 0.0:
		return
	_repair_cooldown = REPAIR_TIME / _repair_speed(player)
	_set_planks(planks + 1)
	($RepairSound as AudioStreamPlayer3D).play()
	if player.session:
		player.session.economy.pay_repair(player)


func tear_plank() -> void:
	if planks > 0:
		_set_planks(planks - 1)
		($TearSound as AudioStreamPlayer3D).play()


## Server: back to full planks (Scrap Kit); clients get the planks through InteractionSync.
func rebuild() -> void:
	if planks < PLANKS:
		_set_planks(PLANKS)
		($RepairSound as AudioStreamPlayer3D).play()


func is_broken() -> bool:
	return planks == 0


func outside_point() -> Vector3:
	return global_position - global_basis.z * OUTSIDE_DEPTH


func inside_point() -> Vector3:
	return global_position + global_basis.z * INSIDE_DEPTH


## Where a drop lands when its zombie died at `killed_at`, outside this window: just
## inside, in line with where it fell, so players can reach it.
func drop_point(killed_at: Vector3) -> Vector3:
	var side: float = clampf(global_basis.x.dot(killed_at - global_position), -SLOT_SPACING, SLOT_SPACING)
	var point: Vector3 = inside_point() + global_basis.x * side
	point.y = killed_at.y
	return point


func net_state() -> Dictionary:
	return {"planks": planks}


func apply_net_state(state: Dictionary) -> void:
	var count: int = state.get("planks", planks)
	if count != planks:
		(get_node(^"RepairSound" if count > planks else ^"TearSound") as AudioStreamPlayer3D).play()
		_set_planks(count)


func _set_planks(count: int) -> void:
	planks = count
	for i: int in _boards.size():
		(_boards[i] as Node3D).visible = i < planks
	state_changed.emit()


## The slot `who` holds, or the nearest free one it now takes; -1 when all are taken.
func claim_slot(who: Node3D) -> int:
	var best: int = -1
	var best_distance: float = INF
	for i: int in SLOTS:
		if _slots[i] == who:
			return i
		if is_instance_valid(_slots[i]):
			continue
		var d: float = who.global_position.distance_squared_to(slot_point(i))
		if d < best_distance:
			best_distance = d
			best = i
	if best >= 0:
		_slots[best] = who
	return best


## Frees the slot and the vault for `who` (climbed in or died).
func release(who: Node3D) -> void:
	for i: int in SLOTS:
		if _slots[i] == who:
			_slots[i] = null
	if _vaulter == who:
		_vaulter = null


## True when `who` may climb through now; one zombie at a time.
func try_start_vault(who: Node3D) -> bool:
	if is_instance_valid(_vaulter) and _vaulter != who:
		return false
	_vaulter = who
	return true


func slot_point(index: int) -> Vector3:
	return outside_point() + global_basis.x * float(index - 1) * SLOT_SPACING


## Where a zombie without a slot waits; `lane` spreads the queue sideways.
func queue_point(lane: int) -> Vector3:
	var side: float = float(posmod(lane, 3) - 1) * QUEUE_SPACING
	return global_position - global_basis.z * QUEUE_DEPTH + global_basis.x * side
