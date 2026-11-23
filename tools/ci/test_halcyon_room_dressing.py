"""Check that the room fixture placements regenerate the committed Godot scene."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "levels"))

import halcyon_room_dressing


class HalcyonRoomDressingTest(unittest.TestCase):
    def test_room_placements_reproduce_the_scene(self):
        scene = Path(__file__).resolve().parents[2] / "levels/halcyon_labs/room_dressing.tscn"
        self.assertEqual(halcyon_room_dressing.build(), scene.read_text(encoding="utf-8"))
