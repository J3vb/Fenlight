"""Throwables (plan F-24 step 4): the frag grenade.

Origin at the body's centre (a RigidBody spins around it), fuze up Blender +Z.
Olive steel body, steel fuze, dark safety lever and a steel pin ring; colours
from look-rules.md. Nothing moves in code, so there are no joints.
"""

import math

import bpy

# Egg-shaped body: (radius, height) from the bottom up.
BODY = [
    (0.008, -0.040),
    (0.020, -0.036),
    (0.028, -0.028),
    (0.032, -0.015),
    (0.0328, -0.006),
    (0.0336, -0.0045),
    (0.0336, -0.0025),
    (0.0325, -0.0015),
    (0.0325, 0.0015),
    (0.0336, 0.0025),
    (0.0336, 0.0045),
    (0.0328, 0.006),
    (0.031, 0.014),
    (0.025, 0.024),
    (0.016, 0.031),
    (0.012, 0.032),
]
FUZE = [(0.0115, 0.031), (0.0115, 0.044), (0.0095, 0.048), (0.006, 0.049)]
RING_AT = (-0.024, 0.0, 0.040)


def build_frag() -> None:
    from build_models import box, material, srgb
    from gun_parts import lathe

    olive = material("OliveCoat", srgb("#4A5446"), roughness=0.6)
    steel = material("GunMetal", srgb("#8A918C"), metallic=0.7, roughness=0.45)
    dark = material("MatteBlack", srgb("#1C2122"), roughness=0.7)
    body = lathe("Body", BODY, (0, 0, 0), olive, segments=22, axis="z")
    body.data.materials.append(dark)
    for face in body.data.polygons:
        if abs(face.center.z) < 0.001:
            face.material_index = 1
    lathe("Fuze", FUZE, (0, 0, 0), steel, segments=16, axis="z")
    box("LeverTop", (0.026, 0.012, 0.003), (0.010, 0.0, 0.0505), dark, bevel=0.0008)
    box("LeverSide", (0.003, 0.012, 0.058), (0.0245, 0.0, 0.020), dark, bevel=0.0008)
    box("LeverBend", (0.006, 0.012, 0.003), (0.022, 0.0, 0.0495), dark, bevel=0.0008)
    lathe("Pin", [(0.0013, -0.0115), (0.0013, -0.020)], (0, 0, 0.040), steel, segments=6, axis="x")
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.0085, minor_radius=0.0013, major_segments=16, minor_segments=6, location=RING_AT
    )
    ring = bpy.context.active_object
    ring.name = "PinRing"
    ring.rotation_euler = (math.pi / 2, 0.0, 0.0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    ring.data.materials.append(steel)


MODELS = {
    "frag": ("throwables/frag.glb", build_frag),
}
