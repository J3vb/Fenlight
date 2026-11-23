## Records one hit and one evaded swing through the player camera in the Halcyon look corridor.
## godot --fixed-fps 30 --write-movie /tmp/shambler.avi tools/shambler_attack_review.tscn
extends Node3D

var _player: Player
var _walker: Zombie
var _swings: int = 0
var _hits: int = 0
var _swinging: bool = false
var _retreat: float = 0.0
var _pursuit: float = 0.0
var _elapsed: float = 0.0
var _input: InputFrame = InputFrame.new()


func _ready() -> void:
	$Corridor/Zombies.free()
	$Corridor/Camera3D.free()
	_player = (load("res://systems/player/player.tscn") as PackedScene).instantiate() as Player
	_player.position = Vector3(0, 0.02, -2)
	add_child(_player)
	_player.set_physics_process(false)
	_player.local_input.enabled = false
	_player.camera_rig.rotation.x = deg_to_rad(-11.0)
	_player.weapons.give(load("res://content/weapons/hollis_44.tres") as WeaponData)
	_player.health.damaged.connect(_on_hit)
	# The reference corridor is an art scene. Supply its straight walking lane for the regular chase AI.
	var nav: NavigationMesh = NavigationMesh.new()
	nav.vertices = PackedVector3Array([Vector3(-1, 0, 1.8), Vector3(1, 0, 1.8), Vector3(1, 0, -8), Vector3(-1, 0, -8)])
	nav.add_polygon(PackedInt32Array([3, 2, 1, 0]))
	var lane: NavigationRegion3D = NavigationRegion3D.new()
	lane.navigation_mesh = nav
	add_child(lane)
	await get_tree().physics_frame
	await get_tree().physics_frame
	var data: EnemyData = load("res://content/enemies/zombie_walker.tres") as EnemyData
	_walker = data.scene.instantiate() as Zombie
	_walker.setup(data, 1, 1.0, 1.0, 1.0, RandomNumberGenerator.new())
	(_walker.get_node("Visual") as ZombieRig).look = 0
	_walker.position = Vector3(0, 0.02, -5.3)
	_walker.rotation.y = PI
	add_child(_walker)
	_walker.visual.position.y = 0.0
	_walker.restart_chase()


func _on_hit(_info: DamageInfo) -> void:
	_hits += 1
	if _swings != 1 or _hits != 1:
		push_error("Only the first swing should damage the player")
		get_tree().quit(1)
	print("Shambler hit at %.2f s, player HP %.0f" % [_elapsed, _player.health.current])


func _physics_process(delta: float) -> void:
	if _walker == null:
		return
	_elapsed += delta
	var attacking: bool = _walker.state == Zombie.State.ATTACKING
	if attacking and not _swinging:
		_swings += 1
		print("Swing %d starts at %.2f s" % [_swings, _elapsed])
		if _swings == 2:
			_retreat = 0.6
	_swinging = attacking
	_input.move = Vector2.DOWN if _retreat > 0.0 else Vector2.ZERO
	_player.apply_frame(_input, delta)
	_retreat -= delta
	if _swings == 2 and _walker.state == Zombie.State.CHASING:
		_pursuit += delta
		if _pursuit >= 0.85 and _hits == 1:
			print("Second swing missed, chase resumed. Player HP %.0f" % _player.health.current)
			get_tree().quit()
	if _elapsed > 10.0:
		push_error("Review expected two swings, one hit and a resumed chase")
		get_tree().quit(1)
