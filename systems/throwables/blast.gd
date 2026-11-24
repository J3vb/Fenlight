## Explosive damage around a point, run on the server: falls off with distance,
## stops at walls, hurts the thrower (capped) but never teammates, bursts Bloaters.
class_name Blast
extends RefCounted

## Rays start this far above the blast so a grenade lying on the floor still sees past it.
const LIFT: Vector3 = Vector3(0.0, 0.3, 0.0)
## Where a blast aims at a body: roughly the chest.
const CHEST: Vector3 = Vector3(0.0, 1.1, 0.0)
const MISSED: int = 0
const HIT: int = 1
const KILLED: int = 2


## 1 inside full_radius, falling linearly to 0 at radius.
static func falloff(data: ThrowableData, distance: float) -> float:
	if distance >= data.radius:
		return 0.0
	if distance <= data.full_radius:
		return 1.0
	return 1.0 - (distance - data.full_radius) / (data.radius - data.full_radius)


static func is_blocked(space: PhysicsDirectSpaceState3D, from: Vector3, to: Vector3) -> bool:
	var query: PhysicsRayQueryParameters3D = PhysicsRayQueryParameters3D.create(from, to, Layers.WORLD)
	return not space.intersect_ray(query).is_empty()


## Server only. `at` is any node in the blast's world (the grenade).
static func apply(at: Node3D, origin: Vector3, data: ThrowableData, thrower: Player) -> void:
	if not at.multiplayer.is_server():
		return
	var attacker: Player = thrower if is_instance_valid(thrower) else null
	var space: PhysicsDirectSpaceState3D = at.get_world_3d().direct_space_state
	var result: int = MISSED
	for node: Node in at.get_tree().get_nodes_in_group(&"enemies"):
		var zombie: Zombie = node as Zombie
		if zombie and zombie.multiplayer == at.multiplayer:
			result = maxi(result, _hit_zombie(zombie, origin, data, attacker, space))
	if attacker:
		_hit_thrower(attacker, origin, data, space)
		if result != MISSED:
			_confirm(attacker, result == KILLED)


## Returns MISSED, HIT or KILLED.
static func _hit_zombie(
	zombie: Zombie, origin: Vector3, data: ThrowableData, attacker: Player, space: PhysicsDirectSpaceState3D
) -> int:
	if zombie.health.is_dead or zombie.state == Zombie.State.DEAD:
		return MISSED
	var target: Vector3 = zombie.global_position + CHEST
	var share: float = falloff(data, origin.distance_to(target))
	if share <= 0.0 or is_blocked(space, origin + LIFT, target):
		return MISSED
	var amount: float = data.centre_damage * share
	if attacker:
		amount *= attacker.get_stat(&"grenade_damage")
	if zombie.data and zombie.data.burst_by_explosives:
		amount = maxf(amount, zombie.health.current)
	var info: DamageInfo = DamageInfo.create(amount, attacker, DamageInfo.Type.EXPLOSIVE)
	info.weapon_id = data.id
	info.position = target
	info.impulse = (target - origin).normalized() * 4.0
	zombie.health.take_damage(info)
	return KILLED if zombie.health.is_dead else HIT


static func _hit_thrower(
	thrower: Player, origin: Vector3, data: ThrowableData, space: PhysicsDirectSpaceState3D
) -> void:
	if not thrower.is_alive():
		return
	var target: Vector3 = thrower.global_position + CHEST
	var share: float = falloff(data, origin.distance_to(target))
	if share <= 0.0 or is_blocked(space, origin + LIFT, target):
		return
	var info: DamageInfo = DamageInfo.create(data.self_damage_max * share, thrower, DamageInfo.Type.EXPLOSIVE)
	info.weapon_id = data.id
	info.position = target
	thrower.take_damage(info)


static func _confirm(attacker: Player, killed: bool) -> void:
	if attacker.session and attacker.session.hit_claims:
		attacker.session.hit_claims.confirm_area_hit(attacker, killed)
	else:
		Events.hit_confirmed.emit(attacker, killed, false)
