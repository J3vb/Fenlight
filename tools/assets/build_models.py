"""Builds the code-made 3D models (style-guide look, stage A) and exports them as .glb.

Run from the repo root:
    pip install -r tools/assets/requirements.txt
    python tools/assets/build_models.py                 # all models into assets/models/
    python tools/assets/build_models.py --out /tmp/x    # somewhere else
    python tools/assets/build_models.py wall_panel      # one model

Blender axes: +Y is the gun's forward, +Z is up. The glTF exporter turns that
into Godot's -Z forward, +Y up. Units are metres.
"""

import argparse
import importlib
import json
import os
import sys

import bpy

# isort: split
# bpy must load before bmesh.
import bmesh
import character_models
import door_models
import finish
import library_barriers
import machine_models
import prop_models
import throwable_models
import town_buildings
import town_cabins
import town_camp
import town_gate
import town_market
import town_props
from mathutils import Vector

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cold Containment palette (see the visual style guide).
# Linear values. Wall paint is #5F6D68 from the guide.
WALL_PAINT = (0.114, 0.153, 0.138, 1.0)
WALL_TRIM = (0.04, 0.05, 0.05, 1.0)
GUN_METAL = (0.2, 0.205, 0.21, 1.0)
MATTE_BLACK = (0.025, 0.025, 0.027, 1.0)
TAN = (0.3, 0.24, 0.16, 1.0)
LENS = (0.05, 0.12, 0.13, 1.0)
WOOD = (0.075, 0.042, 0.022, 1.0)


def srgb(hex_code: str) -> tuple:
    """Style-guide hex colour to the linear RGBA Blender and glTF expect."""
    out = []
    for i in (1, 3, 5):
        c = int(hex_code[i : i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(name: str, color: tuple, metallic: float = 0.0, roughness: float = 0.8, glow: float = 0.0):
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if glow > 0.0:
        bsdf.inputs["Emission Color"].default_value = color
        bsdf.inputs["Emission Strength"].default_value = glow
    return mat


def polished() -> bool:
    """Harden bevelled edges, except while building a model in UNFINISHED."""
    return not bpy.context.scene.get("unfinished", False)


def box(name: str, size: tuple, at: tuple, mat, bevel: float = 0.0, parent=None):
    """A box of `size` (x, y, z) centred on `at`, with optional bevelled edges."""
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=at)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0.0:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = "ANGLE"
        mod.harden_normals = polished()
        bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.data.materials.append(mat)
    obj.parent = parent
    return obj


AXIS_TURN = {"x": (0, 1.5708, 0), "y": (1.5708, 0, 0), "z": (0, 0, 0)}


def cylinder(name: str, radius: float, length: float, at: tuple, mat, parent=None, axis: str = "y"):
    """A cylinder along `axis`; the default +Y is the gun's forward axis."""
    turn = AXIS_TURN[axis]
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=radius, depth=length, location=at, rotation=turn)
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    bpy.ops.object.shade_smooth()
    obj.data.materials.append(mat)
    obj.parent = parent
    return obj


def marker(name: str, at: tuple, parent=None):
    """An empty; exported as a plain Node3D for code to find (muzzle, eject port)."""
    obj = bpy.data.objects.new(name, None)
    obj.location = at
    obj.parent = parent
    bpy.context.scene.collection.objects.link(obj)
    return obj


def build_wall_panel() -> None:
    """Modular wall piece: 2 m wide, 3 m high, 0.2 m thick, origin at bottom centre."""
    paint = material("WallPaint", WALL_PAINT, roughness=0.75)
    trim = material("WallTrim", WALL_TRIM, roughness=0.9)
    box("Panel", (2.0, 0.2, 2.7), (0, 0, 1.65), paint, bevel=0.02)
    box("BaseTrim", (2.0, 0.24, 0.3), (0, 0, 0.15), trim, bevel=0.015)
    box("Stripe", (2.0, 0.22, 0.08), (0, 0, 1.15), trim)
    box("Seam", (0.03, 0.21, 2.7), (0, 0, 1.65), trim)


def gun(module: str, func: str = "build"):
    """Builder for a gun whose shapes and parts live in their own `<module>.py` file."""

    def build() -> None:
        getattr(importlib.import_module(module), func)(sys.modules[__name__])
        for obj in bpy.context.scene.objects:
            if obj.type == "MESH":
                plain_colors(obj)

    return build


def plain_colors(obj) -> None:
    """Gives a mesh with no `Color` attribute a plain white one (alpha 1: no rarity inlay)."""
    if obj.data.color_attributes.get("Color") is not None:
        return
    colors = obj.data.color_attributes.new("Color", "FLOAT_COLOR", "CORNER")
    for color in colors.data:
        color.color = (1.0, 1.0, 1.0, 1.0)


def join_into(target, parts: list) -> None:
    """Merges `parts` into `target` so the static body is one mesh (fewer draw calls).
    If any of them has a `Color` attribute, the others get plain white first: Blender would fill them with
    zero alpha, which the gun shader reads as rarity inlay."""
    objs = [obj for obj in (target, *parts) if obj.type == "MESH"]
    if any(obj.data.color_attributes.get("Color") is not None for obj in objs):
        for obj in objs:
            plain_colors(obj)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in parts:
        obj.select_set(True)
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.join()


def attach(obj, pivot: tuple, parent=None):
    """Moves the origin to `pivot` (the joint code rotates around) and parents without moving."""
    bpy.context.scene.cursor.location = pivot
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    if parent:
        bpy.context.view_layer.update()
        obj.parent = parent
        obj.matrix_parent_inverse = parent.matrix_world.inverted()
    return obj


def ball(name: str, radius: float, at: tuple, mat, squash: tuple = (1, 1, 1), parent=None):
    """A smooth sphere, scaled by `squash`, with its origin at its centre."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=radius, location=at)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = squash
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth()
    obj.data.materials.append(mat)
    return attach(obj, at, parent)


def limb(name: str, start: tuple, end: tuple, radius: float, mat, parent=None):
    """A rounded cylinder from `start` to `end`, origin at `start` so it swings like a joint."""
    a, b = Vector(start), Vector(end)
    tilt = Vector((0, 0, 1)).rotation_difference(b - a).to_euler()
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=12, radius=radius, depth=(b - a).length, location=(a + b) / 2, rotation=tilt
    )
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    mod = obj.modifiers.new("Round", "BEVEL")
    mod.width = radius * 0.6
    mod.segments = 3
    mod.limit_method = "ANGLE"
    mod.harden_normals = polished()
    bpy.ops.object.modifier_apply(modifier=mod.name)
    drop_degenerate_faces(obj)
    bpy.ops.object.shade_auto_smooth()
    obj.data.materials.append(mat)
    return attach(obj, start, parent)


def drop_degenerate_faces(obj) -> None:
    """A bevel wider than a cap ring collapses some faces to zero area; remove them."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=1e-5)
    bm.to_mesh(obj.data)
    bm.free()


def tilted_box(name: str, size: tuple, at: tuple, lean: float, mat, pivot: tuple, parent=None):
    """A bevelled box leaned forward by `lean` radians around its pivot (forward is -Y)."""
    obj = box(name, size, at, mat, bevel=min(size) * 0.25)
    attach(obj, pivot, parent)
    obj.rotation_euler = (lean, 0, 0)
    bpy.context.view_layer.update()
    return obj


# Not finished yet: the Halcyon Labs lightmap was baked on this mesh, so changing it
# needs a GPU re-bake. Remove it from this set together with that bake.
UNFINISHED = {"wall_panel"}
# Guns with baked maps (ADR 0014): their game glb comes from gun_bake.py -> script name.
BAKED = {"rifle_ar": "rifle_model"}
# Models whose game glb carries baked maps from their own script (ADR 0015).
OWN_BAKE = {
    "player": "tools/assets/player_body/build.py",
}

MODELS = {
    "wall_panel": ("kit/wall_panel.glb", build_wall_panel),
    "rifle_ar": ("weapons/rifle_ar.glb", gun("rifle_model")),
    "kestrel_smg": ("weapons/kestrel_smg.glb", gun("kestrel_model", "build_kestrel_smg")),
    "talon_dmr": ("weapons/talon_dmr.glb", gun("talon_model", "build_talon_dmr")),
    "shotgun_brenner": ("weapons/shotgun_brenner.glb", gun("shotgun_model")),
    "hollis_44": ("weapons/hollis_44.glb", gun("hollis_model")),
    "mako_pdw": ("weapons/mako_pdw.glb", gun("mako_model")),
    "atlas_auto": ("weapons/atlas_auto.glb", gun("atlas_model")),
    "halberd_lmg": ("weapons/halberd_lmg.glb", gun("halberd_model")),
    "bastion_lmg": ("weapons/bastion_lmg.glb", gun("bastion_model")),
    "corvid_338": ("weapons/corvid_338.glb", gun("corvid_model")),
    "cryo_lance": ("weapons/cryo_lance.glb", gun("cryo_lance_model")),
    "synapse": ("weapons/synapse.glb", gun("synapse_model")),
    "sentry_br3": ("weapons/sentry_br3.glb", gun("sentry_model")),
    "nightjar_sd": ("weapons/nightjar_sd.glb", gun("nightjar_model")),
    "rampart_br": ("weapons/rampart_br.glb", gun("rampart_model")),
    "fieldhand_lever": ("weapons/fieldhand_lever.glb", gun("fieldhand_model")),
    "ironwood_50": ("weapons/ironwood_50.glb", gun("ironwood_model")),
    "warden_p9": ("weapons/warden_p9.glb", gun("pistol_model")),
    "wren_mp": ("weapons/wren_mp.glb", gun("wren_model")),
    "siphon": ("weapons/siphon.glb", gun("siphon_model")),
    "coachman_2b": ("weapons/coachman_2b.glb", gun("coachman_model")),
    "grubber_sawnoff": ("weapons/grubber_sawnoff.glb", gun("grubber_model")),
}
MODELS.update(character_models.MODELS)
MODELS.update(prop_models.MODELS)
MODELS.update(town_props.MODELS)
MODELS.update(town_buildings.MODELS)
MODELS.update(town_cabins.MODELS)
MODELS.update(town_market.MODELS)
MODELS.update(town_gate.MODELS)
MODELS.update(town_camp.MODELS)
MODELS.update(library_barriers.MODELS)
MODELS.update(door_models.MODELS)
MODELS.update(machine_models.MODELS)
MODELS.update(throwable_models.MODELS)


def export(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    metadata = bpy.context.scene.get("player_arm_grips")
    if metadata is not None:
        metadata = json.dumps(json.loads(metadata), sort_keys=True, allow_nan=False) + "\n"
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        export_yup=True,
        export_apply=True,
        export_vertex_color="ACTIVE",
        export_tangents=bpy.data.materials.get("GeneratorFinish") is not None,
    )
    if metadata is not None:
        with open(os.path.join(os.path.dirname(path), "player_arm_grips.json"), "w", encoding="utf-8") as output:
            output.write(metadata)


def main(argv: list) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("names", nargs="*", help="models to build (default: all)")
    parser.add_argument("--out", default=os.path.join(REPO, "assets", "models"))
    args = parser.parse_args(argv)
    into_assets = os.path.abspath(args.out) == os.path.join(REPO, "assets", "models")
    for name in args.names or MODELS:
        if name not in MODELS:
            sys.exit(f"unknown model: {name} (known: {', '.join(MODELS)})")
        if name in BAKED and into_assets:
            print(f"skipped {name}: a baked gun, run tools/assets/gun_bake.py {name}")
            continue
        if name in OWN_BAKE and into_assets:
            print(f"skipped {name}: run python {OWN_BAKE[name]}")
            continue
        rel_path, build = MODELS[name]
        reset_scene()
        bpy.context.scene["unfinished"] = name in UNFINISHED
        build()
        if name not in UNFINISHED:
            finish.finish()
        export(os.path.join(args.out, rel_path))
        print(f"built {name} -> {rel_path}")


if __name__ == "__main__":
    main(sys.argv[1:])
