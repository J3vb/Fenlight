"""Turns a Tripo (image to 3D) .glb into a game-ready model on our budgets and three baked maps.

    python tools/assets/tripo_intake.py source.glb --kind prop --height 0.9 --name crate
    python tools/assets/tripo_intake.py odile.glb --kind character --name odile_brandt
    python tools/assets/tripo_intake.py track.glb --length 6 --name track_section --folder props
    python tools/assets/tripo_intake.py glower.glb --kind zombie --height 1.7 --name glower --folder zombies

Joins the source meshes, turns the front to Blender -Y (Godot +Z), scales to height, puts the
origin at the floor centre, decimates a copy to budget, unwraps it and bakes the source look into
albedo / normal / ORM maps, then exports one mesh with one `Baked` material.
"""

import argparse
import math
import os
import sys

import bpy

# isort: split
import bmesh
import numpy
import shambler_hand
import tripo_crawler
import tripo_rig
from mathutils import Matrix, Vector
from player_body.build import strip_icc

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "docs", "design", "reviews", "tripo-trial")
MODELS = os.path.join(REPO, "assets", "models")
KINDS = {
    "prop": (2_000, 1024, None),
    "large": (12_000, 2048, None),
    "character": (16_000, 2048, 1.8),
    "zombie": (9_000, 2048, 1.7),
}
## Thin or open Tripo meshes can stop above budget after one collapse; later passes take the rest.
DECIMATE_PASSES = 4
BAKED = "Baked"  # characters: "BodyBaked", the Body* finish the character checks expect; zombies: "ZombieBaked"
CHANNELS = ("albedo", "roughness", "metal")


def load_source(path: str) -> tuple:
    """Empties the scene, imports the source and returns (joined mesh, armature or None)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path, disable_bone_shape=True)
    armature = next((o for o in bpy.context.scene.objects if o.type == "ARMATURE"), None)
    if armature is not None and armature.animation_data:
        armature.animation_data.action = None
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        raise SystemExit(f"{path}: no meshes")
    if armature is not None:
        tripo_rig.a_pose(armature, meshes)
    for obj in meshes:
        for mod in [m for m in obj.modifiers if m.type == "ARMATURE"]:
            obj.modifiers.remove(mod)
        world = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    high = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    high.name = "Source"
    return high, armature


def world_bounds(obj) -> tuple:
    points = numpy.empty(len(obj.data.vertices) * 3, dtype=numpy.float64)
    obj.data.vertices.foreach_get("co", points)
    points = points.reshape(-1, 3)
    return Vector(points.min(axis=0)), Vector(points.max(axis=0))


def place_matrix(obj, height: float, yaw_degrees: float, length: float = 0.0) -> Matrix:
    """Turn about Z, scale to height (or the longest side to length), then move the floor centre to the origin."""
    turn = Matrix.Rotation(math.radians(yaw_degrees), 4, "Z")
    obj.data.transform(turn)
    lo, hi = world_bounds(obj)
    scale = length / max(*(hi - lo), 1e-6) if length else height / max(hi.z - lo.z, 1e-6)
    centre = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    move = Matrix.Scale(scale, 4) @ Matrix.Translation(-centre)
    obj.data.transform(move)
    obj.data.update()
    return move @ turn


def triangle_count(obj) -> int:
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def make_low(high, budget: int):
    """A decimated copy under budget, triangulated, with clean normals."""
    low = high.copy()
    low.data = high.data.copy()
    low.name = "Model"
    bpy.context.collection.objects.link(low)
    weld(low)
    bpy.context.view_layer.objects.active = low
    for _attempt in range(DECIMATE_PASSES):
        ratio = budget * 0.96 / max(triangle_count(low), 1)
        if ratio >= 1.0:
            break
        mod = low.modifiers.new("Decimate", "DECIMATE")
        mod.ratio = ratio
        mod.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=mod.name)
    clean(low)
    floor, _top = world_bounds(low)
    low.data.transform(Matrix.Translation((0.0, 0.0, -floor.z)))
    return low


def weld(obj) -> None:
    """Tripo splits vertices at UV seams; welding stops the decimate from tearing them open."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    # Edges shared by three or more faces stop the collapse decimate; split, they collapse like open edges.
    bmesh.ops.split_edges(bm, edges=[e for e in bm.edges if len(e.link_faces) > 2])
    bm.to_mesh(obj.data)
    bm.free()


def clean(obj) -> None:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=1e-6)
    bad = [f for f in bm.faces if f.calc_area() < 1e-10]
    bmesh.ops.delete(bm, geom=bad, context="FACES")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(obj.data)
    bm.free()
    for poly in obj.data.polygons:
        poly.use_smooth = True


def unwrap(obj) -> None:
    """Fresh UVs for the low mesh: smart project, then pack tight to use the whole map."""
    for layer in list(obj.data.uv_layers):
        obj.data.uv_layers.remove(layer)
    obj.data.uv_layers.new(name="UVMap")
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.002, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(rotate=True, margin=0.003)
    bpy.ops.object.mode_set(mode="OBJECT")


def source_socket(material, name: str):
    """The node output feeding a Principled input, or its default value."""
    principled = next((n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if principled is None:
        return None, (0.5, 0.5, 0.5, 1.0)
    socket = principled.inputs[name]
    if socket.is_linked:
        return socket.links[0].from_socket, None
    value = socket.default_value
    return None, tuple(value) if hasattr(value, "__len__") else (value, value, value, 1.0)


def emit_channel(material, channel: str) -> None:
    """Rewires a source material so its emission shows one channel, for an EMIT bake."""
    inputs = {"albedo": "Base Color", "roughness": "Roughness", "metal": "Metallic"}
    tree = material.node_tree
    output = next(n for n in tree.nodes if n.type == "OUTPUT_MATERIAL")
    emit = tree.nodes.get("TripoEmit") or tree.nodes.new("ShaderNodeEmission")
    emit.name = "TripoEmit"
    socket, value = source_socket(material, inputs[channel])
    for link in list(emit.inputs["Color"].links):
        tree.links.remove(link)
    if socket is not None:
        tree.links.new(socket, emit.inputs["Color"])
    else:
        emit.inputs["Color"].default_value = value
    tree.links.new(emit.outputs[0], output.inputs["Surface"])


def restore_surface(material) -> None:
    tree = material.node_tree
    output = next(n for n in tree.nodes if n.type == "OUTPUT_MATERIAL")
    principled = next((n for n in tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if principled is not None:
        tree.links.new(principled.outputs[0], output.inputs["Surface"])


def new_image(name: str, size: int, color: bool):
    image = bpy.data.images.new(name, size, size, alpha=False, float_buffer=not color)
    image.colorspace_settings.name = "sRGB" if color else "Non-Color"
    return image


def target_material(low, image):
    """The low mesh's bake target: an image node, active, in its only material."""
    mat = bpy.data.materials.get(BAKED) or bpy.data.materials.new(BAKED)
    mat.use_nodes = True
    low.data.materials.clear()
    low.data.materials.append(mat)
    node = mat.node_tree.nodes.get("Target") or mat.node_tree.nodes.new("ShaderNodeTexImage")
    node.name = "Target"
    node.image = image
    mat.node_tree.nodes.active = node
    return mat


def bake_one(high, low, kind: str, reach: float) -> None:
    scene = bpy.context.scene
    bpy.ops.object.select_all(action="DESELECT")
    high.select_set(True)
    low.select_set(True)
    bpy.context.view_layer.objects.active = low
    settings = scene.render.bake
    settings.use_selected_to_active = True
    settings.cage_extrusion = reach
    settings.max_ray_distance = reach * 2
    settings.margin = 8
    settings.margin_type = "EXTEND"
    settings.normal_space = "TANGENT"
    bpy.ops.object.bake(type=kind)


def pixels(image) -> numpy.ndarray:
    data = numpy.empty(len(image.pixels), dtype=numpy.float32)
    image.pixels.foreach_get(data)
    return data.reshape(image.size[1], image.size[0], 4)


def save_png(image, path: str, data: numpy.ndarray | None = None) -> None:
    out = bpy.data.images.new(os.path.basename(path), image.size[0], image.size[1], alpha=False)
    out.colorspace_settings.name = image.colorspace_settings.name
    out.pixels.foreach_set((pixels(image) if data is None else data).ravel())
    out.filepath_raw = path
    out.file_format = "PNG"
    out.save()


def bake_maps(high, low, name: str, folder: str, size: int, samples: int) -> dict:
    """Albedo, tangent normal and ORM (R occlusion, G roughness, B metal) PNGs; returns their paths."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.world = scene.world or bpy.data.worlds.new("BakeWorld")
    lo, hi = world_bounds(low)
    reach = max((hi - lo).length * 0.01, 0.005)
    os.makedirs(folder, exist_ok=True)
    paths = {key: os.path.join(folder, f"{name}_{key}.png") for key in ("albedo", "normal", "orm")}
    orm = numpy.ones((size, size, 4), dtype=numpy.float32)
    for channel in CHANNELS:
        image = new_image(f"{name}_{channel}", size, channel == "albedo")
        target_material(low, image)
        for mat in filter(None, high.data.materials):
            emit_channel(mat, channel)
        bake_one(high, low, "EMIT", reach)
        if channel == "albedo":
            save_png(image, paths["albedo"])
        else:
            orm[:, :, 1 if channel == "roughness" else 2] = numpy.clip(pixels(image)[:, :, 0], 0.0, 1.0)
    for mat in filter(None, high.data.materials):
        restore_surface(mat)
    image = new_image(f"{name}_normal", size, False)
    target_material(low, image)
    bake_one(high, low, "NORMAL", reach)
    save_png(image, paths["normal"])
    image = new_image(f"{name}_ao", size, False)
    target_material(low, image)
    bake_one(high, low, "AO", reach)
    orm[:, :, 0] = pixels(image)[:, :, 0]
    save_png(new_image(f"{name}_orm_pack", size, False), paths["orm"], orm)
    return paths


def final_material(low, paths: dict) -> None:
    """One Principled `Baked` material the glTF exporter writes as albedo, normal and ORM textures."""
    mat = bpy.data.materials.get(BAKED)
    tree = mat.node_tree
    tree.nodes.clear()
    nodes, links = tree.nodes, tree.links
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    links.new(bsdf.outputs[0], out.inputs["Surface"])

    def texture(key: str, color: bool):
        node = nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(paths[key], check_existing=False)
        node.image.colorspace_settings.name = "sRGB" if color else "Non-Color"
        return node

    links.new(texture("albedo", True).outputs["Color"], bsdf.inputs["Base Color"])
    normal_map = nodes.new("ShaderNodeNormalMap")
    links.new(texture("normal", False).outputs["Color"], normal_map.inputs["Color"])
    links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])
    split = nodes.new("ShaderNodeSeparateColor")
    links.new(texture("orm", False).outputs["Color"], split.inputs["Color"])
    links.new(split.outputs["Green"], bsdf.inputs["Roughness"])
    links.new(split.outputs["Blue"], bsdf.inputs["Metallic"])
    low.data.materials.clear()
    low.data.materials.append(mat)


def export(objects: list, path: str) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=path,
        use_selection=True,
        export_format="GLB",
        export_yup=True,
        export_apply=not any(obj.type == "MESH" and obj.data.shape_keys for obj in objects),
        export_image_format="JPEG",
        export_jpeg_quality=88,
    )


def run(args: argparse.Namespace) -> dict:
    """The whole intake; returns a summary for the report."""
    budget, size, default_height = KINDS[args.kind]
    high, armature = load_source(args.source)
    source_tris = triangle_count(high)
    placed = place_matrix(high, args.height or default_height or 1.0, args.yaw, args.length)
    low = make_low(high, budget)
    unwrap(low)
    folder = os.path.join(args.out, args.name)
    paths = bake_maps(high, low, args.name, folder, args.size or size, args.samples)
    final_material(low, paths)
    keep = [low]
    if args.kind == "character":
        low.data.materials[0].name = "Body" + BAKED
        keep = tripo_rig.rig(low, armature, placed, args.clips)
    elif args.kind == "zombie":
        low.data.materials[0].name = "Zombie" + BAKED
        low.name = "Body"
        keep = tripo_rig.rig(low, armature, placed, None)
        keep.append(tripo_rig.head_center_marker(keep[0], keep[2]))
        if args.name == "shambler":
            shambler_hand.add_reach(low, keep[0])
        if args.crawler:
            keep.append(tripo_crawler.make(keep[0], keep[1]))
    bpy.data.objects.remove(high)
    model = os.path.join(os.path.join(MODELS, args.folder) if args.folder else folder, f"{args.name}.glb")
    export(keep, model)
    strip_icc(model)
    return {"source_tris": source_tris, "tris": triangle_count(low), "model": model, **paths}


def parse(argv: list) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source")
    parser.add_argument("--kind", choices=sorted(KINDS), default="prop")
    parser.add_argument("--name", required=True)
    parser.add_argument("--height", type=float, default=0.0, help="metres; characters 1.80, zombies 1.70 by default")
    parser.add_argument("--length", type=float, default=0.0, help="metres for the longest side, instead of height")
    parser.add_argument("--yaw", type=float, default=0.0, help="degrees about up, to turn the front to Godot +Z")
    parser.add_argument("--size", type=int, default=0, help="map size; default 1024 props, 2048 characters")
    parser.add_argument("--samples", type=int, default=16)
    parser.add_argument("--out", default=OUT, help="folder for the baked maps (and the model without --folder)")
    parser.add_argument("--clips", choices=("player", "keeper"), default="player", help="characters: clip set")
    parser.add_argument("--folder", default="", help="write the model to assets/models/<folder>/")
    parser.add_argument("--crawler", action="store_true", help="zombies: cut the legs off and lay it prone")
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    print(run(parse(sys.argv[1:])))
