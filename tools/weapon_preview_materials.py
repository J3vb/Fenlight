"""Blender inspection materials for the game's externally assigned weapon textures."""

from pathlib import Path

import bpy
from assets.gun_bake import Nodes

REPO = Path(__file__).resolve().parents[1]


def surface_grain(nodes, wood):
    """Use the same three projections and fourth-power normal weights as the Godot finish."""
    coords = nodes.n.new("ShaderNodeTexCoord")
    pos = nodes.node("ShaderNodeSeparateXYZ", Vector=coords.outputs["Object"]).outputs
    normal = nodes.node("ShaderNodeSeparateXYZ", Vector=coords.outputs["Normal"]).outputs
    forward = nodes.math("MULTIPLY", pos["Y"], (-0.23 if wood else -1) / 0.085)
    x, z = (nodes.math("DIVIDE", pos[axis], 0.085) for axis in ("X", "Z"))
    image = bpy.data.images.load(str(REPO / "assets/textures/weapons/surface_detail.png"), check_existing=True)
    image.colorspace_settings.name = "Non-Color"
    # Turn the glTF axis conversion back into Blender axes: side, top, end.
    samples, weights = [], []
    for u, v, axis in ((forward, z, "X"), (forward, x, "Z"), (x, z, "Y")):
        uv = nodes.node("ShaderNodeCombineXYZ", X=u, Y=v).outputs[0]
        texture = nodes.node("ShaderNodeTexImage", Vector=uv)
        texture.image = image
        samples.append(nodes.node("ShaderNodeSeparateColor", Color=texture.outputs["Color"]).outputs)
        square = nodes.math("MULTIPLY", normal[axis], normal[axis])
        weights.append(nodes.math("MULTIPLY", square, square))
    total = nodes.math("ADD", nodes.math("ADD", *weights[:2]), weights[2])

    def channel(name):
        parts = [nodes.math("MULTIPLY", sample[name], weight) for sample, weight in zip(samples, weights, strict=True)]
        return nodes.math("DIVIDE", nodes.math("ADD", nodes.math("ADD", *parts[:2]), parts[2]), total)

    return channel


def preview_relief(material, bsdf):
    """Shade studio renders with each finish's linear height channel and roughness response."""
    base = material.name.removesuffix("Worn").removesuffix("Knurled")
    wood = base == "Wood"
    steel = base in ("GunMetal", "Brass")
    coated = base in ("MatteBlack", "OliveCoat")
    if not (wood or steel or coated or base in ("Tan", "GreyPolymer", "OlivePolymer")):
        return
    nodes = Nodes(material)
    grain = surface_grain(nodes, wood)
    color = bsdf.inputs["Base Color"]
    albedo = color.links[0].from_socket if color.is_linked else tuple(color.default_value)
    if wood:
        height = grain("Blue")
        tint = nodes.mix((0.46, 0.34, 0.27, 1), (1.43, 1.28, 1.08, 1), height)
        response = nodes.math("MULTIPLY", nodes.math("SUBTRACT", 0.58, height), 0.38)
        depth = 0.00014
    elif steel:
        height = grain("Red")
        brush = nodes.math("SUBTRACT", height, 0.5)
        tint = nodes.math("ADD", 1.0, nodes.math("MULTIPLY", brush, 0.14))
        response = nodes.math("MULTIPLY", brush, 0.34)
        depth = 0.00005
    else:
        height = grain("Green")
        stipple = nodes.math("SUBTRACT", height, 0.62)
        if coated:
            rub = nodes.math("MULTIPLY", nodes.math("SUBTRACT", grain("Red"), 0.5), 0.24)
            tint = nodes.math("ADD", 1.0, rub)
            response = nodes.math("ADD", rub, nodes.math("MULTIPLY", stipple, 0.16))
            depth = 0.000075
        else:
            tint = nodes.math("ADD", 1.0, nodes.math("MULTIPLY", stipple, 0.18))
            response = nodes.math("MULTIPLY", stipple, 0.22)
            depth = 0.00018
    multiply = nodes.node("ShaderNodeMixRGB", Fac=1.0, Color1=albedo, Color2=tint)
    multiply.blend_type = "MULTIPLY"
    nodes.link(multiply.outputs[0], color)
    rough = bsdf.inputs["Roughness"]
    nodes.link(nodes.math("ADD", rough.default_value, response), rough)
    bump = nodes.node("ShaderNodeBump", Height=height, Distance=depth)
    nodes.link(bump.outputs["Normal"], bsdf.inputs["Normal"])


def gun_preview(material, model):
    """Bind the same external atlas and baked maps that Godot assigns at import."""
    nodes, links = material.node_tree.nodes, material.node_tree.links
    bsdf = nodes["Principled BSDF"]
    base = bsdf.inputs["Base Color"]
    if material.name in ("Markings", "FactoryPrint"):
        image = nodes.new("ShaderNodeTexImage")
        image.image = bpy.data.images.load(str(REPO / "assets/textures/gun_markings.png"), check_existing=True)
        uv = nodes.new("ShaderNodeUVMap")
        uv.uv_map = "UVMap.001"
        links.new(uv.outputs["UV"], image.inputs["Vector"])
        # Preserve the vertex AO multiplier set up by the glTF importer.
        if base.is_linked and base.links[0].from_node.type == "MIX":
            mix = base.links[0].from_node
            base = next(socket for socket in mix.inputs if socket.name == "B" and socket.type == "RGBA")
        links.new(image.outputs["Color"], base)
    elif material.name == "Baked":
        maps = {}
        for kind in ("albedo", "normal", "orm"):
            path = REPO / f"assets/textures/weapons/{model}_{kind}.png"
            image = nodes.new("ShaderNodeTexImage")
            image.image = bpy.data.images.load(str(path), check_existing=True)
            image.image.colorspace_settings.name = "sRGB" if kind == "albedo" else "Non-Color"
            maps[kind] = image.outputs["Color"]
        orm = nodes.new("ShaderNodeSeparateColor")
        links.new(maps["orm"], orm.inputs["Color"])
        links.new(orm.outputs["Green"], bsdf.inputs["Roughness"])
        links.new(orm.outputs["Blue"], bsdf.inputs["Metallic"])
        darken = nodes.new("ShaderNodeMixRGB")
        darken.blend_type = "MULTIPLY"
        darken.inputs[0].default_value = 1.0
        links.new(maps["albedo"], darken.inputs[1])
        links.new(orm.outputs["Red"], darken.inputs[2])
        links.new(darken.outputs[0], base)
        normal = nodes.new("ShaderNodeNormalMap")
        links.new(maps["normal"], normal.inputs["Color"])
        links.new(normal.outputs["Normal"], bsdf.inputs["Normal"])
    else:
        preview_relief(material, bsdf)
