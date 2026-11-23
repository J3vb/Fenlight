"""Lantern Post Deploy gate (plan F-74 step 4, asset list G1-G5): concrete wall, DEPLOY tunnel, banner,
floodlight and radio mast.

Same rules as town_buildings.py: one merged mesh per model, origin at its bottom centre, front facing
Blender -Y (Godot +Z), shared town material slots only. The DEPLOY letters are a Label3D placed by
tools/levels/lantern_post_scene.py; the banner emblem is drawn by the Banner material (town_surface pattern 8).
"""

import math

import bpy
import prop_models as p
import town_buildings as tb
from mathutils import Vector
from town_buildings import _box

HAZARD_PANEL = (1.4, 3.4)  # width, height of the striped panel on each tunnel pillar
STRIPE = 0.26  # width of one hazard stripe; the gap between stripes is the same


def _mats() -> dict:
    from build_models import material, srgb

    return {
        "concrete": material("Concrete", srgb("#6E716E"), roughness=0.9),
        "iron": material("Iron", (0.012, 0.012, 0.014, 1.0), metallic=0.7, roughness=0.5),
        "snow": material("Snow", srgb("#D6DEE8"), roughness=0.8),
        "hazard": material("TownHazard", srgb("#D9A21E"), roughness=0.7),
        "fluid": material("Fluid", srgb("#8DFF3A"), roughness=0.2, glow=2.0),
        "banner": material("Banner", srgb("#5A1A1E"), roughness=0.9),
        "lamp": material("Bulb", srgb("#FFD9A0"), roughness=0.3, glow=3.0),
        "beacon": material("Beacon", srgb("#C3201B"), roughness=0.3, glow=4.0),
    }


def _beam(name: str, a: tuple, b: tuple, radius: float, mat, verts: int = 4) -> None:
    """A thin straight member from point `a` to point `b` (lattice legs and braces)."""
    va, vb = Vector(a), Vector(b)
    d = vb - va
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=d.length, location=(va + vb) / 2)
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = d.to_track_quat("Z", "Y")
    obj.data.materials.append(mat)


def _clip(poly: list, lo: tuple, hi: tuple) -> list:
    """Clips a convex polygon [(x, z), ...] to the rectangle lo..hi (Sutherland-Hodgman)."""
    for axis, limit, keep_above in ((0, lo[0], True), (0, hi[0], False), (1, lo[1], True), (1, hi[1], False)):
        out = []
        for i, cur in enumerate(poly):
            prev = poly[i - 1]
            cur_in = (cur[axis] >= limit) == keep_above
            prev_in = (prev[axis] >= limit) == keep_above
            if cur_in != prev_in:
                t = (limit - prev[axis]) / (cur[axis] - prev[axis])
                out.append(tuple(prev[k] + (cur[k] - prev[k]) * t for k in range(2)))
            if cur_in:
                out.append(cur)
        poly = out
        if not poly:
            break
    return poly


def hazard_stripes(name: str, centre: tuple, size: tuple, y: float, m: dict, flip: bool = False) -> None:
    """Dark plate with diagonal Hazard stripes on a front face at `y`, centred on `centre` (x, z)."""
    w, h = size
    cx, cz = centre
    _box(f"{name}Plate", (w, 0.06, h), (cx, y + 0.03, cz), m["iron"])
    lo, hi = (cx - w / 2, cz - h / 2), (cx + w / 2, cz + h / 2)
    lean = -1 if flip else 1
    k = 0
    start = -h - w
    while start < w + h:
        x0 = lo[0] + start
        band = [(x0, lo[1]), (x0 + STRIPE, lo[1]), (x0 + STRIPE + lean * h, hi[1]), (x0 + lean * h, hi[1])]
        clipped = _clip(band, lo, hi)
        if len(clipped) >= 3:
            tb._prism_y(f"{name}Stripe{k}", clipped, y - 0.03, 0.04, m["hazard"])
            k += 1
        start += 2 * STRIPE


def build_gate_wall() -> None:
    """G1: one 8 m concrete wall section with pilasters at its ends, walkway, front rail and back parapet. 8x3x8.

    Sections stand side by side, so the end pilasters pair up into the joints of the concept wall.
    """
    m = _mats()
    front = -1.2
    _box("Plinth", (8.0, 2.8, 0.5), (0, 0, 0.25), m["concrete"], 0.03)
    _box("Body", (8.0, 2.4, 7.0), (0, 0, 3.5), m["concrete"])
    for k, x in enumerate((-3.7, 3.7)):
        _box(f"Pilaster{k}", (0.6, 0.3, 6.6), (x, front - 0.15, 3.6), m["concrete"], 0.03)
    _box("Ledge", (8.0, 0.24, 0.25), (0, front - 0.12, 2.4), m["concrete"], 0.02)
    _box("LedgeSnow", (7.9, 0.28, 0.06), (0, front - 0.14, 2.55), m["snow"], 0.02)
    _box("Coping", (8.0, 0.36, 0.3), (0, front - 0.18, 6.85), m["concrete"], 0.02)
    for k, x in enumerate((-2.0, 0.0, 2.0)):
        _box(f"Seam{k}", (0.05, 0.04, 4.0), (x, front - 0.02, 4.6), m["iron"])
    _box("Deck", (8.0, 3.0, 0.25), (0, -0.1, 7.12), m["concrete"], 0.02)
    _box("DeckSnow", (7.9, 2.9, 0.12), (0, -0.1, 7.3), m["snow"], 0.04)
    for k, x in enumerate((-3.0, -1.0, 1.0, 3.0)):
        _box(f"Corbel{k}", (0.22, 0.4, 0.3), (x, front - 0.2, 6.85), m["iron"])
    rail_y = -1.5
    for k, x in enumerate((-3.75, -1.25, 1.25, 3.75)):
        _box(f"RailPost{k}", (0.08, 0.08, 1.05), (x, rail_y, 7.77), m["iron"])
    for k, z in enumerate((7.8, 8.25)):
        _box(f"Rail{k}", (8.0, 0.07, 0.07), (0, rail_y, z), m["iron"])
    _box("RailSnow", (7.9, 0.1, 0.04), (0, rail_y, 8.31), m["snow"], 0.015)
    _box("Parapet", (8.0, 0.25, 0.9), (0, 1.25, 7.7), m["concrete"], 0.02)
    _box("ParapetSnow", (7.9, 0.3, 0.08), (0, 1.25, 8.17), m["snow"], 0.03)
    _box("Drift", (8.0, 0.6, 0.35), (0, front - 0.45, 0.17), m["snow"], 0.15)


def build_gate_tunnel() -> None:
    """G2: tunnel mouth with DEPLOY sign panel and green chevrons, hazard pillars and bollards, a 12 m tunnel
    with ribs and green strip lights, and a closed blast door at the far end. 10x14x9.
    """
    m = _mats()
    face = -7.0
    for k, s in enumerate((-1, 1)):
        _box(f"Pillar{k}", (1.8, 2.0, 5.4), (s * 4.1, face + 1.0, 2.7), m["concrete"], 0.04)
        _box(f"Plinth{k}", (2.0, 2.2, 0.45), (s * 4.1, face + 1.0, 0.22), m["concrete"], 0.03)
        _box(f"PlinthSnow{k}", (1.9, 0.5, 0.08), (s * 4.1, face - 0.02, 0.48), m["snow"], 0.03)
        hazard_stripes(f"Hazard{k}", (s * 4.1, 0.55 + HAZARD_PANEL[1] / 2), HAZARD_PANEL, face, m, flip=s > 0)
        _box(f"EdgeGlow{k}", (0.08, 0.08, 5.2), (s * 3.26, face + 0.1, 2.7), m["fluid"])
        _bollard(f"Bollard{k}", (s * 3.65, face - 0.6), m)
        corner = [(s * 3.2, 5.45), (s * 3.2, 4.45), (s * 2.2, 5.45)]
        tb._prism_y(f"MouthCorner{k}", corner if s > 0 else corner[::-1], face, 2.0, m["concrete"])
    # Inset the header between three bevelled precast sections and a cast sill.
    for k, x in enumerate((-4.12, 0, 4.12)):
        width = 1.73 if k != 1 else 6.46
        _box(f"Lintel{k}", (width, 2.0, 3.6), (x, face + 1.0, 7.2), m["concrete"], 0.045)
    for x in (-3.78, 2.98):
        _box(f"SignReveal{x}", (0.15, 0.29, 1.93), (x, face - 0.07, 7.3), m["concrete"], 0.025)
    _box("SignHood", (6.92, 0.42, 0.13), (-0.4, face - 0.11, 8.23), m["concrete"], 0.025)
    _box("LintelSnow", (10.1, 2.1, 0.16), (0, face + 1.0, 9.06), m["snow"], 0.06)
    drift = [
        (-4.85, 8.99),
        (-3.9, 8.91),
        (-2.8, 8.96),
        (-1.9, 8.90),
        (-1.25, 9.02),
        (0.8, 9.01),
        (1.55, 8.94),
        (2.8, 8.97),
        (3.65, 8.89),
        (4.9, 9.02),
        (4.9, 9.10),
        (-4.85, 9.10),
    ]
    tb._prism_y("WindLip", drift, face - 0.064, 0.18, m["snow"])
    _box("SignPanel", (6.6, 0.1, 1.7), (-0.4, face - 0.05, 7.3), m["iron"], 0.02)
    _box("SignLedge", (7.0, 0.3, 0.12), (-0.4, face - 0.12, 6.4), m["concrete"])
    _box("SignLedgeSnow", (6.9, 0.3, 0.05), (-0.4, face - 0.12, 6.48), m["snow"])
    for k, x in enumerate((2.0, 2.65)):
        chevron = [(x, 6.85), (x + 0.22, 6.85), (x + 0.62, 7.3), (x + 0.22, 7.75), (x, 7.75), (x + 0.4, 7.3)]
        tb._prism_y(f"Chevron{k}", chevron, face - 0.14, 0.05, m["fluid"])
    _tunnel(m, face)
    _blast_door(m, 6.0)


def _bollard(name: str, at: tuple, m: dict) -> None:
    """Short post striped in Hazard and Iron bands in front of a pillar."""
    for band in range(6):
        mat = m["hazard"] if band % 2 == 0 else m["iron"]
        p._cyl(f"{name}Band{band}", 0.16, 0.2, (at[0], at[1], band * 0.2), mat, verts=12)
    p._cyl(f"{name}Cap", 0.17, 0.06, (at[0], at[1], 1.2), m["snow"], verts=12)


def _tunnel(m: dict, face: float) -> None:
    """Inner walls, chamfered ceiling, ribs every 2.2 m, green strip lights and a concrete floor."""
    start, end = face + 2.0, 6.0
    length, mid = end - start, (start + end) / 2
    for k, s in enumerate((-1, 1)):
        _box(f"Wall{k}", (0.6, length, 5.0), (s * 3.3, mid, 2.5), m["concrete"])
        _box(f"Chamfer{k}", (0.3, length, 1.2), (s * 2.65, mid, 4.65), m["concrete"], turn=(0, s * math.pi / 4, 0))
        _box(f"WallStrip{k}", (0.05, length, 0.1), (s * 2.98, mid, 3.9), m["fluid"])
        _box(f"FloorStrip{k}", (0.05, length, 0.06), (s * 2.98, mid, 0.35), m["fluid"])
        _box(f"Kerb{k}", (0.3, length + 2.0, 0.15), (s * 2.85, mid - 1.0, 0.075), m["concrete"])
    _box("Ceiling", (6.6, length, 0.6), (0, mid, 5.3), m["concrete"])
    for k, x in enumerate((-1.2, 1.2)):
        _box(f"CeilingStrip{k}", (0.14, length, 0.05), (x, mid, 4.98), m["fluid"])
    for k in range(5):
        y = start + 0.5 + k * 2.2
        for j, s in enumerate((-1, 1)):
            _box(f"Rib{k}_{j}", (0.25, 0.4, 4.4), (s * 2.88, y, 2.2), m["concrete"])
        _box(f"RibTop{k}", (4.6, 0.4, 0.25), (0, y, 4.88), m["concrete"])
    _box("Floor", (6.0, end - face, 0.06), (0, (face + end) / 2, 0.03), m["concrete"])


def _blast_door(m: dict, y: float) -> None:
    """Two closed iron door leaves with a seam, hazard band, green status light, and the back wall."""
    for k, s in enumerate((-1, 1)):
        _box(f"Leaf{k}", (2.95, 0.4, 5.0), (s * 1.5, y + 0.2, 2.5), m["iron"], 0.03)
        for j, z in enumerate((1.6, 3.2)):
            _box(f"LeafRib{k}_{j}", (2.6, 0.08, 0.18), (s * 1.5, y - 0.02, z), m["iron"])
    hazard_stripes("DoorHazard", (0, 0.55), (5.9, 0.7), y - 0.02, m)
    _box("DoorLight", (0.5, 0.1, 0.18), (0, y - 0.04, 4.6), m["fluid"])
    _box("BackWall", (6.6, 0.5, 5.6), (0, y + 0.75, 2.8), m["concrete"])


def build_banner() -> None:
    """G3: maroon banner hung from an iron rod on a wall bracket, pointed foot. 1.4x0.2x4.5.

    The emblem is drawn by the Banner material from the model's own position, so the cloth stays plain here.
    """
    m = _mats()
    top = 4.3
    cloth = [(-0.6, 0.55), (0, 0.0), (0.6, 0.55), (0.6, top), (-0.6, top)]
    tb._prism_y("Cloth", cloth, -0.06, 0.03, m["banner"])
    _box("Sleeve", (1.24, 0.08, 0.14), (0, -0.045, top + 0.02), m["banner"], 0.02)
    p._cyl("Rod", 0.035, 1.5, (0, 0, 0), m["iron"], verts=8)
    rod = bpy.context.active_object
    rod.rotation_euler = (0, math.pi / 2, 0)
    rod.location = (0, -0.045, top + 0.06)
    for k, x in enumerate((-0.77, 0.77)):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=5, radius=0.05, location=(x, -0.045, top + 0.06))
        bpy.context.active_object.name = f"Finial{k}"
        bpy.context.active_object.data.materials.append(m["iron"])
    _box("Bracket", (0.05, 0.16, 0.05), (0, 0.04, top + 0.06), m["iron"])
    _beam("Strut", (0, 0.1, top - 0.35), (0, -0.03, top + 0.04), 0.02, m["iron"])
    _box("WallPlate", (0.14, 0.02, 0.5), (0, 0.11, top - 0.1), m["iron"])
    _box("RodSnow", (1.3, 0.07, 0.035), (0, -0.045, top + 0.11), m["snow"], 0.012)


def _turned(point: tuple, pivot: tuple, tilt: float) -> tuple:
    """`point` turned by `tilt` radians around the X axis through `pivot`."""
    y, z = point[1] - pivot[1], point[2] - pivot[2]
    c, s = math.cos(tilt), math.sin(tilt)
    return (point[0], pivot[1] + y * c - z * s, pivot[2] + y * s + z * c)


def build_floodlight() -> None:
    """G4: box floodlight with four lamps on a yoke and a short pole, aimed a little down. 0.8x0.5x2."""
    m = _mats()
    _box("BasePlate", (0.5, 0.5, 0.05), (0, 0, 0.025), m["iron"])
    p._cyl("Pole", 0.05, 1.55, (0, 0, 0.05), m["iron"], verts=10)
    _box("Yoke", (0.78, 0.06, 0.06), (0, 0, 1.6), m["iron"])
    for k, s in enumerate((-1, 1)):
        _box(f"YokeArm{k}", (0.04, 0.06, 0.3), (s * 0.37, 0, 1.75), m["iron"])
    pivot, tilt = (0, 0, 1.82), math.radians(-18)
    turn = (tilt, 0, 0)
    _box("Head", (0.68, 0.3, 0.44), _turned((0, 0, 1.82), pivot, tilt), m["iron"], 0.02, turn)
    _box("Hood", (0.72, 0.18, 0.04), _turned((0, -0.2, 2.05), pivot, tilt), m["iron"], turn=turn)
    _box("HeadSnow", (0.64, 0.26, 0.04), _turned((0, 0.02, 2.06), pivot, tilt), m["snow"], 0.012, turn)
    for k in range(4):
        x, z = (k % 2 - 0.5) * 0.32, 1.82 + (k // 2 - 0.5) * 0.2
        _box(f"Lamp{k}", (0.28, 0.03, 0.17), _turned((x, -0.155, z), pivot, tilt), m["lamp"], turn=turn)
    for k in range(3):
        _box(f"Fin{k}", (0.6, 0.12, 0.02), _turned((0, 0.2, 1.68 + k * 0.14), pivot, tilt), m["iron"], turn=turn)


def build_radio_mast() -> None:
    """G5: four-leg lattice mast tapering to a pole with red beacons and a dish, on a concrete pad. 3x3x30."""
    m = _mats()
    _box("Pad", (3.2, 3.2, 0.4), (0, 0, 0.2), m["concrete"], 0.04)
    _box("PadSnow", (3.0, 3.0, 0.08), (0, 0, 0.42), m["snow"], 0.03)
    top, levels = 26.0, 9

    def half(z: float) -> float:
        return 1.35 - (1.35 - 0.3) * z / top

    corners = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    for k, (sx, sy) in enumerate(corners):
        _beam(f"Leg{k}", (sx * 1.35, sy * 1.35, 0.4), (sx * 0.3, sy * 0.3, top), 0.05, m["iron"], 6)
    for lv in range(levels + 1):
        z = 0.4 + lv * (top - 0.4) / levels
        h = half(z)
        for k in range(4):
            a, b = corners[k], corners[(k + 1) % 4]
            _beam(f"Ring{lv}_{k}", (a[0] * h, a[1] * h, z), (b[0] * h, b[1] * h, z), 0.025, m["iron"])
            if lv == levels:
                continue
            z2 = 0.4 + (lv + 1) * (top - 0.4) / levels
            h2 = half(z2)
            lo, hi = (a, b) if lv % 2 == 0 else (b, a)
            _beam(f"Brace{lv}_{k}", (lo[0] * h, lo[1] * h, z), (hi[0] * h2, hi[1] * h2, z2), 0.02, m["iron"])
    p._cyl("TopPole", 0.08, 3.6, (0, 0, top), m["iron"], verts=8)
    for k, z in enumerate((9.5, 19.0)):
        p._cyl(f"Beacon{k}", 0.16, 0.3, (half(z) + 0.1, 0, z), m["beacon"], verts=10)
    p._cyl("BeaconTop", 0.18, 0.34, (0, 0, top + 3.6), m["beacon"], verts=10)
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.95, radius2=0.12, depth=0.45, location=(0, 0, 0))
    dish = bpy.context.active_object
    dish.name = "Dish"
    dish.rotation_euler = (math.radians(80), 0, math.radians(35))
    dish.location = (-0.75, -0.9, 18.0)
    dish.data.materials.append(m["iron"])
    for k, x in enumerate((-0.25, 0.25)):
        p._cyl(f"Whip{k}", 0.02, 2.4, (x, 0.2, top + 0.5), m["iron"], verts=6)


MODELS = {
    "gate_wall": ("town_large/gate_wall.glb", tb._merged(build_gate_wall, "GateWall")),
    "gate_tunnel": ("town_large/gate_tunnel.glb", tb._merged(build_gate_tunnel, "GateTunnel")),
    "radio_mast": ("town_large/radio_mast.glb", tb._merged(build_radio_mast, "RadioMast")),
    "banner": ("town/banner.glb", tb._merged(build_banner, "Banner")),
    "floodlight": ("town/floodlight.glb", tb._merged(build_floodlight, "Floodlight")),
}
