"""Author the lab tech's rake on its shipping rig. Run blender -b -P tools/assets/shambler_attack.py.

Frames are at 60 Hz. The forward foot lands at 21, the torso overtakes it and the hand hits at 27.
The pelvis and shoulder start to recover while the elbow and fingers finish the swipe.
"""

import json
import math
import struct
from dataclasses import dataclass
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector

ROOT = Path(__file__).resolve().parents[2]
FPS = 60
FRAMES = (0, 9, 16, 21, 27, 32, 39, 48)
UP_AXIS = Matrix.Rotation(math.pi / 2, 4, "X")  # glTF +Y up to Blender +Z up

# Body-space pitch, yaw, bank in degrees about the glTF axes. The hand's longitudinal roll is separate.
BODY = {
    "pelvis": [(0, 0, 0), (-2, -9, -2), (1, -8, -4), (6, 5, -1), (6, 15, 3), (10, 17, 4), (4, 7, 2), (0, 0, 0)],
    "spine_01": [(3, 0, 0), (0, -5, -2), (-4, -8, -3), (2, -4, -3), (8, 4, 0), (14, 5, 4), (8, 2, 2), (3, 0, 0)],
    "spine_02": [(3, 0, 0), (0, -4, -2), (-4, -6, -3), (-2, -4, -3), (6, 8, 2), (13, 10, 6), (6, 4, 3), (3, 0, 0)],
    "head": [(0, 0, 0), (3, 9, 2), (4, 14, 4), (0, 7, 3), (-16, -14, -4), (-15, -17, -5), (-7, -7, -3), (0, 0, 0)],
    "clavicle_R": [(0, 2, 0), (0, -4, -2), (0, -8, -9), (0, -8, -10), (0, 12, -2), (0, 14, 2), (0, 5, 1), (0, 2, 0)],
    "upperarm_R": [
        (-18, 4, 29),
        (-10, -6, 5),
        (8, -13, -16),
        (4, -12, -25),
        (-103, 26, -6),
        (-73, 38, 10),
        (-34, 18, 15),
        (-18, 4, 29),
    ],
    "forearm_R": [
        (-15, 0, 0),
        (-38, 7, 0),
        (-64, 17, 0),
        (-69, 22, 0),
        (-13, 15, 0),
        (-15, 10, -2),
        (-27, 4, -3),
        (-15, 0, 0),
    ],
    "upperarm_L": [
        (-33, -10, -18),
        (-37, -3, -23),
        (-42, -8, -16),
        (-40, -6, -16),
        (8, 5, -24),
        (12, 9, -24),
        (-10, -6, -17),
        (-33, -10, -18),
    ],
    "forearm_L": [
        (-38, -22, 0),
        (-37, -18, 0),
        (-37, 0, 0),
        (-39, 0, 0),
        (-23, 0, 0),
        (-18, 0, 0),
        (-26, -16, 0),
        (-38, -22, 0),
    ],
}
ROLL = {
    "R": (-54, -48, -40, -40, -137, -122, -77, -54),
    "L": (54, 58, 74, 71, 55, 52, 55, 54),
}
# Blender x is lateral, -y is forward, z is vertical. Keep the rear knee soft enough to support the lunge.
HIPS = [
    (0, 0, -0.018),
    (-0.035, 0.025, -0.065),
    (-0.055, 0.045, -0.085),
    (-0.012, -0.022, -0.085),
    (0.045, -0.085, -0.078),
    (0.057, -0.16, -0.105),
    (0.025, -0.11, -0.078),
    (0, 0, -0.018),
]
LEAD_FOOT = [
    (0, 0, 0),
    (0, -0.025, 0.025),
    (0.015, -0.21, 0.072),
    (0.018, -0.29, 0),
    (0.018, -0.29, 0),
    (0.018, -0.29, 0),
    (0.014, -0.21, 0.06),
    (0, 0, 0),
]
FINGER_KEYS = [(0, 0.05), (9, 0.12), (16, 0.37), (21, 0.81), (25, 1.0), (27, 0.8), (32, 0.18), (39, 0.03), (48, 0.05)]


def body_turn(angles):
    pitch, yaw, bank = map(math.radians, angles)
    return Quaternion((0, 0, 1), yaw) @ Quaternion((1, 0, 0), pitch) @ Quaternion((0, -1, 0), bank)


@dataclass
class Strike:
    model: str
    name: str
    frames: tuple
    body: dict
    roll: dict
    hips: list
    lead_foot: list
    lead_side: str = "L"
    finger_keys: tuple = ()


def author(arm, strike):
    """Set the animator's breakdown poses, then smooth the root, arm and ankle trajectories between keys."""
    arm.animation_data_clear()
    bones = arm.pose.bones
    foot_target = bpy.data.objects.new("Lead ankle travel", None)
    bpy.context.scene.collection.objects.link(foot_target)
    for i, frame in enumerate(strike.frames):
        for name in [*strike.body, "hand_L", "hand_R"]:
            bone = bones[name]
            rest = bone.bone.matrix_local.to_quaternion()
            bend = body_turn(strike.body[name][i]) if name in strike.body else Quaternion()
            local = rest.inverted() @ bend @ rest
            if name.startswith(("hand_", "forearm_")):
                portion = 0.3 if name.startswith("hand_") else 0.7
                local @= Quaternion((0, 1, 0), math.radians(strike.roll[name[-1]][i]) * portion)
            if i:
                local.make_compatible(bone.rotation_quaternion)
            bone.rotation_mode = "QUATERNION"
            bone.rotation_quaternion = local
            bone.keyframe_insert(data_path="rotation_quaternion", frame=frame)
        hip = bones["pelvis"]
        hip.location = hip.bone.matrix_local.to_quaternion().inverted() @ Vector(strike.hips[i])
        hip.keyframe_insert(data_path="location", frame=frame)
        foot_target.location = strike.lead_foot[i]
        foot_target.keyframe_insert(data_path="location", frame=frame)
    arm.animation_data.action.name = strike.name
    return foot_target


def aim_segment(bone, rest_segment, direction):
    rest = bone.bone.matrix_local.to_quaternion()
    turn = rest_segment.normalized().rotation_difference(direction.normalized())
    bone.matrix = Matrix.Translation(bone.head.copy()) @ (turn @ rest).to_matrix().to_4x4()
    bpy.context.view_layer.update()


def plant_leg(bones, side, travel):
    thigh, shin, foot = (bones[f"{part}_{side}"] for part in ("thigh", "shin", "foot"))
    upper = shin.bone.head_local - thigh.bone.head_local
    lower = foot.bone.head_local - shin.bone.head_local
    ankle = foot.bone.head_local + travel
    hip = thigh.head.copy()
    line = ankle - hip
    axis = line.normalized()
    distance = min(line.length, upper.length + lower.length - 1e-5)
    along = (upper.length_squared - lower.length_squared + distance**2) / (2 * distance)
    pole = Vector((0.15 if side == "L" else -0.15, -1, 0))
    bend = (pole - axis * pole.dot(axis)).normalized()
    knee = hip + along * axis + bend * math.sqrt(max(0, upper.length_squared - along**2))
    aim_segment(thigh, upper, knee - hip)
    aim_segment(shin, lower, ankle - shin.head)
    foot.matrix = Matrix.Translation(foot.head.copy()) @ foot.bone.matrix_local.to_quaternion().to_matrix().to_4x4()
    bpy.context.view_layer.update()


def source_rest(model):
    """Read the shipped joint axes. A Blender glTF import may reorient a bone to point at its child."""
    with model.open("rb") as stream:
        stream.seek(12)
        size = struct.unpack("<I", stream.read(4))[0]
        stream.seek(20)
        doc = json.loads(stream.read(size))
    nodes = doc["nodes"]
    parents = {child: i for i, node in enumerate(nodes) for child in node.get("children", [])}

    def global_matrix(i):
        node = nodes[i]
        x, y, z, w = node.get("rotation", (0, 0, 0, 1))
        local = Matrix.LocRotScale(Vector(node.get("translation", (0, 0, 0))), Quaternion((w, x, y, z)), None)
        return global_matrix(parents[i]) @ local if i in parents else local

    return {nodes[i]["name"]: global_matrix(i) for i in doc["skins"][0]["joints"]}


def samples(arm, lead, rest, strike):
    tracks = {b.name: [] for b in arm.pose.bones if not b.name.startswith("sock_")}
    positions = []
    previous = {}
    for frame in range(strike.frames[-1] + 1):
        bpy.context.scene.frame_set(frame)
        for side in ("L", "R"):
            plant_leg(arm.pose.bones, side, lead.location if side == strike.lead_side else Vector())
        posed = {}
        for name, keys in tracks.items():
            bone = arm.pose.bones[name]
            deformation = bone.matrix @ bone.bone.matrix_local.inverted()
            posed[name] = UP_AXIS.inverted() @ deformation @ UP_AXIS @ rest[name]
            transform = posed[bone.parent.name].inverted() @ posed[name] if bone.parent else posed[name]
            q = transform.to_quaternion()
            if name in previous:
                q.make_compatible(previous[name])
            previous[name] = q
            keys.append((frame, (q.x, q.y, q.z, q.w)))
            if name == "pelvis":
                positions.append((frame, transform.translation))
    return tracks, positions


def track_lines(index, kind, path, samples):
    values = [n for frame, sample in samples for n in (frame / FPS, 1, *sample)]
    packed = ", ".join(f"{n:.7g}" for n in values)
    prefix = f"tracks/{index}/"
    return [
        prefix + f'type = "{kind}"',
        prefix + f'path = NodePath("{path}")',
        prefix + "loop_wrap = false",
        prefix + f"keys = PackedFloat32Array({packed})",
    ]


def bake(strike):
    model = ROOT / f"assets/models/zombies/{strike.model}.glb"
    output = ROOT / f"assets/animations/zombies/{strike.model}_attack.tres"
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(model), bone_heuristic="BLENDER")
    arm = next(o for o in bpy.context.selected_objects if o.type == "ARMATURE")
    bpy.context.scene.render.fps = FPS
    rotations, positions = samples(arm, author(arm, strike), source_rest(model), strike)
    lines = [
        '[gd_resource type="Animation" format=3]',
        "",
        "[resource]",
        f'resource_name = "{strike.name}"',
        f"length = {strike.frames[-1] / FPS:g}",
        "step = 0.016666667",
    ]
    for i, (bone, keys) in enumerate(rotations.items()):
        lines.extend(track_lines(i, "rotation_3d", "Skeleton3D:" + bone, keys))
    lines.extend(track_lines(len(rotations), "position_3d", "Skeleton3D:pelvis", positions))
    if strike.finger_keys:
        lines.extend(
            track_lines(
                len(rotations) + 1,
                "blend_shape",
                "Skeleton3D/Body:ReachFingers",
                [(frame, (amount,)) for frame, amount in strike.finger_keys],
            )
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    bake(Strike("shambler", "Shambler rake", FRAMES, BODY, ROLL, HIPS, LEAD_FOOT, finger_keys=tuple(FINGER_KEYS)))
