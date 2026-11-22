## Kills outside a window (in the zombie's spawn area) drop loot and power-ups just
## inside the window, where players can pick them up; kills inside drop where they fell.
extends GutTest

const SESSION: PackedScene = preload("res://systems/game/game_session.tscn")

var session: GameSession
var player: Player
var barrier: Barrier
var walker: EnemyData


func before_each() -> void:
	session = SESSION.instantiate() as GameSession
	session.profile_id = &""
	session.rng_seed = 7
	add_child_autofree(session)
	await wait_until(func() -> bool: return session.level.is_navigation_ready, 15.0, "navmesh baked")
	session.director.stop()
	player = session.get_players()[0]
	barrier = get_tree().get_first_node_in_group(&"barriers") as Barrier
	walker = Content.get_item(&"enemies", &"zombie_walker") as EnemyData
	session.loot.drop_chance_override = 1.0
	session.power_up_drops.drop_chance = 1.0


func _kill(at: Vector3, window: Barrier) -> void:
	var zombie: Zombie = session.spawner.spawn(walker, 1, session.director.rules)
	zombie.barrier = window
	zombie.global_position = at
	zombie.health.take_damage(DamageInfo.create(zombie.health.current + 1.0, player))


func _loot_drops() -> Array[LootDrop]:
	var out: Array[LootDrop] = []
	for node: Node in session.loot.get_children():
		if node is LootDrop:
			out.append(node as LootDrop)
	return out


func _power_up() -> PowerUp:
	for node: Node in session.level.get_children():
		if node is PowerUp and not node.is_queued_for_deletion():
			return node as PowerUp
	return null


## How far into the room a point is, measured from the window plane (+Z faces in).
func _depth(point: Vector3) -> float:
	return (point - barrier.global_position).dot(barrier.global_basis.z)


func test_kill_in_the_spawn_area_drops_inside_the_window() -> void:
	var queued: Vector3 = barrier.queue_point(2)
	_kill(queued, barrier)
	assert_eq(_loot_drops().size(), 1, "the kill still pays out")
	var loot: Vector3 = _loot_drops()[0].global_position
	assert_lt(_depth(queued), 0.0, "the zombie died outside, in its spawn area")
	assert_almost_eq(_depth(loot), Barrier.INSIDE_DEPTH, 0.01, "loot lands inside the window")
	assert_lt(absf(barrier.global_basis.x.dot(loot - barrier.global_position)), Barrier.SLOT_SPACING + 0.01)
	assert_almost_eq(loot.y, queued.y, 0.01, "on the zombie's floor")
	assert_not_null(_power_up())
	assert_almost_eq(
		_power_up().global_position, loot + Vector3.UP * 0.8, Vector3.ONE * 0.01, "power-up lands there too"
	)


func test_drop_from_inside_the_window_is_in_line_with_the_kill() -> void:
	var at_slot: Vector3 = barrier.slot_point(0)
	_kill(at_slot, barrier)
	assert_eq(_loot_drops().size(), 1)
	var loot: Vector3 = _loot_drops()[0].global_position
	var side: float = barrier.global_basis.x.dot(at_slot - barrier.global_position)
	assert_almost_eq(barrier.global_basis.x.dot(loot - barrier.global_position), side, 0.01, "same side of the window")


func test_kill_in_the_room_drops_where_it_fell() -> void:
	var in_room: Vector3 = Vector3(40, 0, 40)
	_kill(in_room, null)
	assert_eq(_loot_drops().size(), 1)
	assert_almost_eq(_loot_drops()[0].global_position, in_room, Vector3.ONE * 0.01)
