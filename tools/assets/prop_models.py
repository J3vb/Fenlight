"""Halcyon Labs props and dressing (plan F-15): specimen tanks, lab bench, jar shelf, filing cabinets.

Every model is one mesh (fewer draw calls), origin at its bottom centre, front facing
Blender -Y (Godot +Z), and fits inside its layout.json box. Props export to props/,
visual-only dressing to dressing/. Monitor screens keep their own `Screen` material.
"""

import math

import bpy


def _mats() -> dict:
    from build_models import material, srgb

    glass = material("Glass", srgb("#CDEEE8"), roughness=0.05)
    glass.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.22
    fluid = material("Fluid", srgb("#8DFF3A"), roughness=0.2, glow=0.35)
    fluid.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.45
    return {
        "steel": material("Steel", srgb("#8A918C"), metallic=0.7, roughness=0.45),
        "dark": material("Dark", srgb("#1C2122"), roughness=0.8),
        "paint": material("Paint", srgb("#5F6D68"), roughness=0.65),
        "glass": glass,
        "fluid": fluid,
        "murk": material("JarFluid", srgb("#4A5446"), roughness=0.25),
        "screen": material("Screen", srgb("#0A1416"), roughness=0.3),
        "paper": material("Paper", srgb("#D9D9D2"), roughness=0.9),
    }


def _cyl(name: str, radius: float, height: float, bottom: tuple, mat, verts: int = 16):
    """Upright cylinder standing on `bottom`."""
    x, y, z = bottom
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=height, location=(x, y, z + height / 2))
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.shade_smooth()
    obj.data.materials.append(mat)
    return obj


def _blob(name: str, radius: float, at: tuple, mat, squash: tuple = (1, 1, 1)):
    """Low-poly smooth sphere for small shapes seen through glass."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=10, ring_count=6, radius=radius, location=at)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = squash
    bpy.ops.object.shade_smooth()
    obj.data.materials.append(mat)
    return obj


def _merge(name: str) -> None:
    """Joins every mesh into one object called `name` and puts the origin at the bottom centre."""
    import halcyon_finish
    from build_models import join_into

    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    mapped = halcyon_finish.apply(name, objs)
    target = objs[0]
    join_into(target, objs[1:])
    if mapped:
        target.data.uv_layers[0].name = "PrintLayout"
    target.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    pts = [target.matrix_world @ v.co for v in target.data.vertices]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    shift = (-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2])
    for v in target.data.vertices:
        v.co.x += shift[0]
        v.co.y += shift[1]
        v.co.z += shift[2]


def _curled_specimen(mat) -> None:
    from mathutils import Vector

    _blob("Head", 0.15, (0.055, -0.025, 1.76), mat, squash=(0.94, 0.87, 1.06))
    torso = _blob("Torso", 0.18, (-0.10, 0.02, 1.48), mat, squash=(0.89, 0.72, 1.42))
    torso.rotation_euler.y = 0.35
    for side in (-1, 1):
        y = 0.095 * side
        shoulder, elbow, wrist = (-0.045, y, 1.62), (0.035, y * 1.4, 1.43), (0.17, y, 1.54)
        hip, knee, ankle = (-0.15, y, 1.30), (0.16, y * 1.2, 1.39), (0.085, y, 1.10 + side * 0.034)
        for name, start, end, radius in (
            ("UpperArm", shoulder, elbow, 0.056),
            ("Forearm", elbow, wrist, 0.045),
            ("Thigh", hip, knee, 0.081),
            ("Shin", knee, ankle, 0.054),
        ):
            delta = Vector(end) - Vector(start)
            segment = _blob(
                f"{name}{side}",
                radius,
                (Vector(start) + Vector(end)) / 2,
                mat,
                squash=(1, 1, delta.length / (2 * radius) + 0.42),
            )
            segment.rotation_euler = delta.to_track_quat("Z", "Y").to_euler()
        _blob(f"Foot{side}", 0.057, (ankle[0] + 0.035, y, ankle[2]), mat, squash=(1.35, 0.76, 0.70))


def build_specimen_tank() -> None:
    """Cold tank: steel base and cap, glass tube, glowing fluid with a curled host inside. Box 1.2 x 1.2 x 2.7."""
    from build_models import material, srgb

    m = _mats()
    liquid = material("IntactTankFluid", srgb("#8DFF3A"), roughness=0.2, glow=0.25)
    liquid.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.30
    _cyl("Base", 0.58, 0.36, (0, 0, 0), m["steel"])
    _cyl("BaseLip", 0.5, 0.05, (0, 0, 0.36), m["dark"])
    _cyl("Tube", 0.45, 2.0, (0, 0, 0.4), m["glass"])
    _cyl("FluidCore", 0.42, 1.8, (0, 0, 0.45), liquid)
    _cyl("CapLip", 0.5, 0.05, (0, 0, 2.39), m["dark"])
    _cyl("Cap", 0.58, 0.26, (0, 0, 2.44), m["steel"])
    for side in (-1, 1):
        _cyl(f"Return{side}", 0.045, 2.12, (side * 0.49, 0.04, 0.34), m["dark"], verts=10)
        for z in (0.36, 1.30, 2.37):
            _cyl(f"Collar{side}_{z}", 0.065, 0.08, (side * 0.49, 0.04, z), m["steel"], verts=10)
    _curled_specimen(m["dark"])
    _merge("SpecimenTank")


def _microscope(m, x: float, top: float) -> None:
    from build_models import box, limb

    box("ScopeFoot", (0.18, 0.24, 0.04), (x, 0.05, top + 0.02), m["paint"], bevel=0.008)
    limb("ScopeArm", (x, 0.13, top + 0.04), (x, 0.08, top + 0.3), 0.025, m["paint"])
    box("ScopeStage", (0.14, 0.12, 0.015), (x, -0.01, top + 0.14), m["dark"])
    limb("ScopeTube", (x, 0.05, top + 0.2), (x, -0.04, top + 0.38), 0.022, m["steel"])


def _terminal(m, x: float, top: float) -> None:
    from build_models import box

    box("MonitorFoot", (0.22, 0.16, 0.02), (x, 0.18, top + 0.01), m["dark"])
    box("MonitorNeck", (0.05, 0.03, 0.16), (x, 0.2, top + 0.1), m["dark"])
    box("Monitor", (0.52, 0.06, 0.36), (x, 0.17, top + 0.36), m["dark"], bevel=0.01)
    box("ScreenFace", (0.46, 0.004, 0.3), (x, 0.138, top + 0.36), m["screen"])
    box("Keyboard", (0.44, 0.15, 0.022), (x, -0.18, top + 0.011), m["dark"])
    box("Tower", (0.2, 0.42, 0.42), (x + 0.45, 0.1, top + 0.21), m["paint"])


def build_lab_bench() -> None:
    """7 m island bench: resin top on painted base units, microscope, centrifuge, terminal, tube racks."""
    from build_models import box

    m = _mats()
    top = 0.93
    box("Top", (7.0, 1.0, 0.06), (0, 0, 0.9), m["dark"], bevel=0.01)
    box("Base", (6.8, 0.84, 0.82), (0, 0.0, 0.46), m["paint"], bevel=0.015)
    box("Kick", (6.7, 0.8, 0.06), (0, 0.02, 0.03), m["dark"])
    for side in (-1, 1):
        for i in range(6):
            x = -2.85 + i * 1.14
            box(f"Drawer{side}{i}", (1.0, 0.02, 0.32), (x, side * 0.425, 0.64), m["steel"])
            box(f"Handle{side}{i}", (0.3, 0.03, 0.025), (x, side * 0.44, 0.72), m["dark"])
    _microscope(m, -2.4, top)
    box("CentrifugeBody", (0.36, 0.36, 0.2), (-1.0, 0.02, top + 0.1), m["paint"], bevel=0.04)
    _cyl("CentrifugeLid", 0.14, 0.03, (-1.0, 0.02, top + 0.2), m["dark"])
    _terminal(m, 0.9, top)
    for r in range(2):
        rx = 2.5 + r * 0.55
        box(f"Rack{r}", (0.36, 0.12, 0.06), (rx, -0.1, top + 0.03), m["paint"])
        for t in range(5):
            _cyl(f"Tube{r}{t}", 0.012, 0.13, (rx - 0.14 + t * 0.07, -0.1, top + 0.03), m["steel"], verts=6)
    box("Binder", (0.32, 0.24, 0.05), (-1.7, -0.2, top + 0.025), m["dark"])
    _merge("LabBench")


JARS = [  # (x, shelf, radius, height, glows)
    (-0.8, 0, 0.08, 0.26, False),
    (-0.55, 0, 0.07, 0.22, False),
    (-0.1, 0, 0.09, 0.3, False),
    (0.3, 0, 0.07, 0.22, False),
    (0.7, 0, 0.08, 0.26, False),
    (-0.75, 1, 0.07, 0.22, False),
    (-0.4, 1, 0.07, 0.22, True),
    (0.05, 1, 0.08, 0.26, False),
    (0.45, 1, 0.07, 0.22, False),
    (0.8, 1, 0.06, 0.18, False),
    (-0.7, 2, 0.08, 0.3, False),
    (-0.2, 2, 0.07, 0.22, False),
    (0.2, 2, 0.09, 0.3, True),
    (0.65, 2, 0.07, 0.22, False),
    (-0.45, 3, 0.07, 0.22, False),
    (0.1, 3, 0.08, 0.26, False),
]


def build_jar_shelf() -> None:
    """Steel wall shelf of specimen jars, two still glowing faintly. Box 2.0 x 0.5 x 2.0."""
    from build_models import box

    m = _mats()
    for sx in (-0.97, 0.97):
        for sy in (-0.22, 0.22):
            box(f"Post{sx}{sy}", (0.04, 0.04, 2.0), (sx, sy, 1.0), m["steel"])
    levels = (0.08, 0.58, 1.08, 1.58)
    for i, z in enumerate(levels):
        box(f"Shelf{i}", (2.0, 0.46, 0.03), (0, 0, z), m["steel"])
    box("TopShelf", (2.0, 0.46, 0.03), (0, 0, 1.985), m["steel"])
    for i, (x, shelf, r, h, glows) in enumerate(JARS):
        z = levels[shelf] + 0.015
        _cyl(f"Jar{i}", r, h, (x, -0.02, z), m["fluid"] if glows else m["murk"], verts=10)
        _cyl(f"Lid{i}", r * 0.9, 0.03, (x, -0.02, z + h), m["dark"], verts=10)
    bpy.ops.mesh.primitive_cylinder_add(vertices=10, radius=0.07, depth=0.22, location=(0.55, -0.05, 1.68))
    tipped = bpy.context.active_object
    tipped.name = "TippedJar"
    tipped.rotation_euler = (0, math.radians(90), math.radians(20))
    tipped.data.materials.append(m["murk"])
    _merge("JarShelf")


def build_filing_cabinets() -> None:
    """Two four-drawer cabinets, one drawer yanked open with papers spilling. Box 1.0 x 0.85 x 1.3."""
    from build_models import box

    m = _mats()
    back = 0.425
    for c, x in enumerate((-0.25, 0.25)):
        box(f"Body{c}", (0.48, 0.6, 1.3), (x, back - 0.3, 0.65), m["paint"], bevel=0.01)
        for d in range(4):
            z = 0.18 + d * 0.31
            if c == 1 and d == 2:
                continue
            box(f"Front{c}{d}", (0.42, 0.02, 0.27), (x, back - 0.61, z), m["steel"])
            box(f"Pull{c}{d}", (0.14, 0.03, 0.025), (x, back - 0.63, z + 0.07), m["dark"])
    z = 0.18 + 2 * 0.31
    box("OpenDrawer", (0.42, 0.5, 0.25), (0.25, back - 0.6, z), m["steel"], bevel=0.005)
    box("OpenPull", (0.14, 0.03, 0.025), (0.25, -back + 0.01, z + 0.07), m["dark"])
    for i in range(5):
        sheet = box(f"Folder{i}", (0.38, 0.012, 0.24), (0.25, back - 0.8 + i * 0.07, z + 0.1), m["paper"])
        sheet.rotation_euler = (math.radians(-12 + i * 5), 0, 0)
    _merge("FilingCabinets")


PAPERS = [(0.0, 0.0, 10), (0.25, 0.12, -25), (-0.3, 0.2, 40), (0.5, -0.2, 75), (-0.15, -0.3, -60), (0.7, 0.3, 15)]


def build_lab_papers() -> None:
    """Floor dressing: scattered papers and a dropped clipboard (no collision)."""
    from build_models import box

    m = _mats()
    for i, (x, y, turn) in enumerate(PAPERS):
        sheet = box(f"Sheet{i}", (0.21, 0.297, 0.002), (x, y, 0.001 + i * 0.0021), m["paper"])
        sheet.rotation_euler = (0, 0, math.radians(turn))
    board = box("Clipboard", (0.23, 0.32, 0.008), (-0.55, -0.05, 0.004), m["dark"])
    board.rotation_euler = (0, 0, math.radians(-15))
    _merge("LabPapers")


MODELS = {
    "specimen_tank": ("props/specimen_tank.glb", build_specimen_tank),
    "lab_bench": ("props/lab_bench.glb", build_lab_bench),
    "jar_shelf": ("props/jar_shelf.glb", build_jar_shelf),
    "filing_cabinets": ("props/filing_cabinets.glb", build_filing_cabinets),
    "lab_papers": ("dressing/lab_papers.glb", build_lab_papers),
}


# Area modules import the helpers above, so they load last.
import props_aftermath  # noqa: E402
import props_ceiling  # noqa: E402
import props_dock  # noqa: E402
import props_fenlight  # noqa: E402
import props_mess_guard  # noqa: E402
import props_power_containment  # noqa: E402
import props_wreck_containment  # noqa: E402
import props_wreck_labs  # noqa: E402
import props_wreck_mess  # noqa: E402

MODELS.update(props_mess_guard.MODELS)
MODELS.update(props_power_containment.MODELS)
MODELS.update(props_dock.MODELS)
MODELS.update(props_aftermath.MODELS)
MODELS.update(props_fenlight.MODELS)
MODELS.update(props_wreck_mess.MODELS)
MODELS.update(props_ceiling.MODELS)
MODELS.update(props_wreck_labs.MODELS)
MODELS.update(props_wreck_containment.MODELS)
