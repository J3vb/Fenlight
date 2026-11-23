"""Loading Dock props (plan F-15 step 4): the burnt-out supply truck, supply crates, fuel drum and a
forklift. Same rules as prop_models.py.
"""

import bpy
import prop_models as p


def _dock():
    from build_models import material, srgb

    return {
        "olive": material("Olive", srgb("#4A5446"), roughness=0.7),
        "sodium": material("SodiumPaint", srgb("#FF9A42"), roughness=0.6),
        "wood": material("Wood", (0.16, 0.11, 0.065, 1.0), roughness=0.85),
    }


def _wheel(m, name: str, x: float, y: float, radius: float, width: float) -> None:
    from build_models import cylinder

    cylinder(name, radius, width, (x, y, radius), m["dark"], axis="x")
    cylinder(name + "Hub", radius * 0.45, width + 0.02, (x, y, radius), m["steel"], axis="x")


def build_supply_truck() -> None:
    """Burnt-out supply truck backed into the dock: charred cab at the front (-Y), box body, six wheels.
    Box 2.6 x 2.8 x 7."""
    from build_models import box

    m = {**p._mats(), **_dock()}
    box("Chassis", (1.9, 6.8, 0.25), (0, 0.05, 0.72), m["dark"])
    box("Body", (2.6, 4.6, 2.0), (0, 1.1, 1.8), m["olive"], bevel=0.03)
    box("BodyScorch", (2.62, 1.2, 1.2), (0, -0.9, 2.2), m["dark"])
    box("Doors", (2.4, 0.04, 1.8), (0, 3.42, 1.8), m["steel"])
    box("Cab", (2.4, 1.7, 1.4), (0, -2.45, 1.55), m["dark"], bevel=0.06)
    box("CabRoof", (2.3, 1.3, 0.12), (0, -2.35, 2.31), m["olive"], bevel=0.02)
    box("Hood", (2.2, 0.75, 0.75), (0, -3.25, 1.2), m["dark"], bevel=0.05)
    box("Bumper", (2.5, 0.12, 0.22), (0, -3.56, 0.72), m["steel"])
    box("Windscreen", (2.1, 0.05, 0.55), (0, -3.29, 1.95), m["dark"])
    for side in (-1, 1):
        box(f"Mirror{side}", (0.08, 0.06, 0.3), (side * 1.27, -2.9, 1.95), m["steel"])
        for k, y in enumerate((-2.85, 1.9, 2.85)):
            _wheel(m, f"Wheel{side}{k}", side * 1.0, y, 0.5, 0.36)
    p._merge("SupplyTruck")


def _crate(m, name: str, size: tuple, at: tuple) -> None:
    """Wooden supply crate with steel corner bands and a pale stencil panel."""
    from build_models import box

    sx, sy, sz = size
    x, y, z = at
    box(name, size, (x, y, z + sz / 2), m["wood"], bevel=0.02)
    for band in (-1, 1):
        box(f"{name}Band{band}", (sx + 0.02, 0.06, sz + 0.02), (x, y + band * (sy / 2 - 0.1), z + sz / 2), m["steel"])
    box(f"{name}Stencil", (sx * 0.5, 0.012, sz * 0.25), (x, y - sy / 2 - 0.006, z + sz * 0.6), m["paper"])


def build_crate_stack() -> None:
    """A 1 m crate with a smaller one shoved on top. Box 1.1 x 1.8 x 1.05."""
    m = {**p._mats(), **_dock()}
    _crate(m, "Lower", (1.0, 1.0, 1.0), (-0.05, -0.02, 0.0))
    _crate(m, "Upper", (0.8, 0.8, 0.8), (0.15, 0.08, 1.0))
    p._merge("CrateStack")


def build_crate_long() -> None:
    """Long ammunition crate. Box 0.9 x 0.9 x 1.2 (long side along z)."""
    m = {**p._mats(), **_dock()}
    _crate(m, "Crate", (0.9, 1.2, 0.9), (0, 0, 0))
    p._merge("CrateLong")


def build_crate_large() -> None:
    """Large supply crate. Box 1.2 x 1.2 x 1.2."""
    m = {**p._mats(), **_dock()}
    _crate(m, "Crate", (1.2, 1.2, 1.2), (0, 0, 0))
    p._merge("CrateLarge")


def build_fuel_drum() -> None:
    """Dented steel fuel drum with rolling hoops and a bung. Box 0.6 x 0.9 x 0.6."""
    m = {**p._mats(), **_dock()}
    p._cyl("Drum", 0.29, 0.88, (0, 0, 0.0), m["olive"])
    for z in (0.28, 0.58):
        p._cyl(f"Hoop{z}", 0.3, 0.03, (0, 0, z), m["dark"])
    p._cyl("Lid", 0.27, 0.02, (0, 0, 0.88), m["steel"])
    p._cyl("Bung", 0.04, 0.02, (0.15, 0.05, 0.89), m["dark"], verts=8)
    p._merge("FuelDrum")


def build_forklift() -> None:
    """Small dock forklift, forks lowered, mast up. Box 2.4 x 2.2 x 1.2 (long side along x, forks at -x)."""
    from build_models import box, cylinder

    m = {**p._mats(), **_dock()}
    box("Body", (0.91, 1.06, 0.75), (0.255, 0, 0.6), m["sodium"], bevel=0.05)
    box("Counterweight", (0.63, 1.12, 0.69), (0.90, 0, 0.61), m["sodium"], bevel=0.15)
    box("RearBumper", (0.20, 0.96, 0.12), (1.11, 0, 0.34), m["dark"], bevel=0.04)
    column = box("SteeringColumn", (0.12, 0.12, 0.41), (-0.01, 0, 1.12), m["dark"], bevel=0.02)
    column.rotation_euler.y = 0.36
    bpy.ops.mesh.primitive_torus_add(
        major_segments=16,
        minor_segments=6,
        major_radius=0.15,
        minor_radius=0.021,
        location=(0.06, 0, 1.31),
        rotation=(0, 0.70, 0),
    )
    wheel = bpy.context.object
    wheel.name = "SteeringWheel"
    wheel.data.materials.append(m["dark"])
    box("WheelSpoke", (0.035, 0.29, 0.027), (0.06, 0, 1.31), m["steel"])
    box("Seat", (0.4, 0.45, 0.12), (0.55, 0, 1.03), m["dark"])
    box("SeatBack", (0.08, 0.45, 0.4), (0.78, 0, 1.25), m["dark"])
    for y in (-0.5, 0.5):
        box(f"Step{y}", (0.49, 0.13, 0.075), (0.34, y, 0.40), m["dark"], bevel=0.016)
        box(f"GuardPost{y}", (0.05, 0.05, 1.25), (0.05, y, 1.6), m["dark"])
        box(f"GuardPostRear{y}", (0.05, 0.05, 1.25), (0.95, y, 1.6), m["dark"])
        box(f"Mast{y}", (0.08, 0.1, 2.15), (-0.32, y * 0.6, 1.08), m["steel"])
        box(f"Fork{y}", (0.9, 0.1, 0.05), (-0.75, y * 0.5, 0.06), m["steel"])
        box(f"ForkUp{y}", (0.05, 0.1, 0.5), (-0.33, y * 0.5, 0.3), m["steel"])
    box("Canopy", (1.0, 1.1, 0.06), (0.5, 0, 2.2), m["dark"])
    box("Carriage", (0.08, 0.95, 0.35), (-0.3, 0, 0.45), m["steel"])
    for x, r in ((-0.05, 0.25), (0.95, 0.22)):
        for y in (-0.52, 0.52):
            cylinder(f"Wheel{x}{y}", r, 0.18, (x, y, r), m["dark"], axis="y")
            cylinder(f"Hub{x}{y}", r * 0.61, 0.026, (x, y * 1.18, r), m["steel"], axis="y")
    p._merge("Forklift")


MODELS = {
    "supply_truck": ("props/supply_truck.glb", build_supply_truck),
    "crate_stack": ("props/crate_stack.glb", build_crate_stack),
    "crate_long": ("props/crate_long.glb", build_crate_long),
    "crate_large": ("props/crate_large.glb", build_crate_large),
    "fuel_drum": ("props/fuel_drum.glb", build_fuel_drum),
    "forklift": ("props/forklift.glb", build_forklift),
}
