"""Tripo zombies (tools/assets/tripo/zombies.json, F-28 step 1, F-86): intake `--kind zombie` output passes the rules.

Run from the repo root: python -m pytest tools/assets/tests/test_tripo_zombies.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bpy

# isort: split
import bmesh
import check_models
import pytest
import tripo_crawler
import tripo_intake
import zombie_checks

MANIFEST = os.path.join(check_models.REPO, "tools", "assets", "tripo", "zombies.json")
with open(MANIFEST, encoding="utf-8") as text:
    ROWS = json.load(text)


def _model(row):
    return os.path.join(check_models.REPO, "assets", "models", row["folder"], row["name"] + ".glb")


def test_zombie_kind_matches_the_zombie_folder_budget():
    budget, _size, height = tripo_intake.KINDS["zombie"]
    assert budget == check_models.BUDGETS["zombies"][0]
    assert height == 1.7


def test_manifest_rows_are_zombies_with_rules():
    assert [row["name"] for row in ROWS] == ["glower", "shambler", "shambler_guard", "bloater", "crawler"]
    for row in ROWS:
        assert row["kind"] == "zombie" and row["folder"] == "zombies"
        assert row["name"] in zombie_checks.JOINTS and row["name"] in zombie_checks.TRIANGLES


@pytest.mark.parametrize("row", ROWS, ids=[row["name"] for row in ROWS])
def test_committed_zombie_passes_every_model_rule(row):
    assert check_models.check_model(_model(row)) == []


@pytest.mark.parametrize("row", ROWS, ids=[row["name"] for row in ROWS])
def test_committed_zombie_is_placed_with_head_center_behind_the_eyes(row):
    objects = check_models.load_glb(_model(row))
    nodes = {obj.name: obj for obj in objects}
    arm = next(obj for obj in objects if obj.type == "ARMATURE")
    assert len(arm.data.bones) == 22
    assert [obj.name for obj in objects if obj.type == "MESH"] == ["Body"]
    assert nodes["Body"].data.materials[0].name.startswith(zombie_checks.BAKED)
    low, high = check_models.bounds([nodes["Body"]])
    assert low.z == pytest.approx(0.0, abs=0.01)
    if row.get("crawler"):
        assert high.z - low.z < 0.8, "the Crawler lies prone"
        assert nodes["Crawler"].parent_bone == "pelvis", "ZombieRig finds the crawl rest by this marker"
        body = nodes["Body"]
        groups = {g.index: g.name for g in body.vertex_groups}
        weighted = {groups[e.group] for v in body.data.vertices for e in v.groups if e.weight > 0.0}
        assert not any(name.startswith(("thigh_", "shin_", "foot_")) for name in weighted), "no legs left"
    else:
        assert high.z - low.z == pytest.approx(row["height"], abs=0.01)
    center = nodes["HeadCenter"]
    assert center.parent == arm and center.parent_type == "BONE" and center.parent_bone == "head"
    eyes = nodes["Eyes"].matrix_world.translation
    assert center.matrix_world.translation.y > eyes.y, "HeadCenter sits behind the eyes (Godot -Z)"
    assert center.matrix_world.translation.z == pytest.approx(eyes.z, abs=0.02)


def test_baked_zombie_rules_want_one_body_mesh_and_only_the_baked_material():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.mesh.primitive_cube_add()
    cube = bpy.context.active_object
    cube.name = "Torso"
    cube.data.materials.append(bpy.data.materials.new(zombie_checks.BAKED))
    cube.data.materials.append(bpy.data.materials.new("ZombieSkin"))
    errors = zombie_checks._check_baked([cube], [cube])
    assert any("one mesh named 'Body'" in error for error in errors)
    assert any("only the ZombieBaked material" in error for error in errors)
    assert any("HeadCenter" in error for error in errors)


def test_crawler_pass_cuts_the_legs_and_caps_them_facing_out():
    objects = check_models.load_glb(_model(ROWS[1]))
    arm = next(obj for obj in objects if obj.type == "ARMATURE")
    body = next(obj for obj in objects if obj.name == "Body")
    tripo_intake.weld(body)
    cut = tripo_crawler.cut_legs(arm, body)
    tripo_crawler.stumps_on_pelvis(arm, body)
    mesh = bmesh.new()
    mesh.from_mesh(body.data)
    groups = {g.index: g.name for g in body.vertex_groups}
    for vert in mesh.verts:
        if vert.co.z < cut - 0.001:
            weights = body.data.vertices[vert.index].groups
            top = max(weights, key=lambda item: item.weight)
            assert groups[top.group].startswith(tripo_crawler.ARMS), "only hands may hang below the cut"
    assert not [e for e in mesh.edges if e.is_boundary and all(abs(v.co.z - cut) < 0.05 for v in e.verts)]
    caps = [f for f in mesh.faces if len(f.verts) > 3]
    assert len(caps) == 2, "one cap per thigh (Tripo bodies are all triangles, caps are n-gons)"
    assert all(f.normal.z < -0.5 for f in caps), "caps face down, out of the stump"
    mesh.free()
    assert not any(name.startswith(tripo_crawler.LEGS) for name in groups.values())


def test_shambler_reach_shape_opens_only_the_striking_hand():
    scene = check_models.load_glb(_model(next(row for row in ROWS if row["name"] == "shambler")))
    body = next(obj for obj in scene if obj.name == "Body")
    keys = body.data.shape_keys.key_blocks
    reach = keys["ReachFingers"]
    assert reach.relative_key == keys["Basis"] and reach.value == 0.0
    hand = body.vertex_groups["hand_R"].index
    travel = []
    for vertex in body.data.vertices:
        delta = reach.data[vertex.index].co - keys["Basis"].data[vertex.index].co
        if delta.length > 0.0001:
            assert any(group.group == hand and group.weight > 0 for group in vertex.groups)
            travel.append(delta.length)
    assert 0.03 < max(travel) < 0.09, "curled fingers release by a few centimetres"
