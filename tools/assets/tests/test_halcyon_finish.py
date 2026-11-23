"""Repeated keyboard meshes receive the same printed key faces before joining."""

import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build_models
import halcyon_finish
from halcyon_atlas import GRID, SLOTS


def test_guard_desk_keyboards_both_use_the_keyboard_tile():
    build_models.reset_scene()
    dark = build_models.material("Dark", (0.1, 0.1, 0.1, 1.0))
    keyboards = [build_models.box("Keyboard", (0.44, 0.15, 0.022), (x, 0.0, 0.0), dark) for x in (-0.55, 0.25)]
    assert halcyon_finish.apply("GuardDesk", keyboards)
    for keyboard in keyboards:
        mesh = keyboard.data
        top = max(mesh.polygons, key=lambda polygon: polygon.normal.z)
        uv = mesh.uv_layers.active.data[top.loop_start].uv
        assert int((1.0 - uv.y) * GRID) * GRID + int(uv.x * GRID) == SLOTS["keyboard"]
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
