## Window barriers hand out 3 attack slots, send the rest to queue points
## further back, and let one zombie vault through at a time.
extends GutTest

const BARRIER: PackedScene = preload("res://systems/interactables/barrier.tscn")

var barrier: Barrier


func before_each() -> void:
	barrier = BARRIER.instantiate() as Barrier
	add_child_autofree(barrier)


func _zombie_at(x: float) -> Node3D:
	var node: Node3D = Node3D.new()
	add_child_autofree(node)
	node.global_position = barrier.outside_point() + Vector3(x, 0.0, 0.0)
	return node


func test_three_slots_then_queue() -> void:
	var a: Node3D = _zombie_at(-0.6)
	var b: Node3D = _zombie_at(0.0)
	var c: Node3D = _zombie_at(0.6)
	var d: Node3D = _zombie_at(0.0)
	assert_eq(barrier.claim_slot(a), 0, "nearest slot: left")
	assert_eq(barrier.claim_slot(c), 2, "nearest slot: right")
	assert_eq(barrier.claim_slot(b), 1)
	assert_eq(barrier.claim_slot(a), 0, "claiming again keeps the same slot")
	assert_eq(barrier.claim_slot(d), -1, "fourth zombie queues")
	barrier.release(b)
	assert_eq(barrier.claim_slot(d), 1, "freed slot goes to the queue")


func test_freed_zombie_frees_its_slot() -> void:
	var zombies: Array[Node3D] = [_zombie_at(-0.6), _zombie_at(0.0), _zombie_at(0.6)]
	for z: Node3D in zombies:
		barrier.claim_slot(z)
	zombies[1].free()
	assert_eq(barrier.claim_slot(_zombie_at(0.0)), 1, "a freed zombie's slot is free")


func test_slot_and_queue_points_sit_outside() -> void:
	for i: int in Barrier.SLOTS:
		var depth: float = (barrier.slot_point(i) - barrier.global_position).dot(barrier.global_basis.z)
		assert_almost_eq(depth, -Barrier.OUTSIDE_DEPTH, 0.001, "slot %d at the window" % i)
	assert_almost_eq(barrier.slot_point(0).distance_to(barrier.slot_point(2)), Barrier.SLOT_SPACING * 2.0, 0.001)
	for lane: int in 3:
		var depth: float = (barrier.queue_point(lane) - barrier.global_position).dot(barrier.global_basis.z)
		assert_almost_eq(depth, -Barrier.QUEUE_DEPTH, 0.001, "queue lane %d stands back" % lane)
	assert_ne(barrier.queue_point(0), barrier.queue_point(1), "queue lanes spread out")


func test_one_vaulter_at_a_time() -> void:
	var a: Node3D = _zombie_at(0.0)
	var b: Node3D = _zombie_at(0.5)
	assert_true(barrier.try_start_vault(a))
	assert_true(barrier.try_start_vault(a), "the vaulter keeps its turn")
	assert_false(barrier.try_start_vault(b), "second zombie waits")
	barrier.release(a)
	assert_true(barrier.try_start_vault(b), "next one goes once the first is through")


func test_drop_point_sits_inside_in_line_and_on_the_killed_zombies_floor() -> void:
	var killed_at: Vector3 = barrier.queue_point(0) + Vector3.DOWN * 0.2
	var point: Vector3 = barrier.drop_point(killed_at)
	assert_almost_eq((point - barrier.global_position).dot(barrier.global_basis.z), Barrier.INSIDE_DEPTH, 0.001)
	assert_almost_eq(barrier.global_basis.x.dot(point - barrier.global_position), -Barrier.SLOT_SPACING, 0.001)
	assert_almost_eq(point.y, killed_at.y, 0.001)
	var far_side: Vector3 = barrier.drop_point(barrier.global_position + barrier.global_basis.x * 5.0)
	assert_almost_eq(barrier.global_basis.x.dot(far_side - barrier.global_position), Barrier.SLOT_SPACING, 0.001)
