"""Checks exported .glb models against the project's model rules.

Run from the repo root:
    python tools/assets/check_models.py                   # every .glb in assets/models/
    python tools/assets/check_models.py --dir /tmp/models # a build output folder

Checks per model: triangle and material budget, origin, forward axis, named
joints with the right parents, closed shells with outward normals, materials.
Rules come from the model's folder (kit/weapons/zombies) and its file name.

After import, Blender axes are: +Z up, Godot's +Z (zombie front) is Blender -Y,
Godot's -Z (gun forward) is Blender +Y.
"""

import argparse
import glob
import os
import sys

import bpy

# isort: split
# bpy must load before bmesh.
import bmesh
import character_checks
import zombie_checks
from mathutils import Matrix, Vector

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Per folder: triangle budget, material budget.
BUDGETS = {
    "kit": (2_000, 4),
    "weapons": (30_000, 6),
    "zombies": (9_000, 8),
    "props": (2_000, 4),
    "dressing": (1_000, 4),
    "doors": (2_000, 4),
    "machines": (2_000, 4),
    "town": (2_500, 4),
    "town_large": (12_000, 6),
    "props_large": (12_000, 6),
    "throwables": (1_500, 3),
}
BUDGETS.update(character_checks.BUDGETS)

GUN = {"Receiver": None, "Muzzle": "Receiver", "Bolt": "Receiver"}
DOUBLE_BARREL = {
    **GUN,
    "Hinge": "Receiver",
    "BarrelL": "Hinge",
    "BarrelR": "Hinge",
    "Foregrip": "Hinge",
    "Muzzle": "Hinge",
}
GUN_WITH_MAG = {**GUN, "Magazine": "Receiver"}

# Folders of models that never move: a model here needs no JOINTS line.
STATIC = {"kit", "props", "props_large", "dressing", "doors", "machines", "town", "town_large"}

# Required node -> required ancestor (None = any). Code finds these by name.
JOINTS = {
    "frag": {},
    "rifle_ar": GUN_WITH_MAG,
    "kestrel_smg": GUN_WITH_MAG,
    "talon_dmr": GUN_WITH_MAG,
    "shotgun_brenner": GUN,
    "hollis_44": GUN,
    "mako_pdw": GUN_WITH_MAG,
    "atlas_auto": GUN_WITH_MAG,
    "halberd_lmg": GUN_WITH_MAG,
    "bastion_lmg": {
        **GUN_WITH_MAG,
        "Belt": "Receiver",
        "FeedCover": "Receiver",
        "Bipod": "Receiver",
        "CarryHandle": "Receiver",
    },
    "corvid_338": GUN_WITH_MAG,
    "cryo_lance": {**GUN_WITH_MAG, "Trigger": "Receiver", "CondenserCoils": "Receiver"},
    "synapse": {**GUN_WITH_MAG, "Trigger": "Receiver", "Cabling": "Receiver"},
    "sentry_br3": GUN_WITH_MAG,
    "nightjar_sd": {**GUN_WITH_MAG, "Suppressor": "Receiver"},
    "rampart_br": GUN_WITH_MAG,
    "fieldhand_lever": {**GUN, "Lever": "Receiver", "MagazineTube": "Receiver"},
    "ironwood_50": {**GUN_WITH_MAG, "ScopeLensMount": "Receiver"},
    "warden_p9": {**GUN_WITH_MAG, "Slide": "Bolt", "Trigger": "Receiver"},
    "wren_mp": {**GUN_WITH_MAG, "Slide": "Bolt", "Trigger": "Receiver", "Brace": "Receiver"},
    "siphon": {**GUN_WITH_MAG, "Emitter": "Receiver", "Core": "Receiver", "Stock": "Receiver"},
    "coachman_2b": {**DOUBLE_BARREL, "Stock": "Receiver", "Trigger": "Receiver"},
    "grubber_sawnoff": {**DOUBLE_BARREL, "Grip": "Receiver", "Trigger": "Receiver"},
    **zombie_checks.JOINTS,
}
JOINTS.update(character_checks.JOINTS)

TOLERANCE = 0.01


def load_glb(path: str) -> list:
    """Empties the scene, imports `path` and returns its objects."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path, disable_bone_shape=True)
    rest_pose()
    return list(bpy.context.scene.objects)


def rest_pose() -> None:
    """The glTF importer leaves the first clip playing; checks measure the rest pose."""
    for obj in bpy.context.scene.objects:
        if obj.type == "ARMATURE" and obj.animation_data:
            obj.animation_data.action = None
            for pbone in obj.pose.bones:
                pbone.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()


def world_mesh(obj) -> bmesh.types.BMesh:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    return bm


def bounds(objects: list) -> tuple:
    lo, hi = Vector((1e9, 1e9, 1e9)), Vector((-1e9, -1e9, -1e9))
    for obj in objects:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            p = obj.matrix_world @ Vector(corner)
            lo, hi = Vector(map(min, lo, p)), Vector(map(max, hi, p))
    return lo, hi


def shell_volumes(bm: bmesh.types.BMesh) -> list:
    """Signed volume of each closed shell; negative means the normals point inwards.
    glTF splits vertices at hard edges, so they are welded first."""
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    seen, volumes = set(), []
    for start in bm.faces:
        if start.index in seen:
            continue
        shell, todo = [], [start]
        seen.add(start.index)
        while todo:
            face = todo.pop()
            shell.append(face)
            for edge in face.edges:
                for other in edge.link_faces:
                    if other.index not in seen:
                        seen.add(other.index)
                        todo.append(other)
        if all(len(e.link_faces) == 2 for f in shell for e in f.edges):
            volumes.append(sum(f.verts[0].co.dot(f.verts[1].co.cross(f.verts[2].co)) for f in shell) / 6.0)
    return volumes


def check_geometry(objects: list, folder: str) -> list:
    errors = []
    tri_budget, mat_budget = BUDGETS[folder]
    tris, materials = 0, set()
    for obj in objects:
        if obj.type != "MESH":
            continue
        bm = world_mesh(obj)
        bm.faces.index_update()
        tris += len(bm.faces)
        if any(f.calc_area() < 1e-10 for f in bm.faces):
            errors.append(f"{obj.name}: has zero-area faces")
        if any(v < -1e-9 for v in shell_volumes(bm)):
            errors.append(f"{obj.name}: a closed part has inward normals (flipped faces)")
        bm.free()
        slots = list(obj.data.materials)
        if not slots or any(m is None for m in slots):
            errors.append(f"{obj.name}: every mesh needs a material in every slot")
        for mat in filter(None, slots):
            materials.add(mat.name)
            if mat.name.startswith("Material"):
                errors.append(f"{obj.name}: material '{mat.name}' needs a real name")
    if tris > tri_budget:
        errors.append(f"{tris} triangles, budget for {folder} is {tri_budget}")
    if len(materials) > mat_budget:
        errors.append(f"{len(materials)} materials, budget for {folder} is {mat_budget}")
    return errors


def check_origin(objects: list, folder: str) -> list:
    if folder in character_checks.BUDGETS:
        return []
    lo, hi = bounds(objects)
    centre = (lo + hi) / 2
    if folder in ("weapons", "throwables"):
        inside = all(lo[i] - TOLERANCE <= 0.0 <= hi[i] + TOLERANCE for i in range(3))
        return [] if inside else [f"origin must sit inside the gun, bounds are {fmt(lo)} to {fmt(hi)}"]
    errors = []
    if abs(lo.z) > TOLERANCE:
        errors.append(f"lowest point is at height {lo.z:.3f}, must be 0 (feet/bottom on the origin)")
    limit = 0.05 if folder in ("kit", "props", "dressing", "doors", "machines") else 0.35
    if Vector((centre.x, centre.y)).length > limit:
        errors.append(f"origin is {Vector((centre.x, centre.y)).length:.2f} m from the footprint centre (max {limit})")
    return errors


def check_forward(nodes: dict, objects: list, folder: str) -> list:
    if folder == "weapons" and "Muzzle" in nodes:
        _lo, hi = bounds(objects)
        tip = nodes["Muzzle"].matrix_world.translation.y
        if tip < hi.y - 0.05 or tip <= 0.0:
            return [f"Muzzle (y {tip:.3f}) must be at the front of the gun (y {hi.y:.3f}); forward is Godot -Z"]
    return []


def check_joints(nodes: dict, stem: str) -> list:
    errors = []
    for name, ancestor in JOINTS.get(stem, {}).items():
        node = nodes.get(name)
        if node is None:
            errors.append(f"missing node '{name}'")
            continue
        chain, parent = [], node.parent
        while parent:
            chain.append(parent.name)
            parent = parent.parent
        if ancestor and ancestor not in chain:
            errors.append(f"'{name}' must be under '{ancestor}'")
        if node.type == "MESH":
            lo, hi = bounds([node])
            at = node.matrix_world.translation
            armature = node.find_armature()
            if (
                stem in character_checks.VEST_BUDGETS
                and name == "Shell"
                and armature is not None
                and (at - armature.matrix_world.translation).length <= TOLERANCE
            ):
                continue  # glTF skins use their skeleton origin, while their vertices stay in the body rest pose.
            if not all(lo[i] - 0.03 <= at[i] <= hi[i] + 0.03 for i in range(3)):
                errors.append(f"'{name}' pivot {fmt(at)} is off the part; put the origin on the joint")
    return errors


def fmt(v: Vector) -> str:
    return "(" + ", ".join(f"{c:.3f}" for c in v) + ")"


def check_model(path: str) -> list:
    """All rule breaks for one .glb, as readable strings."""
    folder = os.path.basename(os.path.dirname(path))
    stem = os.path.splitext(os.path.basename(path))[0]
    if folder not in BUDGETS:
        return [f"unknown model folder '{folder}', add it to BUDGETS in check_models.py"]
    if stem not in JOINTS and folder not in STATIC:
        target = "character_checks.py" if folder in character_checks.BUDGETS else "JOINTS in check_models.py"
        return [f"no rules for '{stem}', add it to {target}"]
    objects = load_glb(path)
    nodes = {obj.name: obj for obj in objects}
    return (
        check_geometry(objects, folder)
        + check_origin(objects, folder)
        + check_forward(nodes, objects, folder)
        + check_joints(nodes, stem)
        + character_checks.check(objects, folder, stem)
        + (zombie_checks.check(objects, stem) if folder == "zombies" else [])
    )


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dir", default=os.path.join(REPO, "assets", "models"))
    args = parser.parse_args(argv)
    paths = sorted(glob.glob(os.path.join(args.dir, "**", "*.glb"), recursive=True))
    if not paths:
        print(f"no .glb files in {args.dir}")
        return 1
    failed = 0
    for path in paths:
        errors = check_model(path)
        rel = os.path.relpath(path, args.dir)
        print(("FAIL " if errors else "ok   ") + rel)
        for error in errors:
            print(f"     - {error}")
        failed += bool(errors)
    print(f"{len(paths) - failed}/{len(paths)} models pass")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
