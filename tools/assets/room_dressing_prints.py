"""Paint the sixteen surface prints used by the Halcyon room dressing scene."""

import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FONT = Path(__file__).parent / "fonts/BebasNeue-Regular.ttf"
TILE = 256
PAPER, INK, TEAL, GOLD = "#dfdbbc", "#293832", "#4e756e", "#d7a65e"


def text(draw, x, y, value, height, color=PAPER):
    draw.text((x, y), value, fill=color, font=ImageFont.truetype(str(FONT), height), anchor="lt")


def panel(draw, color):
    draw.rounded_rectangle((4, 4, 251, 251), radius=6, fill=color, outline="#8b9890", width=3)
    for x in (14, 242):
        for y in (14, 242):
            draw.ellipse((x - 3, y - 3, x + 3, y + 3), fill="#b5b7a4", outline=INK)
            draw.line((x - 2, y + 1, x + 2, y - 1), fill=INK)


def freight(draw):
    text(draw, 12, 12, "ORIEL    /    FREIGHT", 27)
    draw.line((12, 49, 237, 49), fill=PAPER, width=4)
    text(draw, 10, 62, "A1", 168)
    text(draw, 12, 212, "RECEIVING   •   04", 36, GOLD)


def keys(draw):
    panel(draw, "#56665a")
    text(draw, 24, 17, "KEY CONTROL   /   B", 32)
    for i in range(8):
        x, y = 40 + i % 4 * 58, 75 + i // 4 * 80
        draw.rectangle((x - 15, y - 13, x + 15, y + 1), fill=PAPER)
        text(draw, x - 8, y - 11, f"{i + 1:02}", 13, INK)
        draw.ellipse((x - 3, y + 9, x + 3, y + 15), fill=INK, outline="#c4cbc1")
        if i != 3:
            draw.ellipse((x - 6, y + 12, x + 6, y + 29), outline="#d5b576", width=3)
            draw.line((x, y + 29, x - 2, y + 51, x + 5, y + 51), fill=GOLD, width=4)
            draw.polygon(((x + 4, y + 20), (x + 12, y + 25), (x + 8, y + 43), (x + 1, y + 38)), fill="#c7c1a7")


def menu(draw):
    panel(draw, "#283a34")
    text(draw, 20, 19, "HALCYON   /   CANTEEN", 24, GOLD)
    text(draw, 18, 53, "NIGHT SERVICE", 50)
    for i, name in enumerate(("SOUP OF THE DAY", "POTATO HASH", "FILTER COFFEE")):
        y = 123 + i * 37
        draw.line((18, y - 6, 236, y - 6), fill=TEAL, width=2)
        text(draw, 22, y, name, 21)
        text(draw, 207, y, f"0{i + 1}", 21, GOLD)


def wayfinding(draw):
    text(draw, 14, 30, "RESEARCH   /   B WING", 31)
    draw.line((15, 76, 240, 76), fill=PAPER, width=3)
    draw.polygon(((11, 156), (56, 101), (56, 135), (78, 135), (78, 173), (56, 173), (56, 208)), fill=PAPER)
    text(draw, 85, 108, "LABS", 110)


def generator(draw):
    text(draw, 15, 21, "ORIEL     /     PLANT", 31)
    text(draw, 10, 72, "G-02", 135)
    draw.line((15, 191, 235, 191), fill=GOLD, width=8)
    text(draw, 16, 211, "GENERATOR HALL", 29)


def service(draw):
    panel(draw, "#657165")
    for y in range(37, 145, 12):
        draw.rounded_rectangle((33, y, 220, y + 7), 3, fill=INK)
        draw.line((35, y + 8, 217, y + 8), fill="#9ea395", width=2)
    draw.rectangle((25, 169, 230, 220), fill=GOLD)
    text(draw, 34, 181, "SERVICE  /  02", 37, INK)


def frost(draw):
    rng = random.Random(28)
    for _ in range(410):
        x, y = rng.gauss(128, 55), rng.gauss(127, 39)
        a, length = rng.choice(range(6)) * math.pi / 3, rng.uniform(4, 32)
        dx, dy = math.cos(a), math.sin(a)
        ice = (192, 221, 220, rng.randint(35, 202))
        draw.line((x, y, x + dx * length, y + dy * length), fill=ice, width=rng.choice((1, 2, 3)))
        for t in (0.32, 0.53, 0.72):
            for side in (-1, 1):
                bx, by = x + t * dx * length, y + t * dy * length
                draw.line(
                    (bx, by, bx + math.cos(a + side) * length / 4, by + math.sin(a + side) * length / 4), fill=ice
                )


def transfer(draw):
    for x, ex in ((10, 48), (245, 207)):
        for y, ey in ((12, 54), (242, 208)):
            draw.line((x, ey, x, y, ex, y), fill=GOLD, width=5)
    text(draw, 29, 65, "04", 110)
    text(draw, 29, 161, "TRANSFER", 46)
    draw.line((30, 205, 220, 205), fill=GOLD, width=3)


def tracks(draw, caster):
    rng = random.Random(5)
    for y in range(8, 249, 2 if caster else 9):
        curve = int(31 * math.sin((y - 50) / 96))
        for offset in (48, 161):
            x = offset + curve
            alpha = int(min(1, y / 32, (256 - y) / 40) * rng.randint(85, 195))
            if caster:
                draw.line((x, y, x + rng.randint(1, 3), y + 3), fill=(41, 48, 46, alpha), width=3)
                draw.line((x + 7, y, x + 7, y + 2), fill=(101, 106, 98, alpha // 2), width=2)
            else:
                for dx, skew in ((0, 4), (10, -4)):
                    draw.polygon(
                        ((x + dx, y), (x + dx + 8, y + skew), (x + dx + 8, y + skew + 4), (x + dx, y + 4)),
                        fill=(42, 40, 33, alpha),
                    )


def spill(draw):
    rng = random.Random(35)
    for x, y, rx, ry in ((113, 134, 80, 48), (162, 99, 46, 24), (203, 78, 12, 6), (216, 66, 6, 4)):
        pts = []
        for i in range(55):
            a = i * math.tau / 55
            r = rng.uniform(0.91, 1.05) + 0.09 * math.sin(5 * a)
            pts.append((x + rx * r * math.cos(a), y + ry * r * math.sin(a)))
        draw.polygon(pts, fill=(49, 43, 30, 205))
        draw.line(pts[9:21], fill=(130, 119, 88, 154), width=2)


def log_sheet(draw):
    panel(draw, PAPER)
    draw.rectangle((18, 17, 237, 62), fill=TEAL)
    text(draw, 25, 29, "ORIEL   /   SHIFT RECORD", 23)
    text(draw, 23, 77, "TEMPERATURE LOG", 29, INK)
    for i in range(7):
        y = 113 + i * 16
        draw.line((21, y, 234, y), fill="#969782")
        if i < 5:
            text(draw, 25, y + 3, f"0{i + 1}     /     -04 C", 11, INK)
            draw.line((172, y + 11, 180, y + 4, 177, y + 12, 198, y + 7), fill=TEAL, width=1)


def descent(draw):
    panel(draw, "#3d534e")
    text(draw, 19, 21, "B   /   LOWER LEVEL", 30)
    draw.polygon(
        ((40, 87), (102, 146), (102, 110), (124, 109), (124, 185), (49, 185), (49, 163), (85, 163), (25, 103)),
        fill=GOLD,
    )
    text(draw, 138, 97, "B3", 87)
    text(draw, 20, 210, "CONTAINMENT", 32)


def patch(draw):
    panel(draw, "#78817c")
    rng = random.Random(71)
    for _ in range(65):
        x, y = rng.randint(8, 210), rng.randint(12, 241)
        draw.line(
            (x, y, min(x + rng.randint(4, 55), 248), y - rng.choice((0, 1, 2))), fill=rng.choice(("#8d958d", "#616e69"))
        )
    text(draw, 30, 33, "INSPECTED", 22, INK)
    draw.line((170, 190, 182, 202, 217, 157), fill=PAPER, width=4)


def curtain(draw):
    for x in range(5, 251):
        wave = math.sin(x * 0.16 + 0.5 * math.sin(x * 0.055))
        lower = 219 + 8 * math.sin(x * 0.12) - 85 * math.exp(-abs(x - 173) / 9)
        color = int(134 + 22 * wave)
        draw.line((x, 9 + 4 * wave, x, int(lower)), fill=(color - 15, color + 11, color + 5, 169))
        draw.point((x, lower - 5), fill=(124, 151, 136, 220))
    for x in range(15, 244, 32):
        draw.ellipse((x - 3, 14, x + 3, 20), fill=INK, outline=PAPER)


def drain(draw):
    panel(draw, "#4c5550")
    for x in range(21, 240, 10):
        draw.rounded_rectangle((x, 36, x + 5, 218), 2, fill="#202a29")
        draw.line((x + 6, 39, x + 6, 214), fill="#90988b")


def build():
    atlas = Image.new("RGBA", (4 * TILE, 4 * TILE))
    prints = (
        freight,
        keys,
        menu,
        wayfinding,
        generator,
        service,
        frost,
        transfer,
        lambda d: tracks(d, False),
        lambda d: tracks(d, True),
        spill,
        log_sheet,
        descent,
        patch,
        curtain,
        drain,
    )
    rng = np.random.default_rng(681)
    for index, paint in enumerate(prints):
        tile = Image.new("RGBA", (TILE, TILE))
        paint(ImageDraw.Draw(tile))
        pixels = np.asarray(tile).copy()
        grain = rng.normal(0, 4.8, (TILE, TILE, 1))
        pixels[:, :, :3] = np.clip(pixels[:, :, :3] + grain, 0, 255)
        pixels[:, :, 3][rng.random((TILE, TILE)) < 0.019] //= 3
        pixels[pixels[:, :, 3] == 0] = 0
        atlas.paste(Image.fromarray(pixels), (index % 4 * TILE, index // 4 * TILE))
    atlas.save(ROOT / "assets/textures/story/dressing_prints.png", optimize=True)


if __name__ == "__main__":
    build()
