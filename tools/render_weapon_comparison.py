"""Render the four committed gun GLBs for review, without a display or GPU.

Uses the same Python 3.13 / bpy environment as tools/assets/build_models.py:
    python tools/render_weapon_comparison.py --out screenshots/weapons

CPU Cycles produces side.png and first_person.png, each with four labelled
panels. Side panels share an orthographic metre scale; first-person panels use
the game's 110-degree horizontal FOV and each weapon's content hip position.
These are asset inspection renders, rather than Godot gameplay screenshots.
"""

import argparse
import math
import os
import re
import struct
import tempfile
import zlib
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from weapon_preview_materials import gun_preview

REPO = Path(__file__).resolve().parents[1]
GUNS = (
    ("rifle_ar", "rifle_ar", "AR-17 / RIFLE"),
    ("shotgun_brenner", "brenner_trench", "BRENNER / SHOTGUN"),
    ("kestrel_smg", "kestrel_smg", "KESTREL / SMG"),
    ("talon_dmr", "talon_dmr", "TALON / DMR"),
)


def linear(hex_code):
    """Convert the look-rules sRGB palette to Blender's linear colours."""
    channels = [int(hex_code[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels)


def setup_scene(width, samples):
    """Identical CPU rendering, lighting and colour management for every panel."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.seed = 7
    scene.cycles.use_denoising = True
    scene.render.resolution_x = width
    scene.render.resolution_y = round(width * 9 / 16)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = math.log2(1.05)
    world = bpy.data.worlds.new("ColdContainment")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (*linear("#24363A"), 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.2
    scene.world = world
    area_light("Key", (1.2, -0.4, 1.4), 150, 1.4)
    area_light("Rim", (-0.9, 0.7, 0.6), 100, 1.0)
    area_light("ViewFill", (0.5, -1.0, 0.2), 35, 1.0)
    return scene


def area_light(name, at, energy, size):
    """Broad teal-white lights reveal bevels without hiding material values."""
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = linear("#CDEEE8")
    light = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(light)
    light.location = at
    light.rotation_euler = (Vector((0, 0.15, 0)) - light.location).to_track_quat("-Z", "Y").to_euler()


def import_gun(model_id, content_id, view):
    """Render the checked-in export, including the same part transforms Godot imports."""
    bpy.ops.import_scene.gltf(filepath=str(REPO / "assets/models/weapons" / f"{model_id}.glb"))
    imported = list(bpy.context.selected_objects)
    for material in {mat for obj in imported if obj.type == "MESH" for mat in obj.data.materials if mat}:
        gun_preview(material, model_id)
    triangles = sum(len(poly.vertices) - 2 for obj in imported if obj.type == "MESH" for poly in obj.data.polygons)
    if view == "first_person":
        content = (REPO / "content/weapons" / f"{content_id}.tres").read_text()
        values = re.search(r"^hip_position = Vector3\(([^)]+)\)", content, re.MULTILINE)
        if values is None:
            raise ValueError(f"{content_id} has no explicit hip_position")
        x, y, z = (float(value) for value in values.group(1).split(","))
        offset = Vector((x, -z, y))
        for obj in imported:
            if obj.parent is None:
                obj.location += offset
    return triangles


def camera_for(view):
    """Keep framing fixed so the compact SMG and long DMR remain comparable."""
    data = bpy.data.cameras.new("ComparisonCamera")
    camera = bpy.data.objects.new("ComparisonCamera", data)
    bpy.context.scene.collection.objects.link(camera)
    data.clip_start = 0.03
    data.clip_end = 20
    if view == "side":
        data.type = "ORTHO"
        data.ortho_scale = 1.65
        camera.location = (2, 0.20, 0.01)
        target = Vector((0, 0.20, 0.01))
    else:
        data.type = "PERSP"
        data.sensor_fit = "HORIZONTAL"
        data.angle = math.radians(110)
        camera.location = (0, 0, 0)
        target = Vector((0, 1, 0))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = camera
    return camera


def label(camera, title, subtitle):
    """Camera-facing text uses the bundled UI font and the look-rules text colour."""
    width = camera.data.ortho_scale if camera.data.type == "ORTHO" else 2 * math.tan(camera.data.angle / 2)
    height = width * 9 / 16
    font = bpy.data.fonts.load(str(REPO / "assets/fonts/AtkinsonHyperlegibleNext.ttf"))
    material = bpy.data.materials.new("Caption")
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = (*linear("#E8ECE6"), 1)
    shader.inputs["Emission Color"].default_value = (*linear("#E8ECE6"), 1)
    shader.inputs["Emission Strength"].default_value = 1
    for index, text in enumerate((title, subtitle)):
        curve = bpy.data.curves.new("Caption", "FONT")
        curve.body = text
        curve.font = font
        curve.size = width * (0.037 if index == 0 else 0.024)
        curve.materials.append(material)
        obj = bpy.data.objects.new("Caption", curve)
        bpy.context.scene.collection.objects.link(obj)
        obj.parent = camera
        obj.location = (-width * 0.46, height * (0.37 - index * 0.085), -1)
        obj.visible_shadow = False


def render_panel(gun, view, output, args):
    scene = setup_scene(args.width, args.samples)
    triangles = import_gun(gun[0], gun[1], view)
    camera = camera_for(view)
    scale = "1.65 m frame" if view == "side" else "110 deg HFOV / content hip pose"
    label(camera, gun[2], f"{triangles:,} triangles / {scale}")
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    print(f"rendered {gun[0]} {view}: {triangles} triangles", flush=True)


def combine_panels(paths, output):
    """Compose encoded PNG pixels without adding another imaging dependency."""
    panels = []
    for path in paths:
        image = bpy.data.images.load(str(path), check_existing=False)
        image.colorspace_settings.name = "Non-Color"
        width, height = image.size
        pixels = np.empty(width * height * 4, dtype=np.float32)
        image.pixels.foreach_get(pixels)
        panels.append(np.rint(pixels.reshape(height, width, 4)[::-1] * 255).astype(np.uint8))
        bpy.data.images.remove(image)
    pixels = np.concatenate(panels, axis=1)
    height, width, _ = pixels.shape
    scanlines = b"".join(b"\0" + row.tobytes() for row in pixels)
    with output.open("wb") as stream:
        stream.write(b"\x89PNG\r\n\x1a\n")
        for kind, data in (
            (b"IHDR", struct.pack(">2I5B", width, height, 8, 6, 0, 0, 0)),
            (b"IDAT", zlib.compress(scanlines)),
            (b"IEND", b""),
        ):
            stream.write(struct.pack(">I", len(data)) + kind + data)
            stream.write(struct.pack(">I", zlib.crc32(kind + data)))
    print(f"saved {output}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=REPO / "screenshots/weapons")
    parser.add_argument("--width", type=int, default=800, help="width of each 16:9 panel")
    parser.add_argument("--samples", type=int, default=48, help="CPU Cycles samples per pixel")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("OMP_NUM_THREADS", "8")
    with tempfile.TemporaryDirectory(prefix="weapon-comparison-") as directory:
        for view in ("side", "first_person"):
            paths = []
            for gun in GUNS:
                output = Path(directory) / f"{gun[0]}_{view}.png"
                render_panel(gun, view, output, args)
                paths.append(output)
            combine_panels(paths, args.out / f"{view}.png")


if __name__ == "__main__":
    main()
