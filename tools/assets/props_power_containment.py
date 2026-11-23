"""Generator Hall, Containment Wing and Main Corridor props (plan F-15 step 3): diesel generator,
holding cell with a bent door, wall pipe runs and hazard signs. Same rules as prop_models.py.
"""

import math

import prop_models as p


def _extra():
    from build_models import material, srgb

    return {
        "olive": material("Olive", srgb("#4A5446"), roughness=0.7),
        "alarm": material("Alarm", srgb("#C3201B"), roughness=0.6),
    }


def build_generator() -> None:
    """Skid-mounted diesel generator: engine, radiator grille, exhaust, control box, fuel line. Box 4 x 2.4 x 2.5."""
    from build_models import box, cylinder

    m = {**p._mats(), **_extra()}
    box("Skid", (4.0, 2.4, 0.18), (0, 0, 0.09), m["dark"])
    box("Engine", (2.3, 1.5, 1.35), (-0.35, 0.1, 0.86), m["olive"], bevel=0.04)
    box("Head", (1.9, 1.1, 0.35), (-0.35, 0.1, 1.71), m["olive"], bevel=0.03)
    box("Radiator", (0.5, 1.9, 1.75), (-1.72, 0.0, 1.05), m["olive"], bevel=0.03)
    for i in range(9):
        box(f"Grille{i}", (0.02, 1.6, 0.06), (-1.98, 0.0, 0.42 + i * 0.16), m["dark"])
    box("AlternatorMount", (1.17, 1.05, 0.25), (1.29, 0.08, 0.29), m["dark"])
    cylinder("AlternatorBarrel", 0.55, 1.12, (1.31, 0.08, 0.87), m["steel"], axis="x")
    for i in range(3):
        cylinder(f"CoolingFin{i}", 0.60, 0.06, (0.87 + i * 0.36, 0.08, 0.87), m["steel"], axis="x")
    cylinder("EndBell", 0.38, 0.10, (1.89, 0.08, 0.87), m["dark"], axis="x")
    cylinder("ExhaustHeader", 0.105, 1.74, (-0.36, -0.74, 1.34), m["dark"], axis="x")
    for i in range(4):
        x = -1.02 + i * 0.44
        neck = box(f"ManifoldBranch{i}", (0.14, 0.30, 0.32), (x, -0.61, 1.49), m["dark"])
        neck.rotation_euler.x = -0.48
        box(f"ServiceCover{i}", (0.34, 0.034, 0.46), (x, -0.666, 0.80), m["olive"])
    box("ControlBox", (0.75, 0.32, 0.9), (1.35, -0.95, 1.05), m["olive"], bevel=0.02)
    box("ControlFace", (0.6, 0.02, 0.5), (1.35, -1.115, 1.2), m["dark"])
    for i in range(3):
        p._cyl(f"Gauge{i}", 0.05, 0.02, (1.15 + i * 0.2, -1.12, 1.33), m["steel"], verts=10).rotation_euler = (
            math.radians(90),
            0,
            0,
        )
    p._cyl("Exhaust", 0.11, 0.55, (0.3, 0.45, 1.85), m["dark"], verts=12)
    p._cyl("Silencer", 0.185, 0.31, (0.3, 0.45, 1.99), m["steel"], verts=12)
    p._cyl("ExhaustCap", 0.14, 0.05, (0.3, 0.45, 2.35), m["dark"], verts=12)
    cylinder("FuelLine", 0.03, 3.6, (0.0, 1.12, 0.32), m["steel"], axis="x")
    for i in range(4):
        box(f"Rocker{i}", (0.3, 0.6, 0.1), (-1.0 + i * 0.44, 0.1, 1.93), m["steel"])
    p._merge("Generator")


def build_holding_cell() -> None:
    """Barred holding cell with its door bent inward off one hinge. Box 2.5 x 3 x 2.5, door side faces +Z."""
    from build_models import box

    m = {**p._mats(), **_extra()}
    s = 1.25
    box("Floor", (2.5, 2.5, 0.06), (0, 0, 0.03), m["dark"])
    box("Roof", (2.5, 2.5, 0.08), (0, 0, 2.96), m["olive"])
    for x in (-s + 0.05, s - 0.05):
        for y in (-s + 0.05, s - 0.05):
            box(f"Corner{x}{y}", (0.1, 0.1, 2.9), (x, y, 1.48), m["olive"])
    for side, (axis, at) in enumerate((("x", s - 0.05), ("y", -s + 0.05), ("y", s - 0.05))):
        for i in range(9):
            t = -1.0 + i * 0.25
            pos = (t, at, 1.5) if axis == "x" else (at, t, 1.5)
            p._cyl(f"Bar{side}{i}", 0.018, 2.86, (pos[0], pos[1], 0.06), m["steel"], verts=6)
        rail = (2.4, 0.06, 0.06) if axis == "x" else (0.06, 2.4, 0.06)
        mid = (0, at, 1.0) if axis == "x" else (at, 0, 1.0)
        box(f"Rail{side}", rail, mid, m["olive"])
    front = -s + 0.05
    for i in range(4):
        t = -1.0 + i * 0.25
        p._cyl(f"FrontBar{i}", 0.018, 2.86, (t, front, 0.06), m["steel"], verts=6)
    box("FrontRail", (1.0, 0.06, 0.06), (-0.62, front, 1.0), m["olive"])
    box("DoorFrame", (0.08, 0.08, 2.9), (-0.1, front, 1.48), m["olive"])
    door = []
    for i in range(4):
        door.append(p._cyl(f"DoorBar{i}", 0.018, 2.2, (0.2 + i * 0.25, front, 0.3), m["steel"], verts=6))
    door.append(box("DoorTop", (0.95, 0.05, 0.05), (0.57, front, 2.5), m["olive"]))
    door.append(box("DoorMid", (0.95, 0.05, 0.05), (0.57, front, 1.4), m["olive"]))
    door.append(box("Lock", (0.12, 0.1, 0.2), (1.0, front, 1.4), m["alarm"]))
    for part in door:
        part.rotation_euler = (math.radians(-6), math.radians(4), math.radians(-28))
        part.location.x -= 0.15
        part.location.y += 0.45
    p._merge("HoldingCell")


def _pipe_run(length: float, name: str) -> None:
    """Wall pipes: two water pipes, a steam pipe and a cable tray on brackets. Back against the wall (+Y)."""
    from build_models import box, cylinder

    m = {**p._mats(), **_extra()}
    for i in range(int(length / 1.5) + 1):
        x = -length / 2 + 0.1 + i * (length - 0.2) / int(length / 1.5)
        box(f"Bracket{i}", (0.05, 0.3, 0.42), (x, 0.0, 0.21), m["dark"])
    cylinder("Steam", 0.07, length, (0, -0.02, 0.33), m["steel"], axis="x")
    cylinder("WaterA", 0.04, length, (0, 0.06, 0.15), m["olive"], axis="x")
    cylinder("WaterB", 0.04, length, (0, -0.07, 0.15), m["olive"], axis="x")
    box("Tray", (length, 0.22, 0.02), (0, 0.0, 0.03), m["dark"])
    for k, y in enumerate((-0.06, 0.0, 0.06)):
        cylinder(f"Cable{k}", 0.015, length, (0, y, 0.055), m["alarm"] if k == 1 else m["dark"], axis="x")
    p._merge(name)


def build_pipe_run_3() -> None:
    """3 m wall pipe run (dressing)."""
    _pipe_run(3.0, "PipeRun3")


def build_pipe_run_6() -> None:
    """6 m wall pipe run (dressing)."""
    _pipe_run(6.0, "PipeRun6")


def build_hazard_sign() -> None:
    """Wall plaque: pale plate, red border band and a stencilled hazard triangle. Dressing."""
    from build_models import box

    m = {**p._mats(), **_extra()}
    box("Plate", (0.6, 0.02, 0.45), (0, 0, 0.225), m["paper"])
    box("Band", (0.6, 0.022, 0.1), (0, -0.002, 0.4), m["alarm"])
    for i, (x, z, turn) in enumerate(((-0.07, 0.15, -60), (0.07, 0.15, 60), (0.0, 0.07, 0))):
        bar = box(f"Tri{i}", (0.2, 0.024, 0.025), (x, -0.003, z), m["dark"])
        bar.rotation_euler = (0, math.radians(turn), 0)
    box("Mark", (0.025, 0.026, 0.08), (0, -0.005, 0.15), m["alarm"])
    p._merge("HazardSign")


MODELS = {
    "generator": ("props/generator.glb", build_generator),
    "holding_cell": ("props/holding_cell.glb", build_holding_cell),
    "pipe_run_3": ("dressing/pipe_run_3.glb", build_pipe_run_3),
    "pipe_run_6": ("dressing/pipe_run_6.glb", build_pipe_run_6),
    "hazard_sign": ("dressing/hazard_sign.glb", build_hazard_sign),
}
