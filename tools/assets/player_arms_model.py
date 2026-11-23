"""First-person thermal sleeves and reinforced grip gloves on the shared body rig."""

import json
import math

import bpy

# isort: split
import bmesh
import body_parts as soft
import character_rig as rig
import gear_paint as paint
import player_arm_shapes as body
import player_grip_profiles as profiles
import player_shell_grasp as shell_grasp
from mathutils import Matrix, Vector
from player_arm_morphs import add_variant
from player_grip_model import (
    FINGER_RADII as FINGER_RADII,
)
from player_grip_model import (
    FINGER_SCALES as FINGER_SCALES,
)
from player_grip_model import (
    GRIP_HALVES as GRIP_HALVES,
)
from player_grip_model import (
    _bore_point as _bore_point,
)
from player_grip_model import (
    _finger_pad as _finger_pad,
)
from player_grip_model import (
    _finger_path as _finger_path,
)
from player_grip_model import (
    _finger_radii as _finger_radii,
)
from player_grip_model import (
    _firing_curl as _firing_curl,
)
from player_grip_model import (
    _frame as _frame,
)
from player_grip_model import (
    _grip_axes as _grip_axes,
)
from player_grip_model import (
    _grip_centre as _grip_centre,
)
from player_grip_model import (
    _grip_tube as _grip_tube,
)
from player_grip_model import (
    _thumb_path as _thumb_path,
)
from player_wrist_fit import add_wrist_variants


def _materials():
    from build_models import material, srgb

    return {
        "suit": material("BodySuit", srgb("#5F6D68"), roughness=0.88),
        "knit": material("BodyKnit", srgb("#2F393B"), roughness=0.96),
        "rubber": material("BodyRubber", srgb("#1C2122"), roughness=0.78),
    }


def _sleeves(mats):
    """Cut the body's actual sleeve surface halfway down each upper arm."""
    source = body.sleeve_surface(mats["suit"])
    for side, sign in (("L", 1), ("R", -1)):
        data = source.data.copy()
        obj = bpy.data.objects.new("Sleeve" + side, data)
        bpy.context.collection.objects.link(obj)
        bm = bmesh.new()
        bm.from_mesh(data)
        bmesh.ops.bisect_plane(
            bm,
            geom=[*bm.verts, *bm.edges, *bm.faces],
            plane_co=(sign * 0.30, 0, 0),
            plane_no=(sign, 0, 0),
            clear_inner=True,
            dist=1e-6,
        )
        bmesh.ops.holes_fill(bm, edges=[edge for edge in bm.edges if edge.is_boundary])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bm.to_mesh(data)
        bm.free()
        paint.zone(obj, paint.ZONE_MAIN)
    bpy.data.objects.remove(source, do_unlink=True)


def _tip_marker(name, point, armature, side):
    obj = bpy.data.objects.new(name + "_" + side, None)
    bpy.context.collection.objects.link(obj)
    obj.parent, obj.parent_type, obj.parent_bone = armature, "BONE", "hand_" + side
    bpy.context.view_layer.update()
    obj.matrix_world = Matrix.Translation(point)


def _fingers(armature, mats, side, sign, profile="rifle_ar", markers=True, carrying=False):
    across, _along, _inward = _frame(sign)
    diameter = 0.032 if side == "R" else 0.045
    parts = []
    for index in range(4):
        offset = (index - 1.5) * 0.016
        root = Vector((sign * 0.675, -0.017 if side == "R" else -0.012, 0.985)) + across * offset
        points = (
            shell_grasp.finger_path(root, index) if carrying else _finger_path(root, sign, diameter, index, profile)
        )
        radii = _finger_radii(diameter, index, profile)
        finger = _grip_tube("GripFinger" + side, points, radii, mats["rubber"], sign)
        parts.append(finger)
        paint.zone(finger, paint.ZONE_ACCENT)
        joints = (4, 10) if side == "R" else (3, 6)
        if profile == "coachman_2b" and side == "R":
            joints = {2: (5, 10), 3: (4, 7)}.get(index, joints)
        for joint in joints:
            pad = _finger_pad(points, radii, joint, sign, mats["knit"])
            parts.append(pad)
            paint.zone(pad, paint.ZONE_ACCENT)
        if index == 0:
            index_tip = points[-1]
            centre = _grip_centre(root, sign, diameter, profile)
            if markers:
                _tip_marker("GripIndexTip", index_tip, armature, side)
    points = shell_grasp.thumb_path() if carrying else _thumb_path(index_tip, centre, sign, diameter, profile)
    radii = [0.014, 0.014, 0.013, 0.011, 0.008, 0.002]
    if side == "R":
        radii = [0.014, 0.014, 0.013, 0.012, 0.011, 0.010, 0.008, 0.006, 0.004, 0.002]
    thumb = _grip_tube("GripThumb" + side, points, radii, mats["rubber"], sign)
    parts.append(thumb)
    paint.zone(thumb, paint.ZONE_ACCENT)
    if markers:
        _tip_marker("GripThumbTip", points[-1], armature, side)
    return parts, {
        "center": [sign * 0.675, -profiles.section(profile, diameter)[2], 0.985],
        "index": list(index_tip),
        "thumb": list(points[-1]),
    }


def _grip_variants(armature, mats, base, metadata):
    for profile in profiles.PROFILES:
        if profile == "rifle_ar":
            continue
        key = "grip_" + profile
        info = {"morph": key}
        for side, sign in (("L", 1), ("R", -1)):
            parts, info[side] = _fingers(armature, mats, side, sign, profile, markers=False)
            add_variant(base[side], parts, key)
        metadata[profile] = info
    for profile in ("coachman_2b", "grubber_sawnoff"):
        key = "carry_" + profile
        parts, carry = _fingers(armature, mats, "L", 1, profile, markers=False, carrying=True)
        add_variant(base["L"], parts, key)
        parts, _ = _fingers(armature, mats, "R", -1, profile, markers=False)
        add_variant(base["R"], parts, key)
        metadata[profile]["carry"] = {"morph": key, "index": carry["index"], "thumb": carry["thumb"]}
    bpy.context.scene["player_arm_grips"] = json.dumps({"version": 1, "profiles": metadata}, allow_nan=False)


def _wrist_details(mats, side, sign):
    _across, along, inward = _frame(sign)
    centre = Vector((sign * 0.603, 0, 1.057))
    # Same round knitted cuff as the body, with a narrow rubber retention strap.
    rib = soft.ellipse_ring("CuffRib" + side, (0, 0, 0), (0.047, 0.047), 0.0015, mats["knit"])
    rib.rotation_euler = Vector((0, 1, 0)).rotation_difference(along).to_euler()
    rib.location = centre + along * 0.008
    paint.zone(rib, paint.ZONE_ACCENT)
    strap = soft.pad("WristStrap" + side, (0.054, 0.009, 0.021), centre - inward * 0.046, mats["rubber"], 0.003)
    strap.rotation_euler.y = -sign * math.pi / 4
    paint.zone(strap, paint.ZONE_ACCENT)
    keeper = soft.pad("StrapKeeper" + side, (0.010, 0.004, 0.027), centre - inward * 0.052, mats["knit"], 0.002)
    keeper.rotation_euler.y = -sign * math.pi / 4
    paint.zone(keeper, paint.ZONE_TRIM)


def _stitching(mats, side, sign):
    across, along, inward = _frame(sign)
    palm = Vector((sign * 0.649, 0, 1.011))
    lines = [
        ("GloveStitch", edge * 0.031, [(index - 4) * 0.007 + delta for delta in (0, 0.0035)], 0.0008)
        for edge in (-1, 1)
        for index in range(9)
    ]
    lines += [("BackSeam", (index - 1.5) * 0.016, [-0.020, 0.0025, 0.025], 0.0007) for index in range(4)]
    for name, u, distances, radius in lines:
        points = []
        for v in distances:
            depth = 0.027 * math.sqrt(max(0, 1 - (u / 0.046) ** 2 - (v / 0.055) ** 2))
            points.append(palm + across * u + along * v - inward * (depth + 0.0003))
        seam = soft.tube(name + side, points, [radius] * len(points), mats["knit"], 5)
        paint.zone(seam, paint.ZONE_ACCENT)


def _bind_parts(objects, armature):
    """The fitted glove follows the hand; sleeve and cuff fabrics retain joint blending."""
    rigid = ("GlovePalm", "KnucklePad", "GripFinger", "GripThumb", "FingerPad", "GloveStitch", "BackSeam")
    bpy.context.view_layer.update()
    for obj in objects:
        if obj.name.startswith(rigid):
            point = obj.matrix_world @ obj.data.vertices[0].co
            rig.bind_rigid(obj, armature, "hand_L" if point.x > 0 else "hand_R")
        else:
            rig.bind(obj, armature, blend=0.08)


def build_player_arms():
    """Keep the shared A-pose rig and author the weapon-specific grip shapes."""
    from build_models import join_into

    mats = _materials()
    armature = rig.build_armature()
    _sleeves(mats)
    body.gloves(armature, mats)
    # Preserve the world body's palms, knit cuffs and knuckle pads; replace only curls.
    for obj in list(bpy.context.scene.objects):
        if obj.name.startswith(("GloveFinger", "GloveThumb")):
            bpy.data.objects.remove(obj, do_unlink=True)
    base, metadata = {}, {"rifle_ar": {"morph": ""}}
    for side, sign in (("L", 1), ("R", -1)):
        base[side], metadata["rifle_ar"][side] = _fingers(armature, mats, side, sign)
        _wrist_details(mats, side, sign)
        _stitching(mats, side, sign)
    _grip_variants(armature, mats, base, metadata)
    objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    add_wrist_variants(objects)
    _bind_parts(objects, armature)
    target = objects[0]
    join_into(target, objects[1:])
    target.name = "PlayerArms"
    soft.clean(target)
    bpy.context.view_layer.update()
