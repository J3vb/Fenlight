## Points for one player. Only Economy should change it.
class_name Wallet
extends Node

signal points_changed(total: int, delta: int)

var points: int = 0
var earned: int = 0


## Rewards count toward the run recap. Grants, refunds and spending only change the balance.
func earn(amount: int) -> void:
	earned += amount
	add(amount)


func set_points(value: int) -> void:
	var delta: int = value - points
	points = value
	points_changed.emit(points, delta)


func add(amount: int) -> void:
	if amount == 0:
		return
	points += amount
	points_changed.emit(points, amount)
