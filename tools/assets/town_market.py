"""Lantern Post market row (plan F-74 step 3, asset list S1-S7): stall frame, sign board and stall dressing.

Same rules as town_buildings.py: one merged mesh per model, origin at its bottom centre, front facing
Blender -Y (Godot +Z), shared town slots only (docs/design/lantern-post-assets.md), at most 4 per model
(the `town` budget). Sign text is a Label3D the scene generator puts on `stall_sign`, so one model serves
all four stalls.
"""

import math

import bpy
import mission_print
import prop_models as p
import town_buildings as tb
from town_buildings import _box

STALL_W, STALL_D = 4.0, 3.0
POST_X, POST_Y = 1.85, 1.3
COUNTER_Y = -1.0  # centre of the counter; its front face is POST_Y from the middle, flush with the posts


def _mats() -> dict:
    from build_models import material, srgb

    return {
        "planks": material("Planks", srgb("#5A4434"), roughness=0.85),
        "dark": material("DarkWood", srgb("#2A1E16"), roughness=0.8),
        "canvas": material("Canvas", srgb("#3B3D33"), roughness=0.9),
        "snow": material("Snow", srgb("#D6DEE8"), roughness=0.8),
        "sign": material("SignPaint", srgb("#1E1C1A"), roughness=0.7),
        "iron": material("Iron", (0.012, 0.012, 0.014, 1.0), metallic=0.7, roughness=0.5),
        "bulb": material("Bulb", srgb("#FF9A3C"), roughness=0.3, glow=4.0),
        "paper": material("Paper", srgb("#D8D2C0"), roughness=0.9),
        "olive": material("Olive", srgb("#4A4F33"), roughness=0.7),
        "screen": material("Screen", srgb("#4FD6C8"), roughness=0.2, glow=2.0),
    }


def _cyl(name: str, radius: float, height: float, bottom: tuple, mat, verts: int = 8) -> None:
    p._cyl(name, radius, height, bottom, mat, verts=verts)


def build_stall_frame() -> None:
    """S1: four timber posts, plank counter and back wall, sloped canvas awning with snow, hanging lamp."""
    m = _mats()
    front_h, back_h = 2.55, 3.05
    for k, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        h = front_h if sy < 0 else back_h
        _box(f"Post{k}", (0.16, 0.16, h), (sx * POST_X, sy * POST_Y, h / 2), m["planks"], 0.02)
    _box("Counter", (3.54, 0.6, 0.95), (0, COUNTER_Y, 0.475), m["planks"], 0.02)
    _box("CounterTop", (3.8, 0.75, 0.08), (0, COUNTER_Y - 0.05, 0.99), m["planks"], 0.02)
    _box("BackWall", (3.54, 0.08, 2.4), (0, POST_Y, 1.3), m["planks"])
    _box("Shelf", (3.4, 0.35, 0.05), (0, POST_Y - 0.2, 1.55), m["planks"])
    run = math.hypot(2 * POST_Y + 0.7, back_h - front_h)
    tilt = math.atan2(back_h - front_h, 2 * POST_Y + 0.7)
    mid_z = (front_h + back_h) / 2 + 0.06
    _box("Awning", (STALL_W + 0.2, run, 0.05), (0, 0, mid_z), m["canvas"], turn=(tilt, 0, 0))
    _box("AwningSnow", (STALL_W, run - 0.25, 0.1), (0, 0.05, mid_z + 0.08), m["snow"], 0.04, turn=(tilt, 0, 0))
    edge_y = -(POST_Y + 0.35)
    _box("Valance", (STALL_W + 0.2, 0.04, 0.32), (0, edge_y, front_h - 0.25), m["canvas"])
    for k, x in enumerate((-1.2, 0.0, 1.2)):
        _box(f"ValanceDip{k}", (0.9, 0.04, 0.12), (x, edge_y, front_h - 0.46), m["canvas"])
    for k, sx in enumerate((-1, 1)):
        _box(f"Beam{k}", (0.12, 2 * POST_Y + 0.2, 0.14), (sx * POST_X, 0, mid_z - 0.12), m["planks"], turn=(tilt, 0, 0))
    _box("LampCord", (0.02, 0.02, 0.45), (0, -0.3, mid_z - 0.35), m["planks"])
    bpy.ops.mesh.primitive_cone_add(
        vertices=10, radius1=0.24, radius2=0.06, depth=0.18, location=(0, -0.3, mid_z - 0.62)
    )
    shade = bpy.context.active_object
    shade.name = "LampShade"
    shade.data.materials.append(m["planks"])
    _box("LampBulb", (0.12, 0.12, 0.1), (0, -0.3, mid_z - 0.74), m["bulb"])
    _box("CounterSnow", (1.2, 0.4, 0.05), (1.1, COUNTER_Y - 0.1, 1.05), m["snow"], 0.02)


def build_stall_sign() -> None:
    """S2: long painted board in a dark timber frame with a snow cap and two iron hooks. 3.6 x 0.1 x 0.8."""
    m = _mats()
    _box("Board", (3.5, 0.06, 0.7), (0, 0, 0.4), m["sign"])
    for k, (size, at) in enumerate(
        (
            ((3.6, 0.1, 0.06), (0, 0, 0.03)),
            ((3.6, 0.1, 0.06), (0, 0, 0.77)),
            ((0.06, 0.1, 0.8), (-1.77, 0, 0.4)),
            ((0.06, 0.1, 0.8), (1.77, 0, 0.4)),
        )
    ):
        _box(f"Frame{k}", size, at, m["dark"])
    _box("Snow", (3.5, 0.14, 0.05), (0, 0, 0.82), m["snow"], 0.02)
    for k, x in enumerate((-1.4, 1.4)):
        _box(f"Hook{k}", (0.04, 0.04, 0.12), (x, 0.03, 0.9), m["iron"])


def build_missions_board() -> None:
    """S3: big notice board on two legs, a map and pinned notes, roof cap with snow, a small lamp. 3 x 0.4 x 2.6."""
    m = _mats()
    for k, x in enumerate((-1.4, 1.4)):
        _box(f"Leg{k}", (0.14, 0.14, 2.4), (x, 0.05, 1.2), m["dark"])
    _box("Board", (2.9, 0.08, 1.7), (0, 0.05, 1.45), m["dark"], 0.01)
    ink = mission_print.printed_material()
    papers = [
        ("Map", -0.52, 1.60, 1.52, 1.12, -0.025, mission_print.CHART),
        ("ReportA", 0.60, 1.74, 0.42, 0.58, -0.07, mission_print.REPORT),
        ("ReportB", 1.13, 1.23, 0.39, 0.51, 0.08, mission_print.REPORT),
        ("PhotoA", -0.84, 0.85, 0.43, 0.33, 0.09, mission_print.PHOTOS[0]),
        ("PhotoB", -0.20, 0.87, 0.44, 0.34, -0.08, mission_print.PHOTOS[1]),
        ("PhotoC", 1.12, 1.92, 0.42, 0.32, 0.06, mission_print.PHOTOS[2]),
    ]
    for name, x, z, w, h, tilt, region in papers:
        size = (w, 0.015, h)
        paper = _box(name, size, (x, -0.015, z), ink, turn=(0, tilt, 0))
        mission_print.sheet(paper, size, region)
        for side in (-1, 1) if name == "Map" else (0,):
            px = x + side * (w / 2 - 0.04) + math.sin(tilt) * h * 0.42
            p._blob(f"{name}Pin{side}", 0.020, (px, -0.031, z + h * 0.42), m["dark"], squash=(1, 0.6, 1))
    _box("Cap", (3.2, 0.42, 0.08), (0, 0.0, 2.38), m["dark"], 0.01, turn=(math.radians(-8), 0, 0))
    _box("CapSnow", (3.05, 0.36, 0.08), (0, 0.0, 2.45), m["snow"], 0.03, turn=(math.radians(-8), 0, 0))
    _box("LampArm", (0.04, 0.3, 0.04), (0, -0.12, 2.28), m["dark"])
    _box("LampBulb", (0.14, 0.1, 0.1), (0, -0.28, 2.22), m["bulb"])
    p._merge("MissionsBoard")
    bpy.context.active_object.data.uv_layers[0].name = "PrintLayout"


def build_trader_goods() -> None:
    """S4: counter dressing: two crates, olive ammo tins, a hanging scale and a cash box. 2 x 0.8 x 0.6."""
    m = _mats()
    _box("CrateA", (0.55, 0.5, 0.42), (-0.7, 0.05, 0.21), m["planks"], 0.02)
    _box("CrateB", (0.4, 0.4, 0.3), (-0.72, 0.05, 0.57), m["planks"], 0.02)
    for k, (x, z) in enumerate(((-0.15, 0.0), (0.2, 0.0), (0.02, 0.22))):
        _box(f"Tin{k}", (0.32, 0.22, 0.2), (x, 0.15, z + 0.1), m["olive"], 0.015)
        _box(f"TinHandle{k}", (0.12, 0.03, 0.03), (x, 0.15, z + 0.215), m["iron"])
    _box("ScalePlate", (0.4, 0.3, 0.02), (0.65, -0.1, 0.12), m["iron"])
    _cyl("ScaleStem", 0.025, 0.35, (0.65, -0.1, 0.0), m["iron"])
    _cyl("ScaleDial", 0.1, 0.05, (0.65, -0.1, 0.33), m["iron"], verts=12)
    _box("CashBox", (0.3, 0.22, 0.14), (0.25, -0.22, 0.07), m["iron"], 0.01)
    for k, x in enumerate((-0.7, -0.15, 0.2)):
        _box(f"Tag{k}", (0.1, 0.01, 0.06), (x, -0.22 + (0.02 if k else -0.05), 0.12), m["paper"])


def build_gun_wall() -> None:
    """S5: pegboard in a timber frame with three rifle silhouettes and hand tools hung on it. 3 x 0.2 x 2."""
    m = _mats()
    _box("Pegboard", (2.9, 0.05, 1.5), (0, 0.05, 1.2), m["planks"])
    for k, (size, at) in enumerate(
        (
            ((3.0, 0.12, 0.08), (0, 0.06, 1.97)),
            ((3.0, 0.12, 0.08), (0, 0.06, 0.43)),
            ((0.1, 0.12, 2.0), (-1.45, 0.06, 1.0)),
            ((0.1, 0.12, 2.0), (1.45, 0.06, 1.0)),
        )
    ):
        _box(f"Frame{k}", size, at, m["dark"])
    for k, z in enumerate((1.75, 1.42, 1.1)):
        _rifle(f"Rifle{k}", (-0.35 + k * 0.08, -0.03, z), m)
    for k, (x, z, h) in enumerate(((0.95, 1.6, 0.3), (1.15, 1.55, 0.4), (1.3, 1.62, 0.26), (1.0, 1.0, 0.34))):
        _box(f"Tool{k}", (0.04, 0.03, h), (x, -0.02, z), m["iron"])
        _box(f"ToolHead{k}", (0.1, 0.035, 0.05), (x, -0.02, z + h / 2), m["iron"])
    for k in range(6):
        _box(f"Peg{k}", (0.025, 0.08, 0.025), (-0.9 + k * 0.4, -0.03, 1.85 - (k % 2) * 0.75), m["iron"])


def _rifle(name: str, at: tuple, m: dict) -> None:
    """Flat rifle silhouette lying left to right: wooden stock and grip, iron receiver, barrel and magazine."""
    x, y, z = at
    _box(f"{name}Stock", (0.45, 0.04, 0.12), (x - 0.62, y, z - 0.02), m["dark"])
    _box(f"{name}Body", (0.5, 0.05, 0.1), (x - 0.15, y, z), m["iron"])
    _box(f"{name}Barrel", (0.65, 0.03, 0.03), (x + 0.42, y, z + 0.02), m["iron"])
    _box(f"{name}Mag", (0.07, 0.04, 0.16), (x - 0.05, y, z - 0.12), m["iron"], turn=(0, 0.2, 0))
    _box(f"{name}Grip", (0.06, 0.04, 0.12), (x - 0.3, y, z - 0.1), m["dark"], turn=(0, -0.3, 0))


def build_workbench() -> None:
    """S6: heavy plank bench with a shelf, a vice, tools and a small lamp on an iron arm. 2 x 0.8 x 1."""
    m = _mats()
    _box("Top", (2.0, 0.8, 0.1), (0, 0, 0.85), m["planks"], 0.02)
    for k, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        _box(f"Leg{k}", (0.1, 0.1, 0.8), (sx * 0.9, sy * 0.33, 0.4), m["dark"])
    _box("Shelf", (1.85, 0.65, 0.05), (0, 0, 0.25), m["planks"])
    _box("ViceBody", (0.2, 0.25, 0.16), (-0.7, -0.3, 0.98), m["iron"], 0.01)
    _box("ViceJaw", (0.22, 0.05, 0.1), (-0.7, -0.45, 1.0), m["iron"])
    _box("ViceScrew", (0.03, 0.25, 0.03), (-0.7, -0.6, 0.98), m["iron"])
    for k, (x, y, w) in enumerate(((0.1, -0.1, 0.35), (0.35, 0.1, 0.25), (-0.25, 0.15, 0.3))):
        _box(f"Tool{k}", (w, 0.04, 0.03), (x, y, 0.915), m["iron"], turn=(0, 0, k * 0.5))
    _box("LampPost", (0.04, 0.04, 0.3), (0.85, 0.3, 1.05), m["iron"])
    _box("LampArm", (0.3, 0.04, 0.04), (0.72, 0.3, 1.2), m["iron"])
    _box("LampBulb", (0.1, 0.1, 0.07), (0.6, 0.3, 1.15), m["bulb"])


def build_tech_desk() -> None:
    """S7: desk with two glowing monitors, a radio set with dials and loose cables. 2 x 0.8 x 1.4."""
    m = _mats()
    _box("Top", (2.0, 0.8, 0.06), (0, 0, 0.77), m["planks"], 0.01)
    for k, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        _box(f"Leg{k}", (0.07, 0.07, 0.74), (sx * 0.93, sy * 0.35, 0.37), m["dark"])
    for k, x in enumerate((-0.55, 0.15)):
        _box(f"Monitor{k}", (0.55, 0.3, 0.45), (x, 0.12, 1.12), m["iron"], 0.02)
        _box(f"Screen{k}", (0.46, 0.02, 0.36), (x, -0.04, 1.13), m["screen"])
        _box(f"Stand{k}", (0.08, 0.08, 0.12), (x, 0.15, 0.86), m["iron"])
    _box("Radio", (0.5, 0.35, 0.3), (0.72, 0.1, 0.95), m["iron"], 0.02)
    for k in range(3):
        _cyl(f"Dial{k}", 0.035, 0.04, (0.58 + k * 0.13, -0.08, 0.9), m["dark"])
    _box("Antenna", (0.02, 0.02, 0.4), (0.9, 0.2, 1.3), m["iron"])
    _box("Handset", (0.08, 0.2, 0.06), (0.45, -0.25, 0.83), m["dark"])
    for k, (x, length) in enumerate(((-0.2, 0.7), (0.4, 0.6))):
        _box(f"Cable{k}", (0.025, length, 0.025), (x, 0.1, 0.5), m["dark"], turn=(0.9, 0, 0))


MODELS = {
    "stall_frame": ("town/stall_frame.glb", tb._merged(build_stall_frame, "StallFrame")),
    "stall_sign": ("town/stall_sign.glb", tb._merged(build_stall_sign, "StallSign")),
    "missions_board": ("town/missions_board.glb", build_missions_board),
    "trader_goods": ("town/trader_goods.glb", tb._merged(build_trader_goods, "TraderGoods")),
    "gun_wall": ("town/gun_wall.glb", tb._merged(build_gun_wall, "GunWall")),
    "workbench": ("town/workbench.glb", tb._merged(build_workbench, "Workbench")),
    "tech_desk": ("town/tech_desk.glb", tb._merged(build_tech_desk, "TechDesk")),
}
