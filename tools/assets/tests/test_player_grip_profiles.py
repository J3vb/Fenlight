"""Every generated weapon grip keeps connected anatomy, cap markers and shared topology."""

import itertools
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bpy

# isort: split
import bmesh
import build_models
import character_rig
import finish
import grip_checks
import player_arm_shapes as body
import player_arms_model as arms
import player_grip_profiles as profiles
import pytest
from mathutils import Vector
from mathutils.geometry import closest_point_on_tri
from test_player_arm_morphs import accessor, glb


@pytest.mark.parametrize("profile", profiles.PROFILES)
@pytest.mark.parametrize(("side", "sign"), [("R", -1), ("L", 1)])
def test_profile_curls_keep_attached_roots_closed_surfaces_and_real_tip_markers(profile, side, sign):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = arms._materials()
    skeleton = character_rig.build_armature()
    body.gloves(skeleton, mats)
    parts, metadata = arms._fingers(skeleton, mats, side, sign, profile, markers=False)
    bpy.context.view_layer.update()
    palm = bpy.data.objects["GlovePalm" + side]
    if profile == "rifle_ar":
        expected = 0.032 if side == "R" else 0.045
        assert (Vector(metadata["index"]) - Vector(metadata["thumb"])).length == pytest.approx(expected, abs=1e-6)
    for obj in parts:
        mesh = bmesh.new()
        mesh.from_mesh(obj.data)
        assert all(edge.is_manifold for edge in mesh.edges), (profile, obj.name)
        assert all(face.calc_area() > 1e-10 for face in mesh.faces), (profile, obj.name)
        assert mesh.calc_volume(signed=True) > 0, (profile, obj.name)
        mesh.free()
        if obj.name.startswith("FingerPad"):
            continue
        roots = []
        for vertex in list(obj.data.vertices)[:12]:
            point = palm.matrix_world.inverted() @ (obj.matrix_world @ vertex.co)
            hit, nearest, normal, _face = palm.closest_point_on_mesh(point)
            assert hit
            roots.append((point - nearest).dot(normal))
        assert min(roots) < -0.001, (profile, obj.name, "a morph must not detach a finger root")
    for obj, marker in ((parts[0], "index"), (parts[-1], "thumb")):
        centre = sum((obj.matrix_world @ vertex.co for vertex in list(obj.data.vertices)[-12:]), Vector()) / 12
        assert (centre - Vector(metadata[marker])).length < 1e-6


def test_finished_arm_export_has_all_zero_default_morphs_and_matching_metadata(tmp_path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    arms.build_player_arms()
    finish.finish()
    path = tmp_path / "player_arms.glb"
    build_models.export(str(path))
    document, binary = glb(path)
    metadata = json.loads(path.with_name("player_arm_grips.json").read_text())
    assert metadata["version"] == 1 and set(metadata["profiles"]) == set(profiles.PROFILES)
    mesh = document["meshes"][0]
    expected = ["grip_" + profile for profile in profiles.PROFILES if profile != "rifle_ar"]
    expected += ["carry_coachman_2b", "carry_grubber_sawnoff"]
    assert mesh["extras"]["targetNames"] == expected
    assert mesh["weights"] == [0.0] * len(expected)
    assert len(document["skins"][0]["joints"]) == 22
    assert {material["name"] for material in document["materials"]} == {"BodySuit", "BodyRubber", "BodyKnit"}
    for primitive in mesh["primitives"]:
        assert len(primitive["targets"]) == len(expected)
        base = primitive["attributes"]
        count = document["accessors"][base["POSITION"]]["count"]
        for target in primitive["targets"]:
            assert {"POSITION", "NORMAL"} <= target.keys()
            assert all(document["accessors"][target[field]]["count"] == count for field in ("POSITION", "NORMAL"))
        for weights in accessor(document, binary, base["WEIGHTS_0"]):
            assert sum(weights) == pytest.approx(1.0)
    assert_exported_cap_markers(document, binary, metadata)
    assert_morph_normals_face_outward(document, binary)


def assert_exported_cap_markers(document, binary, metadata):
    mesh = document["meshes"][0]
    names = mesh["extras"]["targetNames"]
    rubber = next(
        primitive
        for primitive in mesh["primitives"]
        if document["materials"][primitive["material"]]["name"] == "BodyRubber"
    )
    base = [Vector(point) for point in accessor(document, binary, rubber["attributes"]["POSITION"])]
    indices = [item[0] for item in accessor(document, binary, rubber["indices"])]
    poses = dict(metadata["profiles"])
    for profile in metadata["profiles"].values():
        if "carry" in profile:
            carry = profile["carry"]
            poses[carry["morph"]] = {"morph": carry["morph"], "L": carry, "R": profile["R"]}
    for name, profile in poses.items():
        points = base
        if profile["morph"]:
            target = rubber["targets"][names.index(profile["morph"])]["POSITION"]
            delta = accessor(document, binary, target)
            points = [point + Vector(change) for point, change in zip(base, delta, strict=True)]
        triangles = [
            tuple(points[index] for index in indices[start : start + 3]) for start in range(0, len(indices), 3)
        ]
        for side in ("R", "L"):
            for marker in ("index", "thumb"):
                x, y, z = profile[side][marker]
                tip = Vector((x, z, -y))
                distance = min((closest_point_on_tri(tip, *triangle) - tip).length for triangle in triangles)
                assert distance < 0.001, (name, side, marker, "exported marker must touch its morphed cap", distance)


def assert_morph_normals_face_outward(document, binary):
    """Bent fingers require target sharp splits; Basis normals alone can turn inward."""
    mesh = document["meshes"][0]
    for primitive in mesh["primitives"]:
        base = primitive["attributes"]
        vertices = np.array(accessor(document, binary, base["POSITION"]))
        normals = np.array(accessor(document, binary, base["NORMAL"]))
        faces = np.array(accessor(document, binary, primitive["indices"])).reshape(-1, 3)
        for name, target in zip(mesh["extras"]["targetNames"], primitive["targets"], strict=True):
            delta = np.array(accessor(document, binary, target["POSITION"]))
            points = (vertices + delta)[faces]
            directions = np.cross(points[:, 1] - points[:, 0], points[:, 2] - points[:, 0])
            lengths = np.linalg.norm(directions, axis=1)
            changed = np.max(np.abs(delta[faces]), axis=(1, 2)) > 1e-6
            valid = changed & (lengths > 1e-12)
            directions = directions[valid] / lengths[valid, None]
            target_normals = normals + np.array(accessor(document, binary, target["NORMAL"]))
            dots = np.sum(target_normals[faces[valid]] * directions[:, None, :], axis=2)
            assert not np.any(dots < -1e-4), (name, "a morphed corner normal faces into its triangle", dots.min())


def test_precision_thumb_does_not_make_an_oversized_loop_to_force_a_rifle_tip_gap():
    import player_precision_grip as precision

    points = precision.thumb_path()
    length = sum((second - first).length for first, second in itertools.pairwise(points))
    assert length < 0.160, "the stock thumb must not stretch around the stock to meet a rifle-only tip chord"


def test_angled_stop_support_uses_short_digits_instead_of_wrapping_the_entire_fore_end():
    import player_angled_grip as angled

    paths = [angled.finger_path(index) for index in range(4)] + [angled.thumb_path()]
    for points, maximum in zip(paths, (0.120, 0.110, 0.095, 0.090, 0.100), strict=True):
        length = sum((second - first).length for first, second in itertools.pairwise(points))
        assert length < maximum, "support digits must seat on the stop without an oversized curl around the guard"


def test_stock_trigger_finger_reaches_forward_without_dorsal_mcp_hyperextension():
    across, _along, _inward = arms._frame(-1)
    root = grip_checks.ROOT - across * 0.024
    grip_checks.assert_index_reach(arms._finger_path(root, -1, grip_checks.WIDTH, 0, "brenner_trench"))


def test_fitted_gloves_keep_rigid_hand_weights_after_join_and_cleanup(monkeypatch):
    """Forearm influence must not pull a fitted palm through its grip during reload."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    hand_points, fabric_points = {}, set()
    original = build_models.join_into
    rigid = ("GlovePalm", "KnucklePad", "GripFinger", "GripThumb", "FingerPad", "GloveStitch", "BackSeam")

    def record_parts(target, parts):
        for obj in [target, *parts]:
            if obj.type != "MESH":
                continue
            for vertex in obj.data.vertices:
                point = obj.matrix_world @ vertex.co
                key = tuple(round(value, 6) for value in point)
                if obj.name.startswith(rigid):
                    hand_points[key] = "hand_L" if point.x > 0 else "hand_R"
                elif obj.name.startswith(("Sleeve", "GloveCuff", "CuffRib", "WristStrap", "StrapKeeper")):
                    fabric_points.add(key)
        original(target, parts)

    monkeypatch.setattr(build_models, "join_into", record_parts)
    arms.build_player_arms()
    result = bpy.data.objects["PlayerArms"]
    checked, blended = set(), 0
    for vertex in result.data.vertices:
        key = tuple(round(value, 6) for value in result.matrix_world @ vertex.co)
        weights = {result.vertex_groups[group.group].name: group.weight for group in vertex.groups if group.weight}
        if key in hand_points:
            assert weights == {hand_points[key]: 1.0}, (key, "fitted glove moved with the forearm", weights)
            checked.add(key)
        elif key in fabric_points and len(weights) > 1:
            blended += 1
    assert len(checked) >= len(hand_points) * 0.95
    assert set(hand_points.values()) == {"hand_L", "hand_R"}
    assert blended > 0, "sleeves and wrist fabric still need a flexible transition"
