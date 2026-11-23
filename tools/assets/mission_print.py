"""Print atlas for the Cordon liaison's route chart, field reports and survey photographs."""

import math
from pathlib import Path

ATLAS = Path(__file__).resolve().parents[2] / "assets/textures/signs/cordon_print.png"

SIZE = (1024, 512)
CHART = (4, 4, 628, 508)
REPORT = (640, 8, 820, 240)
PHOTOS = ((832, 8, 1018, 162), (832, 174, 1018, 328), (832, 340, 1018, 494))
PAPER, INK, MOSS, RUST = "#d8d2c0", "#303d3b", "#8c9984", "#a14532"


def chart_art():
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (624, 504), PAPER)
    draw = ImageDraw.Draw(image)
    draw.rectangle((16, 68, 607, 448), fill="#bcc1a9")
    # Survey contours around two ridges, clipped at the neatline of the chart.
    terrain = image.crop((16, 68, 608, 449))
    relief = ImageDraw.Draw(terrain)
    for cx, cy in ((85, 95), (470, 320)):
        for ring in range(17, 0, -1):
            points = []
            for step in range(97):
                a = step * math.tau / 96
                r = ring * (10 + 1.5 * math.sin(3 * a) + 1.2 * math.cos(5 * a))
                points.append((cx + 1.38 * r * math.cos(a), cy + r * math.sin(a)))
            relief.polygon(points, fill=MOSS if ring < 9 else None, outline="#7e8a78", width=2)
    image.paste(terrain, (16, 68))
    for x in range(38, 605, 64):
        draw.line((x, 68, x, 448), fill="#a4ad99")
    for y in range(92, 445, 64):
        draw.line((16, y, 607, y), fill="#a4ad99")
    route = [(57, 386), (112, 338), (194, 351), (273, 297), (298, 244), (382, 218), (427, 157), (535, 114)]
    draw.line(route, fill=PAPER, width=12)
    draw.line(route, fill=RUST, width=6)
    for x, y in route[::2] + route[-1:]:
        draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=PAPER, outline=RUST, width=4)
    draw.rectangle((16, 14, 608, 58), fill=INK)
    draw.text((27, 20), "CORDON   /   FIELD SURVEY", fill=PAPER, font_size=27)
    draw.text((20, 459), "LANTERN POST", fill=INK, font_size=22)
    draw.text((443, 459), "SECTOR   01", fill=INK, font_size=22)
    return image


def draw_atlas():
    from PIL import Image, ImageDraw

    atlas = Image.new("RGB", SIZE, PAPER)
    atlas.paste(chart_art(), CHART[:2])
    draw = ImageDraw.Draw(atlas)
    draw.rectangle((653, 36, 806, 62), fill=INK)
    draw.text((660, 38), "FIELD REPORT", fill=PAPER, font_size=18)
    for row, width in enumerate((140, 115, 133, 87, 141, 126)):
        y = 83 + row * 19
        draw.rectangle((656, y, 656 + width, y + 3), fill=MOSS)
    draw.rectangle((745, 206, 805, 225), outline=RUST, width=3)
    for i, (x, y, right, _) in enumerate(PHOTOS):
        draw.rectangle((x + 9, y + 9, right - 9, y + 120), fill="#a6b4ad")
        ridge = [(x + 9 + k * 14, y + 58 + 15 * math.sin(k * 0.69 + i)) for k in range(13)]
        draw.polygon([*ridge, (right - 9, y + 120), (x + 9, y + 120)], fill="#60746f")
        for k in range(7):
            px = x + 22 + k * 23
            top = y + 49 + int(18 * math.sin(k * 2.3 + i))
            draw.polygon([(px, top), (px - 10, y + 120), (px + 10, y + 120)], fill=INK)
        if i == 1:
            draw.rectangle((x + 65, y + 36, x + 114, y + 54), fill=INK)
            draw.polygon([(x + 55, y + 36), (x + 90, y + 19), (x + 125, y + 36)], fill=INK)
            for dx, foot in ((70, 60), (108, 120)):
                draw.line((x + dx, y + 50, x + foot, y + 119), fill=INK, width=5)
            draw.line((x + 70, y + 52, x + 115, y + 104), fill=INK, width=3)
        elif i == 2:
            draw.rectangle((x + 69, y + 77, x + 149, y + 114), fill=INK)
            draw.polygon([(x + 59, y + 80), (x + 98, y + 52), (x + 130, y + 52), (x + 159, y + 80)], fill=PAPER)
            for dx in (80, 103, 126):
                draw.rectangle((x + dx, y + 87, x + dx + 9, y + 97), fill=PAPER)
        caption = ("RIDGE", "WATCHTOWER", "LODGE")[i]
        draw.text((x + 12, y + 126), f"0{i + 1}   /   {caption}", fill=INK, font_size=15)
    atlas.save(ATLAS)


def printed_material():
    import bpy
    from build_models import material

    image = bpy.data.images.load(str(ATLAS))
    image.pack()
    mat = material("CordonPrint", (1, 1, 1, 1), roughness=0.92)
    texture = mat.node_tree.nodes.new("ShaderNodeTexImage")
    texture.image = image
    mat.node_tree.links.new(texture.outputs["Color"], mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    return mat


def sheet(obj, size, region):
    """Project the atlas region in sheet-local coordinates before the board is joined."""
    uv = obj.data.uv_layers.active.data
    left, top, right, bottom = region
    for loop in obj.data.loops:
        coord = obj.data.vertices[loop.vertex_index].co
        u, v = coord.x / size[0] + 0.5, 0.5 - coord.z / size[2]
        uv[loop.index].uv = ((left + u * (right - left)) / SIZE[0], 1 - (top + v * (bottom - top)) / SIZE[1])


if __name__ == "__main__":
    draw_atlas()
