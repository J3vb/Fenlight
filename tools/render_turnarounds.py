"""Render a turnaround of every committed model and compare it with the last approved render.

Uses the bpy environment from tools/assets/requirements.txt, plus Pillow:
    python tools/render_turnarounds.py --out screenshots/turnarounds
    python tools/render_turnarounds.py --approve          # accept the current look
    python tools/render_turnarounds.py shambler bloater   # only some models

For each model it writes <out>/<category>__<name>.png: the turnaround (front,
3/4, side, back), the approved turnaround, a diff (changed pixels in bio-green)
and the style-guide reference for that category. <out>/summary.md lists what
changed. --fail-on-change exits 1 when a model looks different from its
approved render and the approved file was not updated.
"""

import argparse
import math
import os
import sys
import tempfile
from pathlib import Path

import bpy
from mathutils import Vector
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import turnarounds
from render_weapon_comparison import linear
from weapon_preview_materials import gun_preview

ELEVATION = math.radians(12)


def setup_scene(size, samples):
    """Fixed CPU Cycles camera and lights; the model turns, so lighting matches across views."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.seed = 7
    scene.cycles.use_denoising = True
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = math.log2(1.05)
    world = bpy.data.worlds.new("ColdContainment")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (*linear("#24363A"), 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.2
    scene.world = world
    for name, at, energy in (
        ("Key", (1.6, -2.0, 1.8), 260),
        ("Rim", (-1.6, 1.8, 1.2), 200),
        ("Fill", (-1.8, -1.6, 0.2), 70),
    ):
        add_light(name, at, energy)
    data = bpy.data.cameras.new("TurnaroundCamera")
    data.type = "ORTHO"
    data.ortho_scale = 1.1
    camera = bpy.data.objects.new("TurnaroundCamera", data)
    scene.collection.objects.link(camera)
    camera.location = (0, -5 * math.cos(ELEVATION), 5 * math.sin(ELEVATION))
    camera.rotation_euler = (-camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera
    return scene


def add_light(name, at, energy):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = 1.5
    data.color = linear("#CDEEE8")
    light = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(light)
    light.location = at
    light.rotation_euler = (-light.location).to_track_quat("-Z", "Y").to_euler()


def _gear_preview(material):
    """Preview gear.gdshader's Common palette and finish means with baked AO."""
    if material.name == "GearGlass":
        _glass_preview(material)
        return
    nodes, links = material.node_tree.nodes, material.node_tree.links
    original = nodes.get("Principled BSDF")
    base = original.inputs["Base Color"]
    if base.is_linked:
        multiply = base.links[0].from_node
        base = next(socket for socket in multiply.inputs if socket.name == "B" and socket.type == "RGBA")
    albedo = tuple(base.default_value[:3])
    metallic, roughness = {
        "GearPlate": (0.05, 0.64),
        "GearPolymer": (0, 0.72),
        "GearRubber": (0, 0.95),
        "GearLiquid": (0.15, 0.12),
    }[material.name]
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    surface = nodes.new("ShaderNodeBsdfPrincipled")
    surface.inputs["Metallic"].default_value = metallic
    surface.inputs["Roughness"].default_value = roughness
    colors = nodes.new("ShaderNodeVertexColor")
    colors.layer_name = "Color"
    mask = nodes.new("ShaderNodeMath")
    mask.operation = "LESS_THAN"
    mask.inputs[1].default_value = 0.5
    links.new(colors.outputs["Alpha"], mask.inputs[0])
    painted = nodes.new("ShaderNodeMixRGB")
    painted.inputs[1].default_value = (*albedo, 1)
    painted.inputs[2].default_value = (*linear("#D9D9D2"), 1)
    links.new(mask.outputs[0], painted.inputs[0])
    separate = nodes.new("ShaderNodeSeparateColor")
    links.new(colors.outputs["Color"], separate.inputs["Color"])
    ao = nodes.new("ShaderNodeMixRGB")
    ao.blend_type = "MULTIPLY"
    ao.inputs[0].default_value = 1
    links.new(painted.outputs["Color"], ao.inputs[1])
    links.new(separate.outputs["Red"], ao.inputs[2])
    links.new(ao.outputs["Color"], surface.inputs["Base Color"])
    links.new(surface.outputs["BSDF"], output.inputs["Surface"])


def _glass_preview(material):
    """Use the same clear face/strong rim alpha as the Godot optical pass."""
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    surface = nodes.new("ShaderNodeBsdfPrincipled")
    surface.inputs["Base Color"].default_value = (*linear("#CDEEE8"), 1)
    surface.inputs["Roughness"].default_value = 0.10
    surface.inputs["Specular IOR Level"].default_value = 0.65
    weight = nodes.new("ShaderNodeLayerWeight")
    rim = nodes.new("ShaderNodeMath")
    rim.operation = "POWER"
    rim.inputs[1].default_value = 4.0
    links.new(weight.outputs["Facing"], rim.inputs[0])
    alpha = nodes.new("ShaderNodeMapRange")
    alpha.inputs["To Min"].default_value = 0.12
    alpha.inputs["To Max"].default_value = 0.52
    links.new(rim.outputs[0], alpha.inputs["Value"])
    links.new(alpha.outputs[0], surface.inputs["Alpha"])
    links.new(surface.outputs["BSDF"], output.inputs["Surface"])


def preview_materials(path, meshes):
    materials = {mat for obj in meshes for mat in obj.data.materials if mat}
    if path.parent.name in ("weapons", "throwables"):
        for material in materials:
            gun_preview(material, path.stem)
    elif path.parent.name == "gear" and path.stem.startswith(("charm_", "implant_")):
        for material in materials:
            _gear_preview(material)


def import_model(path):
    """Import a .glb, centred on a turntable pivot and scaled so every view fits a 1 m frame."""
    bpy.ops.import_scene.gltf(filepath=str(path), disable_bone_shape=True)
    imported = list(bpy.context.selected_objects)
    for obj in imported:
        if obj.type == "ARMATURE" and obj.animation_data:
            obj.animation_data.action = None  # turnarounds show the rest pose, not the first clip
            for pbone in obj.pose.bones:
                pbone.matrix_basis.identity()
    pivot = bpy.data.objects.new("TurntablePivot", None)
    offset = bpy.data.objects.new("TurntableOffset", None)
    for empty in (pivot, offset):
        bpy.context.scene.collection.objects.link(empty)
    offset.parent = pivot
    for obj in imported:
        if obj.parent is None:
            obj.parent = offset
    bpy.context.view_layer.update()
    meshes = [obj for obj in imported if obj.type == "MESH"]
    preview_materials(path, meshes)
    corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    low = Vector(tuple(min(c[i] for c in corners) for i in range(3)))
    high = Vector(tuple(max(c[i] for c in corners) for i in range(3)))
    size = high - low
    scale = 1 / max(math.hypot(size.x, size.y), size.z)
    offset.location = -(low + high) / 2
    pivot.scale = (scale, scale, scale)
    triangles = sum(len(poly.vertices) - 2 for obj in meshes for poly in obj.data.polygons)
    return pivot, size, triangles


def render_model(path, directory, args):
    """Render the four views and return (strip image, size in metres, triangle count)."""
    scene = setup_scene(args.size, args.samples)
    root, size, triangles = import_model(path)
    panels = []
    for _caption, degrees in turnarounds.VIEWS:
        root.rotation_euler = (0, 0, math.radians(degrees))
        scene.render.filepath = str(Path(directory) / f"{path.stem}_{degrees}.png")
        bpy.ops.render.render(write_still=True)
        panels.append(Image.open(scene.render.filepath).convert("RGB"))
    strip = turnarounds.make_strip(panels, [caption for caption, _ in turnarounds.VIEWS])
    return strip, size, triangles


def review_model(category, name, path, directory, args):
    """Render one model, write its review sheet and return its summary row."""
    strip, size, triangles = render_model(path, directory, args)
    approved_file = turnarounds.approved_path(category, name)
    approved = Image.open(approved_file).convert("RGB") if approved_file.is_file() else None
    fraction, diff = turnarounds.compare(strip, approved)
    result = {
        "model": f"{category}/{name}",
        "status": turnarounds.status(fraction),
        "fraction": fraction,
        "triangles": triangles,
    }
    subtitle = (
        f"{size.x:.2f} x {size.y:.2f} x {size.z:.2f} m (width x length x height) / "
        f"{triangles:,} triangles / {result['status']}"
    )
    rows = [("CURRENT", strip), ("APPROVED", approved), ("DIFF (changed pixels in green)", diff)]
    sheet = turnarounds.make_sheet(
        f"{category.upper()} / {name.upper()}", subtitle, rows, turnarounds.reference_for(category)
    )
    sheet.save(args.out / f"{category}__{name}.png")
    if args.approve and result["status"] != "same":
        approved_file.parent.mkdir(parents=True, exist_ok=True)
        strip.save(approved_file, optimize=True)
        print(f"approved {approved_file.relative_to(turnarounds.REPO)}", flush=True)
    print(f"{result['model']}: {result['status']} {fraction}", flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("models", nargs="*", help="model names to render (default: all)")
    parser.add_argument("--out", type=Path, default=turnarounds.REPO / "screenshots/turnarounds")
    parser.add_argument("--size", type=int, default=256, help="pixels per square panel")
    parser.add_argument("--samples", type=int, default=32, help="CPU Cycles samples per pixel")
    parser.add_argument("--approve", action="store_true", help="save changed renders as approved")
    parser.add_argument("--fail-on-change", action="store_true", help="exit 1 if any model changed")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("OMP_NUM_THREADS", "8")
    models = [m for m in turnarounds.find_models() if not args.models or m[1] in args.models]
    if not models:
        parser.error("no matching models in assets/models")
    with tempfile.TemporaryDirectory(prefix="turnarounds-") as directory:
        results = [review_model(*model, directory, args) for model in models]
    summary = turnarounds.summary_table(results)
    (args.out / "summary.md").write_text(summary)
    print(summary, flush=True)
    if args.fail_on_change and not args.approve and any(r["status"] != "same" for r in results):
        print("Models changed or are new. Check the sheets, then run with --approve and commit.", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
