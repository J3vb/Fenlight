"""Finishing pass run on every built model just before export.

1. Normals: smooth by angle (35 degrees) plus a weighted-normal modifier, so
   flat faces stay flat, bevels catch light and cylinder caps stay crisp.
2. UVs: smart UV project per mesh, so later textures and bakes have clean,
   non-overlapping islands.
3. Shading mask: ambient occlusion baked with Cycles into a vertex colour,
   multiplied by a cavity (concave curvature) term. Godot multiplies albedo by
   it, so creases and contact spots darken without extra textures or draw calls.
"""

import math

import bpy

# isort: split
# bpy must load before bmesh.
import bmesh
from mathutils import Vector

SMOOTH_ANGLE = math.radians(35.0)
AO_SAMPLES = 64
AO_REACH = 0.08  # AO distance as a share of the model's largest size
AO_STRENGTH = 0.8  # 0 = no darkening, 1 = full baked AO
CAVITY_STRENGTH = 0.5  # how much the deepest crease darkens
COLOR_NAME = "Color"


def meshes() -> list:
    return [o for o in bpy.context.scene.objects if o.type == "MESH"]


def _select_only(obj) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def _morph_sharp_edges(obj, target) -> None:
    """A crease in any authored shape needs its own split normal in every shape."""
    mesh = target.data
    neighbors = [[] for _edge in mesh.edges]
    for face in mesh.polygons:
        for loop in face.loop_indices:
            neighbors[mesh.loops[loop].edge_index].append(face.index)
    threshold = math.cos(SMOOTH_ANGLE)
    basis = [tuple(vertex.co) for vertex in mesh.vertices]
    for key in obj.data.shape_keys.key_blocks:
        for vertex, point in zip(mesh.vertices, key.data, strict=True):
            vertex.co = point.co
        mesh.update()
        for edge, faces in zip(mesh.edges, neighbors, strict=True):
            if len(faces) == 2 and mesh.polygons[faces[0]].normal.dot(mesh.polygons[faces[1]].normal) < threshold:
                edge.use_edge_sharp = True
    for source, edge in zip(obj.data.edges, mesh.edges, strict=True):
        source.use_edge_sharp = edge.use_edge_sharp
    for vertex, position in zip(mesh.vertices, basis, strict=True):
        vertex.co = position
    obj.data.update()
    mesh.update()


def fix_normals(obj) -> None:
    _select_only(obj)
    bpy.ops.object.shade_smooth_by_angle(angle=SMOOTH_ANGLE, keep_sharp_edges=True)
    target = obj
    if obj.data.shape_keys:
        target = obj.copy()
        target.data = obj.data.copy()
        bpy.context.collection.objects.link(target)
        target.shape_key_clear()
        for modifier in list(target.modifiers):
            target.modifiers.remove(modifier)
    try:
        if target is not obj:
            _morph_sharp_edges(obj, target)
        _select_only(target)
        mod = target.modifiers.new("Weighted", "WEIGHTED_NORMAL")
        mod.keep_sharp = True
        mod.weight = 50
        bpy.ops.object.modifier_apply(modifier=mod.name)
        if target is not obj:
            source = [tuple(face.vertices) for face in obj.data.polygons]
            finished = [tuple(face.vertices) for face in target.data.polygons]
            if source != finished or len(obj.data.vertices) != len(target.data.vertices):
                raise ValueError("normal finishing changed morph topology")
            obj.data.normals_split_custom_set([corner.vector for corner in target.data.corner_normals])
    finally:
        if target is not obj:
            mesh = target.data
            bpy.data.objects.remove(target, do_unlink=True)
            bpy.data.meshes.remove(mesh)
            _select_only(obj)


def unwrap(obj) -> None:
    """Smart-projects the first UV map. A second map (gun `Markings`) is authored and kept."""
    layers = obj.data.uv_layers
    if layers and layers[0].name == "PrintLayout":
        return  # Keep the atlas coordinates on printed sheets.
    if len(layers) > 1:
        layers.active_index = 0
    _select_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66.0), island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")


def _model_size(objs: list) -> float:
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    for obj in objs:
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            for i in range(3):
                lo[i] = min(lo[i], world[i])
                hi[i] = max(hi[i], world[i])
    return max(h - low for h, low in zip(hi, lo, strict=True))


def bake_ao(objs: list) -> None:
    """Bakes AO from all meshes (they shade each other) into each mesh's colour attribute."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = AO_SAMPLES
    scene.cycles.seed = 0
    if scene.world is None:
        scene.world = bpy.data.worlds.new("BakeWorld")
    scene.world.light_settings.distance = _model_size(objs) * AO_REACH
    saved_alpha = {}
    for obj in objs:
        mesh = obj.data
        attr = mesh.color_attributes.get(COLOR_NAME)
        if attr is not None:
            saved_alpha[obj] = [color.color[3] for color in attr.data]
        else:
            attr = mesh.color_attributes.new(COLOR_NAME, "FLOAT_COLOR", "CORNER")
        mesh.color_attributes.active_color = attr
        mesh.color_attributes.render_color_index = mesh.color_attributes.active_color_index
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objs:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    try:
        bpy.ops.object.bake(type="AO", target="VERTEX_COLORS")
    finally:
        for obj, alphas in saved_alpha.items():
            attr = obj.data.color_attributes[COLOR_NAME]
            for color, alpha in zip(attr.data, alphas, strict=True):
                color.color[3] = alpha


def cavity(mesh) -> list:
    """Per vertex 0..1: how deep a crease it sits in (0 = flat or convex edge)."""
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    out = [0.0] * len(bm.verts)
    for v in bm.verts:
        if not v.link_edges:
            continue
        bend = 0.0
        for e in v.link_edges:
            d = (e.other_vert(v).co - v.co).normalized()
            bend += d.dot(v.normal)
        out[v.index] = max(0.0, min(1.0, bend / len(v.link_edges) * 2.0))
    bm.free()
    return out


def _unshaded(obj) -> bool:
    for mat in obj.data.materials:
        if mat and mat.name in ("OpticGlass", "SightGlass"):
            continue
        bsdf = mat.node_tree.nodes.get("Principled BSDF") if mat and mat.node_tree else None
        if bsdf is None or bsdf.inputs["Emission Strength"].default_value <= 0.0:
            return False
    return bool(obj.data.materials)


def apply_mask(obj) -> None:
    """Softens baked AO/cavity; light sources and optical glass keep their full colour."""
    mesh = obj.data
    attr = mesh.color_attributes[COLOR_NAME]
    unshaded = _unshaded(obj)
    cav = cavity(mesh)
    for loop in mesh.loops:
        if unshaded:
            value = 1.0
        else:
            ao = attr.data[loop.index].color[0]
            value = (1.0 - AO_STRENGTH + AO_STRENGTH * ao) * (1.0 - CAVITY_STRENGTH * cav[loop.vertex_index])
        attr.data[loop.index].color = (value, value, value, attr.data[loop.index].color[3])


def finish() -> None:
    objs = meshes()
    for obj in objs:
        fix_normals(obj)
        unwrap(obj)
    bake_ao(objs)
    for obj in objs:
        apply_mask(obj)
