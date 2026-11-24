## Frag grenades in a real match (docs/plans/frag-grenades.md, step 1): a dropped
## frag kills a Shambler and pays the thrower; Resupply refills grenades.
extends GutTest

const SESSION: PackedScene = preload("res://systems/game/game_session.tscn")
const WALKER: EnemyData = preload("res://content/enemies/zombie_walker.tres")

var session: GameSession
var player: Player


func before_each() -> void:
	session = SESSION.instantiate() as GameSession
	session.profile_id = &""
	session.rng_seed = 11
	add_child_autofree(session)
	await wait_until(func() -> bool: return session.level.is_navigation_ready, 15.0, "navmesh baked")
	session.director.stop()
	player = session.get_players()[0]


func _live_grenades() -> int:
	var live: int = 0
	for child: Node in session.get_children():
		if child is Grenade and not child.is_queued_for_deletion():
			live += 1
	return live


func test_a_frag_kills_a_shambler_and_pays_the_thrower() -> void:
	var zombie: Zombie = session.spawner.spawn(WALKER, 1, session.wave_rules)
	zombie.set_physics_process(false)
	await wait_physics_frames(2)
	zombie.global_position = player.global_position + player.global_basis.x * 2.0
	await wait_physics_frames(2)
	var points: int = player.wallet.points
	player.grenades.fuse_left = 0.4
	player.grenades.throw(Vector3.ZERO)
	assert_eq(player.grenades.count, 1)
	await wait_until(func() -> bool: return _live_grenades() == 0, 3.0, "the frag went off")
	assert_true(zombie.health.is_dead, "a frag at 2 m kills a round-1 Shambler")
	assert_gt(player.wallet.points, points, "the kill pays the thrower")
	assert_true(player.is_alive(), "the thrower survives their own frag")
	assert_lt(player.health.current, player.health.max_health, "but it hurts")


func test_resupply_refills_grenades() -> void:
	player.grenades.count = 0
	var resupply: PowerUpData = Content.get_item(&"power_ups", &"resupply") as PowerUpData
	var pickup: PowerUp = session.power_up_drops.drop(resupply, player.global_position + Vector3(5, 0, 0))
	pickup.collect(player)
	assert_eq(player.grenades.count, player.grenades.data.carry)


func test_rolled_implant_increases_frag_damage_to_an_enemy() -> void:
	var zombie: Zombie = session.spawner.spawn(WALKER, 1, session.wave_rules)
	zombie.set_physics_process(false)
	zombie.global_position = Vector3(34, 0, 51)
	await wait_physics_frames(2)
	var centre: Vector3 = zombie.global_position + Blast.CHEST
	var data: ThrowableData = player.grenades.data
	zombie.health.reset(5000.0)
	Blast.apply(session.level, centre, data, player)
	var ordinary: float = 5000.0 - zombie.health.current
	assert_almost_eq(ordinary, data.centre_damage, 0.01)
	player.equip_gear([{"uid": "rolled", "aff": [["grenade_damage", 1, 1.0]]}])
	zombie.health.reset(5000.0)
	Blast.apply(session.level, centre, data, player)
	assert_almost_eq(5000.0 - zombie.health.current, ordinary * 1.20, 0.01)
