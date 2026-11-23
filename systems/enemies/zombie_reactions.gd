## Window crossings and falls for the three upright variants.
class_name ZombieReactions
extends RefCounted


static func vault(rig: ZombieRig, look_name: StringName, t: float, hop: float) -> void:
	match look_name:
		&"shambler_guard":
			# Left forearm bears weight while the right shoulder and trailing knee turn through the opening.
			rig.pose_part(&"Torso", Vector3(0.50 * hop, -0.43 * hop, 0.16 * hop))
			rig.pose_part(&"Head", Vector3(-0.28 * hop, 0.25 * hop, -0.09 * hop))
			rig.pose_part(&"ArmL", Vector3(-1.22 + 0.85 * t, -0.22, -0.24))
			rig.pose_grasp(&"forearm_L", &"hand_L", Vector3(-0.46 - 0.45 * hop, -0.2, 0), 0.95)
			rig.pose_part(&"ArmR", Vector3(-0.67 + 0.58 * hop, 0.11, 0.28))
			rig.pose_grasp(&"forearm_R", &"hand_R", Vector3(-0.65, 0.22, 0), -0.71)
			rig.pose_part(&"LegL", Vector3(-1.08 * hop, 0, -0.15 * hop))
			rig.pose_part(&"LegR", Vector3(-0.42 * hop, 0, -0.10 * hop))
			rig.pose_part(&"shin_L", Vector3(1.03 * hop, 0, 0))
			rig.pose_part(&"shin_R", Vector3(0.70 * hop, 0, 0))
		&"bloater":
			# Haul the belly up between two planted hands, then lower both feet together.
			var press: float = smoothstep(0.12, 0.64, t)
			rig.pose_part(&"Torso", Vector3(0.39 * hop, 0, 0))
			rig.pose_part(&"Head", Vector3(-0.25 * hop, 0, 0))
			rig.pose_part(&"ArmL", Vector3(-1.04 + 0.95 * press, -0.27, -0.22))
			rig.pose_part(&"ArmR", Vector3(-1.04 + 0.95 * press, 0.27, 0.22))
			rig.pose_grasp(&"forearm_L", &"hand_L", Vector3(-0.62 + 0.38 * press, -0.19, 0), 1.05)
			rig.pose_grasp(&"forearm_R", &"hand_R", Vector3(-0.62 + 0.38 * press, 0.19, 0), -1.05)
			rig.pose_part(&"LegL", Vector3(-0.82 * hop, 0, -0.16 * hop))
			rig.pose_part(&"LegR", Vector3(-0.82 * hop, 0, 0.16 * hop))
			rig.pose_part(&"shin_L", Vector3(1.13 * hop, 0, 0))
			rig.pose_part(&"shin_R", Vector3(1.13 * hop, 0, 0))
		&"glower":
			# Throw the right leg out first, with the left arm back as a counterweight.
			rig.pose_part(&"Torso", Vector3(0.74 * hop, 0.45 * hop, -0.26 * hop))
			rig.pose_part(&"Head", Vector3(-0.48 * hop, -0.29 * hop, 0.15 * hop))
			rig.pose_part(&"ArmL", Vector3(-0.49 + 0.91 * hop, -0.08, -0.17))
			rig.pose_part(&"ArmR", Vector3(-1.24 + 0.71 * t, 0.25, 0.18))
			rig.pose_grasp(&"forearm_L", &"hand_L", Vector3(-0.52, -0.16, 0), 0.7)
			rig.pose_grasp(&"forearm_R", &"hand_R", Vector3(-0.24 - 0.18 * hop, 0.19, 0), -0.92)
			rig.pose_part(&"LegL", Vector3(0.34 * hop, 0, 0))
			rig.pose_part(&"LegR", Vector3(-1.23 * hop, 0, 0))
			rig.pose_part(&"shin_L", Vector3(1.27 * hop, 0, 0))
			rig.pose_part(&"shin_R", Vector3(0.39 * hop, 0, 0))
		_:
			rig.pose_part(&"ArmL", Vector3(-1.4 + 0.9 * t, 0.0, -0.2))
			rig.pose_part(&"ArmR", Vector3(-1.4 + 0.9 * t, 0.0, 0.2))
			rig.pose_part(&"Torso", Vector3(0.6 * hop, 0.0, 0.0))
			rig.pose_part(&"LegL", Vector3(-0.9 * hop, 0.0, 0.0))
			rig.pose_part(&"LegR", Vector3(-0.6 * hop, 0.0, 0.0))
			rig.pose_part(&"Head", Vector3(-0.2 * hop, 0.0, 0.0))
			rig.pose_part(&"forearm_L", Vector3(-0.35 * hop, 0.0, 0.0))
			rig.pose_part(&"forearm_R", Vector3(-0.35 * hop, 0.0, 0.0))
			rig.pose_part(&"shin_L", Vector3(0.75 * hop, 0.0, 0.0))
			rig.pose_part(&"shin_R", Vector3(0.6 * hop, 0.0, 0.0))
			return
	rig.set_hip_offset(Vector3.ZERO)


static func relax_pose(look_name: StringName, slack: Dictionary[StringName, Vector3]) -> void:
	match look_name:
		&"shambler_guard":
			slack[&"ArmL"] = Vector3(0.20, -0.08, -0.24)
			slack[&"ArmR"] = Vector3(-0.24, 0.09, 0.20)
			slack[&"LegR"] = Vector3(-0.052, 0, 0.05)
			slack[&"LegL"] = Vector3(-0.29, 0, 0.09)
			slack[&"shin_L"] = Vector3(0.69, 0, 0)
			slack[&"forearm_L"] = Vector3(-0.43, -0.21, 0)
			slack[&"Torso"] = Vector3(0.20, -0.18, 0.15)
		&"bloater":
			slack[&"ArmL"] = Vector3(0.64, -0.08, -0.12)
			slack[&"ArmR"] = Vector3(0.60, 0.08, 0.12)
			slack[&"LegL"] = Vector3(-0.017, 0, -0.15)
			slack[&"LegR"] = Vector3(-0.017, 0, 0.15)
			slack[&"Head"] = Vector3(0.32, 0.14, 0)
		&"glower":
			slack[&"ArmL"] = Vector3(1.10, -0.19, -0.58)
			slack[&"forearm_L"] = Vector3(-0.26, -0.12, 0)
			slack[&"ArmR"] = Vector3(-1.40, 0.43, 0.37)
			slack[&"LegR"] = Vector3(-0.59, 0, 0.12)
			slack[&"shin_R"] = Vector3(1.00, 0, 0)
			slack[&"Head"] = Vector3(0.14, -0.48, -0.15)


static func fall(rig: ZombieRig, tween: Tween, look_name: StringName, side: float) -> void:
	var tipped: Vector3
	var seconds: float
	# End heights seat the vest, gas pods or hip on the ground when the body turns around its foot-level origin.
	match look_name:
		&"shambler_guard":
			tween.tween_property(rig, "rotation", Vector3(-0.26, 0, 0.23 * side), 0.15)
			tipped = Vector3(-1.49, 0.10 * side, 0.52 * side)
			seconds = 0.30
		&"bloater":
			tween.tween_property(rig, "rotation", Vector3(0.30, 0, 0.05 * side), 0.20)
			tipped = Vector3(1.56, 0, 0.12 * side)
			seconds = 0.25
		&"glower":
			tipped = Vector3(-0.58, 0, 1.48)
			seconds = 0.34
		_:
			tipped = Vector3(deg_to_rad(-85.0), 0.0, deg_to_rad(10.0) * side)
			seconds = 0.45
	tween.tween_property(rig, "rotation", tipped, seconds).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	match look_name:
		&"shambler_guard":
			tween.parallel().tween_property(rig, "position:y", 0.153, seconds)
		&"bloater":
			tween.parallel().tween_property(rig, "position:y", 0.394, seconds)
		&"glower":
			tween.parallel().tween_property(rig, "position:y", 0.17, seconds)
			tween.tween_property(rig, "rotation", Vector3(-0.51, 0, 1.54), 0.11)
