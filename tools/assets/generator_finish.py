"""Project the diesel set's named panels onto its painted and engraved atlas regions."""

import bpy
from generator_texture import DEST, SIZE, SLOTS


def _surface(part, axis, front):
    name = part.name
    if axis == 1 and front:
        for prefix, tile in (
            ("ServiceCover", "service"),
            ("ControlFace", "panel"),
            ("ControlBox", "cabinet"),
            ("Radiator", "radiator"),
            ("Head", "head"),
            ("Engine", "engine"),
        ):
            if name.startswith(prefix):
                return tile
    if name.startswith("Gauge") and axis == 2:
        return "gauge"
    if name == "Radiator" and axis == 0:
        return "grille"
    if name == "Skid":
        return "skid" if axis == 2 else "edge"
    if name == "EndBell" and axis == 0:
        return "endbell"
    if name.startswith("Rocker") and axis == 2:
        return "rocker"
    return {"Dark": "iron", "Steel": "steel", "Olive": "paint"}[part.data.materials[0].name]


def _project(part):
    mesh = part.data
    uv = mesh.uv_layers.active.data
    coords = [v.co for v in mesh.vertices]
    low = [min(v[k] for v in coords) for k in range(3)]
    span = [max(v[k] for v in coords) - low[k] for k in range(3)]
    for face in mesh.polygons:
        axis = max(range(3), key=lambda k: abs(face.normal[k]))
        front = face.normal[axis] < 0
        index = SLOTS.index(_surface(part, axis, front))
        h, v = ((1, 2), (0, 2), (0, 1))[axis]
        for loop in face.loop_indices:
            co = coords[mesh.loops[loop].vertex_index]
            u = (co[h] - low[h]) / span[h]
            if (axis == 0 and front) or (axis == 1 and not front):
                u = 1 - u
            t = (co[v] - low[v]) / span[v]
            # Keep bilinear samples inside their tile, including at oblique viewing angles.
            uv[loop].uv = (
                (index % 4 + (5 + u * (SIZE - 10)) / SIZE) / 4,
                1 - (index // 4 + (5 + (1 - t) * (SIZE - 10)) / SIZE) / 4,
            )


def apply():
    from build_models import material

    mat = material("GeneratorFinish", (1, 1, 1, 1))
    tree = mat.node_tree
    shader = tree.nodes["Principled BSDF"]
    textures = {}
    for kind in ("albedo", "orm", "normal"):
        node = tree.nodes.new("ShaderNodeTexImage")
        node.image = bpy.data.images.load(str(DEST / f"generator_{kind}.png"))
        if kind != "albedo":
            node.image.colorspace_settings.name = "Non-Color"
        node.image.pack()
        textures[kind] = node.outputs["Color"]
    tree.links.new(textures["albedo"], shader.inputs["Base Color"])
    split = tree.nodes.new("ShaderNodeSeparateColor")
    tree.links.new(textures["orm"], split.inputs["Color"])
    tree.links.new(split.outputs["Green"], shader.inputs["Roughness"])
    tree.links.new(split.outputs["Blue"], shader.inputs["Metallic"])
    normal = tree.nodes.new("ShaderNodeNormalMap")
    tree.links.new(textures["normal"], normal.inputs["Color"])
    tree.links.new(normal.outputs["Normal"], shader.inputs["Normal"])
    for part in bpy.context.scene.objects:
        if part.type == "MESH":
            _project(part)
            part.data.materials[0] = mat
