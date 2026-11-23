"""Check that the room fixture placements regenerate the committed Godot scene."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "levels"))

import halcyon_room_dressing


class HalcyonRoomDressingTest(unittest.TestCase):
    def test_room_placements_reproduce_the_scene(self):
        directory = Path(__file__).resolve().parents[2] / "levels/halcyon_labs"
        generated = halcyon_room_dressing.build()
        self.assertEqual(set(generated), {"room_dressing.tscn", "room_fixture_collision.tscn"})
        for name, contents in generated.items():
            with self.subTest(name=name):
                self.assertEqual(contents, (directory / name).read_text(encoding="utf-8"))
