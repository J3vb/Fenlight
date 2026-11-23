## Pursuit poses for the upright models, sampled at their footstep phase.
class_name ZombieGait
extends RefCounted


static func cadence(look_name: StringName) -> float:
	match look_name:
		&"shambler_guard":
			return 1.05
		&"bloater":
			return 0.84
		&"glower":
			return 1.14
	return 1.0


static func pose(rig: ZombieRig, look_name: StringName, phase: float, stride: float, reach: float) -> void:
	var swing: float = sin(phase) * stride
	match look_name:
		&"shambler_guard":
			_guard(rig, phase, swing, stride, reach)
		&"bloater":
			_bloater(rig, phase, swing, stride, reach)
		&"glower":
			_glower(rig, phase, swing, stride, reach)
		_:
			_shambler(rig, phase, stride, reach)


static func _shambler(rig: ZombieRig, phase: float, stride: float, reach: float) -> void:
	var swing: float = sin(phase) * stride
	rig.pose_part(&"LegL", Vector3(swing * 0.55, 0.0, 0.0))
	rig.pose_part(&"LegR", Vector3(-swing * 0.55, 0.0, 0.0))
	var lift: float = -0.35 * reach
	rig.pose_part(&"ArmL", Vector3(lift - swing * 0.2 - 0.38 + sin(phase * 0.7) * 0.06, -0.28, -0.23))
	rig.pose_part(&"ArmR", Vector3(lift + swing * 0.24 + 0.05 + cos(phase * 0.8) * 0.06, 0.16, 0.35))
	rig.pose_part(&"Torso", Vector3(0.1 * stride + 0.05 * reach, 0.0, sin(phase) * 0.07))
	rig.pose_part(&"Head", Vector3(0.0, 0.0, sin(phase * 0.5) * 0.18))
	rig.pose_grasp(&"forearm_L", &"hand_L", Vector3(-0.54 - 0.19 * reach, -0.38, 0.0), 0.65 + 0.30 * reach)
	rig.pose_grasp(&"forearm_R", &"hand_R", Vector3(-0.40 - 0.16 * reach, 0.0, 0.0), -0.65 - 0.30 * reach)
	rig.pose_part(&"shin_L", Vector3(maxf(0.0, swing) * 0.3, 0.0, 0.0))
	rig.pose_part(&"shin_R", Vector3(maxf(0.0, -swing) * 0.3, 0.0, 0.0))
	var bob: Vector3 = Vector3.DOWN * absf(cos(phase)) * 0.035 * stride
	rig.set_hip_offset(bob)


## Leads with a bent left arm, keeping the rear hand close and the head facing forward as the vest turns.
static func _guard(rig: ZombieRig, phase: float, swing: float, stride: float, reach: float) -> void:
	rig.pose_part(&"LegL", Vector3(0.49 * swing, 0, 0))
	rig.pose_part(&"LegR", Vector3(-0.49 * swing, 0, 0))
	rig.pose_part(&"shin_L", Vector3(0.37 * maxf(swing, 0), 0, 0))
	rig.pose_part(&"shin_R", Vector3(0.37 * maxf(-swing, 0), 0, 0))
	rig.pose_part(&"Torso", Vector3(0.07 + 0.05 * stride, -0.17 + 0.12 * swing, 0.025 * swing))
	rig.pose_part(&"Head", Vector3(-0.05, 0.12 - 0.09 * swing, 0))
	rig.pose_part(&"ArmL", Vector3(-0.36 - 0.38 * reach - 0.10 * swing, -0.16, -0.27))
	rig.pose_part(&"ArmR", Vector3(-0.20 + 0.22 * swing - 0.13 * reach, 0.12, 0.35))
	rig.pose_grasp(&"forearm_L", &"hand_L", Vector3(-1.22 - 0.10 * reach, -0.36, 0), 0.86)
	rig.pose_grasp(&"forearm_R", &"hand_R", Vector3(-0.85 + 0.12 * swing, 0.20, 0), -0.85)
	rig.set_hip_offset(Vector3(0, -0.030 * absf(cos(phase)) * stride, 0))


## Transfers weight over each foot. The low hands and head trail the lateral movement of the belly.
static func _bloater(rig: ZombieRig, phase: float, swing: float, stride: float, reach: float) -> void:
	var shift: float = cos(phase) * stride
	rig.pose_part(&"LegL", Vector3(0.44 * swing, 0, -0.035 - 0.05 * shift))
	rig.pose_part(&"LegR", Vector3(-0.44 * swing, 0, 0.035 - 0.05 * shift))
	rig.pose_part(&"shin_L", Vector3(0.25 * maxf(swing, 0), 0, 0))
	rig.pose_part(&"shin_R", Vector3(0.25 * maxf(-swing, 0), 0, 0))
	rig.pose_part(&"Torso", Vector3(-0.04 + 0.07 * reach, 0.09 * swing, 0.13 * shift))
	rig.pose_part(&"Head", Vector3(0.04, -0.05 * swing, -0.09 * shift))
	rig.pose_part(&"ArmL", Vector3(-0.12 - 0.25 * reach - 0.15 * swing, -0.14, -0.30))
	rig.pose_part(&"ArmR", Vector3(-0.12 - 0.25 * reach + 0.15 * swing, 0.14, 0.30))
	rig.pose_grasp(&"forearm_L", &"hand_L", Vector3(-0.43 - 0.18 * reach, -0.20, 0), 0.65)
	rig.pose_grasp(&"forearm_R", &"hand_R", Vector3(-0.43 - 0.18 * reach, 0.20, 0), -0.65)
	rig.set_hip_offset(Vector3(0.059 * shift, -0.045 * absf(swing), 0))


## Runs pitched over flexed knees. The elbows pump past each other and the head steadies against the chest.
static func _glower(rig: ZombieRig, phase: float, swing: float, stride: float, reach: float) -> void:
	var bounce: float = absf(cos(phase)) * stride
	rig.pose_part(&"LegL", Vector3(-0.14 + 0.72 * swing, 0, 0))
	rig.pose_part(&"LegR", Vector3(-0.14 - 0.72 * swing, 0, 0))
	rig.pose_part(&"shin_L", Vector3(0.29 + 0.64 * maxf(swing, 0), 0, 0))
	rig.pose_part(&"shin_R", Vector3(0.29 + 0.64 * maxf(-swing, 0), 0, 0))
	rig.pose_part(&"Torso", Vector3(0.21 + 0.18 * stride, 0.19 * swing, -0.07 + 0.05 * swing))
	rig.pose_part(&"Head", Vector3(-0.16 - 0.13 * stride, -0.12 * swing, 0.06))
	rig.pose_part(&"ArmL", Vector3(-0.30 - 0.54 * swing - 0.21 * reach, -0.17, -0.25))
	rig.pose_part(&"ArmR", Vector3(-0.38 + 0.54 * swing - 0.24 * reach, 0.18, 0.32))
	rig.pose_grasp(&"forearm_L", &"hand_L", Vector3(-0.77 - 0.17 * swing, -0.22, 0), 0.90)
	rig.pose_grasp(&"forearm_R", &"hand_R", Vector3(-0.90 + 0.17 * swing, 0.21, 0), -0.94)
	rig.set_hip_offset(Vector3(0, -0.030 - 0.037 * bounce, 0))
