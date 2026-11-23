"""Aftermath props everywhere (plan F-15 step 5): barricades where the staff held a door, covered
gurneys and body bags. Same rules as prop_models.py.
"""

import math

import bpy
import prop_models as p


def _extra():
    from build_models import material

    return {"wood": material("Wood", (0.16, 0.11, 0.065, 1.0), roughness=0.85)}


def build_barricade() -> None:
    """Overturned canteen table braced with planks and a crate. Box 2.4 x 1.4 x 0.9 (long side along x)."""
    from build_models import box

    m = {**p._mats(), **_extra()}
    top = box("TableTop", (2.2, 0.05, 1.0), (0.0, 0.2, 0.55), m["paint"], bevel=0.01)
    top.rotation_euler = (math.radians(-10), 0, 0)
    for x in (-0.95, 0.95):
        box(f"Leg{x}", (0.05, 0.6, 0.05), (x, -0.12, 0.85), m["steel"])
        box(f"LegLow{x}", (0.05, 0.6, 0.05), (x, -0.12, 0.3), m["steel"])
    for i, (x, turn) in enumerate(((-0.5, 22), (0.35, -18), (0.9, 30))):
        plank = box(f"Plank{i}", (0.16, 0.03, 1.3), (x, 0.32, 0.65), m["wood"])
        plank.rotation_euler = (0, math.radians(turn), 0)
    box("Crate", (0.7, 0.6, 0.6), (-0.7, -0.12, 0.3), m["wood"], bevel=0.02)
    box("Sandbag", (0.6, 0.3, 0.18), (0.5, -0.25, 0.09), m["dark"], bevel=0.06)
    p._merge("Barricade")


SHEET_SECTIONS = (
    (-0.97, 0.65, 0.12),
    (-0.89, 0.78, 0.13),
    (-0.78, 0.87, 0.13),
    (-0.64, 0.86, 0.13),
    (-0.56, 0.78, 0.10),
    (-0.44, 0.90, 0.22),
    (-0.27, 0.93, 0.23),
    (-0.08, 0.87, 0.20),
    (0.12, 0.83, 0.19),
    (0.32, 0.80, 0.17),
    (0.51, 0.85, 0.15),
    (0.72, 0.77, 0.12),
    (0.87, 0.79, 0.10),
    (0.97, 0.65, 0.08),
)


def _draped_sheet(mat) -> None:
    # Each cross-section runs from the hanging near hem over the patient to the far hem.
    # The neck dips between the pillow and shoulders; raised knees interrupt the slope to the feet.
    vertices, faces = [], []
    for i, (x, height, width) in enumerate(SHEET_SECTIONS):
        fold = math.sin(i * 2.16)
        hem = 0.48 + 0.045 * fold + 0.08 * abs(x) ** 3
        near, far = -0.329 - 0.018 * fold, 0.329 + 0.013 * math.cos(i * 2.0)
        profile = (
            (near, hem),
            (-0.318, 0.65),
            (-width, height - 0.055),
            (-0.045, height),
            (width * 0.69, height - 0.015),
            (width, height - 0.07),
            (0.318, 0.65),
            (far, hem + 0.015),
            (0, hem + 0.018),
        )
        start = len(vertices)
        vertices.extend((x, y, z) for y, z in profile)
        count = len(profile)
        if i:
            for j in range(count):
                k = (j + 1) % count
                faces.append((start - count + j, start + j, start + k, start - count + k))
    faces.extend([tuple(range(count)), tuple(reversed(range(start, start + count)))])
    mesh = bpy.data.meshes.new("DrapedSheet")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("DrapedSheet", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(mat)
    bpy.context.view_layer.objects.active = obj
    soften = obj.modifiers.new("Cloth folds", "SUBSURF")
    soften.levels = 1
    bpy.ops.object.modifier_apply(modifier=soften.name)


def build_covered_gurney() -> None:
    """Hospital trolley with a single draped sheet, scissor lift and four casters."""
    from build_models import box, cylinder

    m = p._mats()
    box("Frame", (1.9, 0.60, 0.065), (0, 0, 0.60), m["steel"])
    for y in (-0.25, 0.25):
        box(f"BaseRail{y}", (1.62, 0.052, 0.065), (0, y, 0.18), m["steel"])
        for side in (-1, 1):
            arm = box(f"Lift{side}{y}", (1.35, 0.035, 0.043), (0, y + side * 0.02, 0.38), m["steel"])
            arm.rotation_euler.y = side * 0.31
            x = side * 0.78
            box(f"Fork{x}{y}", (0.078, 0.052, 0.12), (x, y, 0.147), m["steel"])
            cylinder(f"Caster{x}{y}", 0.08, 0.060, (x + 0.023, y, 0.08), m["dark"], axis="y")
        cylinder(f"Pivot{y}", 0.045, 0.09, (0, y, 0.38), m["dark"], axis="y")
    for x in (-0.75, 0.75):
        box(f"CrossRail{x}", (0.05, 0.5, 0.05), (x, 0, 0.18), m["steel"])
    _draped_sheet(m["paper"])
    p._merge("CoveredGurney")


def build_body_bag() -> None:
    """Zipped black body bag lying on the floor (dressing). About 1.9 x 0.6 x 0.3."""
    from build_models import box

    m = p._mats()
    p._blob("Bag", 0.3, (0.0, 0.0, 0.15), m["dark"], squash=(3.1, 0.95, 0.48))
    p._blob("Shoulders", 0.22, (-0.55, 0.0, 0.18), m["dark"], squash=(1.0, 1.25, 0.6))
    box("Zip", (0.9, 0.02, 0.01), (0.05, 0.0, 0.29), m["steel"])
    box("Tag", (0.08, 0.05, 0.005), (0.85, 0.12, 0.2), m["paper"])
    p._merge("BodyBag")


MODELS = {
    "barricade": ("props/barricade.glb", build_barricade),
    "covered_gurney": ("props/covered_gurney.glb", build_covered_gurney),
    "body_bag": ("dressing/body_bag.glb", build_body_bag),
}
