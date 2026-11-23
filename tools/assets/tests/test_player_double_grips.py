"""Break-action grips keep a natural trigger reach and seated lower phalanges."""

import importlib
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bpy

# isort: split
import build_models
import grip_checks
import player_double_grips as double
import player_grip_model as grip
import player_lever_grip as lever
import pytest
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def _path(profile, index):
    across, _along, _inward = grip._frame(-1)
    root = Vector((-0.675, -0.017, 0.985)) + across * (index - 1.5) * 0.016
    start = grip._finger_path(root, -1, 0.032, index)[0]
    return double.finger_path(start, index, profile)


@pytest.mark.parametrize("profile", ["coachman_2b", "grubber_sawnoff"])
def test_break_action_index_starts_forward_without_dorsal_extension(profile):
    points = _path(profile, 0)
    grip_checks.assert_index_reach(points, extension=(-30, 30))
    assert grip_checks.path_length(points) < 0.110


@pytest.mark.parametrize(
    ("profile", "model", "part"),
    [
        ("coachman_2b", "coachman_model", "Stock"),
        ("grubber_sawnoff", "grubber_model", "Grip"),
    ],
)
def test_lower_phalanges_follow_actual_stock_surface(profile, model, part):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    importlib.import_module(model).build(build_models)
    bpy.context.view_layer.update()
    stock = bpy.data.objects[part]
    tree = BVHTree.FromPolygons(
        [stock.matrix_world @ vertex.co for vertex in stock.data.vertices],
        [list(face.vertices) for face in stock.data.polygons],
    )
    for index in (1, 2, 3):
        tube = grip._grip_tube(
            "ContactProbe",
            _path(profile, index),
            lever.finger_radii(index),
            stock.data.materials[0],
            -1,
        )
        for row in range(3, 14):
            ring = list(tube.data.vertices)[row * 12 : (row + 1) * 12]
            distance = min(tree.find_nearest(double._gun(tube.matrix_world @ vertex.co, profile))[3] for vertex in ring)
            assert distance < 0.006, "a clear finger must still rest against the stock"


@pytest.mark.parametrize("profile", ["coachman_2b", "grubber_sawnoff"])
def test_lower_mcp_starts_in_its_natural_flexion_plane(profile):
    across, along, inward = grip._frame(-1)
    for index in (1, 2, 3):
        points = _path(profile, index)
        for row in (1, 2):
            direction = points[row] - points[0]
            u, v, w = direction.dot(across), direction.dot(along), direction.dot(inward)
            flexion = math.degrees(math.atan2(w, v))
            abduction = math.degrees(math.atan2(u, math.hypot(v, w)))
            assert -15 < flexion < 80
            assert abs(abduction) < 30


def test_coachman_palm_seats_against_the_stock_neck():
    from test_player_hand_anatomy import hands

    palm = hands("world")["GlovePalmR"]
    importlib.import_module("coachman_model").build(build_models)
    bpy.context.view_layer.update()
    stock = bpy.data.objects["Stock"]
    tree = BVHTree.FromPolygons(
        [stock.matrix_world @ vertex.co for vertex in stock.data.vertices],
        [list(face.vertices) for face in stock.data.polygons],
    )
    points = [palm.matrix_world @ vertex.co for vertex in palm.data.vertices]
    points += [sum((points[i] for i in face.vertices), Vector()) / len(face.vertices) for face in palm.data.polygons]
    gaps = [tree.find_nearest(double._gun(point, "coachman_2b"))[3] for point in points]
    assert 0.0005 < min(gaps) < 0.0035, "fingertip contact alone must not leave the palm suspended"
    assert sum(distance < 0.005 for distance in gaps) >= 3, "the stock needs a palm contact patch"


def test_shell_carry_flexes_each_finger_toward_the_palm():
    import player_shell_grasp as carry

    across, along, inward = grip._frame(1)
    for index in range(4):
        points = carry.finger_path(Vector((0.675, -0.012, 0.985)) + across * ((index - 1.5) * 0.016), index)
        angles = []
        for start, end in zip((0, 3, 6), (3, 6, 9), strict=True):
            segment = points[end] - points[start]
            assert abs(segment.dot(across)) < 0.0001
            angles.append(math.degrees(math.atan2(segment.dot(inward), segment.dot(along))))
        assert 0 < angles[0] < angles[1] < angles[2] < 115
        assert 0.06 < grip_checks.path_length(points) < 0.09
        if index == 0:
            assert 0.011 < (points[-1] - carry.thumb_path()[-1]).length < 0.021
