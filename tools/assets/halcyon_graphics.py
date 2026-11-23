"""Paint markings in the printable area of each 256 px Halcyon finish tile."""

import math
import random

from generator_texture import _letter
from halcyon_atlas import AMBER, CREAM, INK, PATINA


def rivets(d, x0=15, x1=241, ys=(18, 237)):
    for x in (x0, x1):
        for y in ys:
            d.ellipse((x - 3, y - 2, x + 3, y + 4), fill="#47534f")
            d.ellipse((x - 2, y - 3, x + 2, y + 1), fill="#a8afa1")


def stencil(d, x, y, word, size, ink=INK):
    _letter(d, (x, y), word, size, ink)


def bars(d, x, y, width, height):
    rng = random.Random(57)
    end = x + width
    while x + 5 < end:
        w = rng.choice((1, 2, 2, 3, 4))
        d.rectangle((x, y, x + w, y + height), fill=INK)
        x += w + rng.choice((2, 3, 4))


def wood(d):
    rng = random.Random(51)
    for y in (48, 96, 144, 192, 240):
        d.line((4, y, 253, y - 1), fill="#574838", width=3)
        d.line((5, y + 2, 251, y + 1), fill="#ad9575", width=2)
        for x in (17, 237):
            d.ellipse((x - 2, y - 9, x + 2, y - 5), fill="#504b3c")
    for _ in range(70):
        x, y = rng.randint(0, 240), rng.randint(8, 246)
        d.line((x, y, x + rng.randint(7, 50), y + rng.choice((-1, 0, 1))), fill=rng.choice(("#857058", "#a48c6e")))
    for x, y in ((64, 80), (186, 170)):
        for w in (24, 16, 8):
            d.arc((x - w, y - w // 5, x + w, y + w // 5), 0, 335, fill="#74604d", width=1)


def cargo(d):
    for x in (12, 62, 112, 162, 212, 244):
        d.line((x, 8, x, 246), fill="#414d42", width=2)
        rivets(d, x, x, (20, 72, 208, 236))
    d.rectangle((8, 86, 248, 165), fill="#657669")
    d.rectangle((8, 161, 248, 168), fill=AMBER)
    stencil(d, 55, 87, "ORIEL", 42, CREAM)
    stencil(d, 59, 134, "FACILITY   TRANSPORT", 15, CREAM)
    stencil(d, 182, 205, "HL / 04", 14, CREAM)


def freight(d):
    d.rectangle((12, 15, 244, 240), outline=INK, width=5)
    d.rectangle((13, 19, 242, 80), fill=INK)
    stencil(d, 23, 21, "ORIEL   /   FREIGHT", 24, CREAM)
    stencil(d, 22, 85, "DOCK  04", 36)
    bars(d, 24, 150, 144, 52)
    for x in (190, 218):
        d.polygon(
            ((x, 151), (x - 10, 172), (x - 4, 172), (x - 4, 194), (x + 4, 194), (x + 4, 172), (x + 10, 172)), fill=INK
        )
    stencil(d, 24, 207, "HL   /   RECEIVING", 13)


def rear(d):
    d.line((128, 8, 128, 248), fill=INK, width=5)
    for x in (48, 207):
        d.line((x, 17, x, 242), fill=INK, width=7)
        d.line((x - 1, 19, x - 1, 240), fill="#929d93", width=3)
        for y in (47, 171, 212):
            d.rectangle((x - 6, y, x + 6, y + 5), fill=PATINA)
    for x in (12, 136):
        d.rectangle((x, 210, x + 29, 218), fill=CREAM)
        d.rectangle((x + 30, 210, x + 58, 218), fill="#925241")
    rivets(d)


def window(d):
    d.rounded_rectangle((8, 8, 247, 247), radius=12, fill="#202c2e", outline="#667773", width=5)
    d.polygon(((19, 21), (181, 21), (76, 160), (17, 184)), fill="#394b4d")
    d.polygon(((17, 22), (101, 22), (16, 119)), fill="#4c6060")
    d.line((43, 223, 137, 190, 171, 174), fill="#151e1e", width=4)


def rings(d, kind):
    center = 128
    radii = (105, 92, 72, 50, 20) if kind == "burner" else (117, 105, 63, 48, 22)
    for i, r in enumerate(radii):
        d.ellipse((center - r, center - r, center + r, center + r), outline=(INK, PATINA)[i % 2], width=5)
    if kind == "hub":
        for k in range(8):
            a = k * math.pi / 4
            x, y = 128 + 64 * math.cos(a), 128 + 64 * math.sin(a)
            d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=INK)
    if kind == "headlight":
        for x in range(22, 236, 10):
            d.line((x, 25, x, 231), fill="#b2b9a9", width=3)


def slots(d, kind):
    x0, x1 = (40, 216) if kind == "locker" else (18, 238)
    top, bottom = (28, 69) if kind == "locker" else (25, 229)
    for y in range(top, bottom, 14):
        d.rounded_rectangle((x0, y, x1, y + 7), 3, fill=INK)
        d.line((x0 + 3, y + 8, x1 - 3, y + 8), fill="#9da79c")
    if kind == "locker":
        d.rectangle((99, 88, 156, 106), fill=CREAM)
        d.line((109, 98, 146, 98), fill=INK, width=2)
    rivets(d)


def paper(d, kind):
    heading = {"document": "INTAKE", "file": "RECORDS", "tag": "HOLD", "log": "SHIFT LOG", "labels": "ARCHIVE"}[kind]
    d.rectangle((14, 15, 242, 53), fill=PATINA)
    stencil(d, 21, 16, "ORIEL   /   " + heading, 21, CREAM)
    stencil(d, 19, 66, heading, 29)
    for index, y in enumerate(range(120, 186, 13)):
        d.line((21, y, (212, 173, 225)[index % 3], y), fill="#82877c", width=2)
    bars(d, 23, 198, 106, 27)
    d.rectangle((162, 192, 229, 222), outline="#925241", width=2)
    stencil(d, 168, 194, "FILED", 16, "#925241")


def keyboard(d, kind):
    d.rounded_rectangle((8, 10, 247, 245), 9, fill="#46514e", outline=INK, width=4)
    cols = 11 if kind == "keyboard" else 4
    step = 220 // cols
    for row in range(4):
        for col in range(cols):
            x, y = 18 + step * col, 28 + 46 * row
            d.rounded_rectangle((x, y, x + step - 4, y + 33), 2, fill=INK)
            d.line((x + 3, y + 6, x + step // 2, y + 6), fill=CREAM, width=2)
    d.rectangle((67, 214, 177, 233), fill=INK)


def equipment(d, kind):
    title, id_text = {
        "access": ("ACCESS", "CONTROL"),
        "cold": ("COLD ROOM", "STORAGE"),
        "case": ("ORIEL", "FIELD SUPPLY"),
        "archive": ("ARCHIVE", "SAMPLE STORAGE"),
        "service": ("SERVICE", "ACCESS PANEL"),
        "hatch": ("ORIEL", "SAMPLE VAULT"),
        "menu": ("COLD", "DRINKS"),
        "caution": ("CAUTION", "RESTRICTED"),
        "cab": ("04", "TRANSPORT"),
        "sign": ("CAUTION", "AUTHORIZED ACCESS"),
    }[kind]
    ink = INK if kind in ("cold", "sign") else CREAM
    d.rounded_rectangle((12, 12, 243, 243), 6, outline=PATINA, width=3)
    d.rectangle((19, 157, 232, 163), fill=AMBER)
    stencil(d, 24, 86, title, 35, ink)
    stencil(d, 25, 169, id_text, 17, ink)
    rivets(d, 19, 235, (23, 232))


def bands(d, kind):
    if kind in ("drum", "tank"):
        for y in (43, 194):
            d.rectangle((0, y, 255, y + 11), fill=PATINA)
            d.line((0, y + 12, 255, y + 12), fill="#a4a99c", width=2)
        d.rectangle((74, 85, 185, 150), fill=CREAM)
        stencil(d, 81, 88, "ORIEL", 22)
        stencil(d, 81, 113, "RESERVE" if kind == "drum" else "VESSEL", 14)
    else:
        for x in (31, 44, 188, 201):
            d.rectangle((x, 0, x + 4, 255), fill=AMBER if kind == "conduit" else PATINA)


def woven(d, kind):
    if kind == "linen":
        for y in (20, 27, 226):
            d.line((0, y, 255, y), fill="#77908a", width=2)
    elif kind in ("braid", "zipper"):
        for x in range(0, 256, 12):
            d.line((x, 0, x + 5, 255), fill="#45534e", width=3)
        d.rectangle((48, 0, 55, 255), fill=PATINA)
    else:
        for x in range(8, 250, 29):
            pts = [(x + 9 * math.sin(y / 45 + x), y) for y in range(0, 260, 8)]
            d.line(pts, fill="#65704b", width=2)
        if kind == "leaf":
            d.line((128, 255, 128, 0), fill="#89935e", width=4)
            for y in range(35, 240, 32):
                d.line((57, y - 31, 128, y, 206, y - 37), fill="#657647", width=3)


def plates(d, kind):
    if kind in ("tray", "meal"):
        for bounds in ((12, 12, 240, 240), (23, 24, 150, 223), (157, 24, 229, 114), (157, 121, 229, 223)):
            d.rounded_rectangle(bounds, radius=11, outline="#64746d", width=4)
    elif kind == "deck":
        for y in range(0, 256, 16):
            for x in range(y % 32, 256, 32):
                d.line((x, y + 8, x + 9, y), fill="#55635d", width=4)
    elif kind == "drawer":
        d.rectangle((68, 142, 189, 181), fill=INK)
        d.rectangle((73, 147, 184, 176), fill=CREAM)
        d.line((85, 161, 159, 161), fill=PATINA, width=2)
    else:
        for x in range(19, 246, 27):
            d.line((x, 13, x, 242), fill="#c0bfad", width=2)
        rivets(d)


def decorate(tile, name):
    from PIL import ImageDraw

    draw = ImageDraw.Draw(tile)
    simple = {
        "wood": wood,
        "cargo": cargo,
        "cargo_left": cargo,
        "freight": freight,
        "tailgate": rear,
        "windshield": window,
        "tinted": window,
    }
    groups = {
        rings: "hub burner headlight dial",
        slots: "grille grillelight locker vent",
        paper: "document file tag labels log",
        keyboard: "keyboard console cassette",
        equipment: "access cold case archive service hatch menu caution cab sign",
        bands: "tank drum conduit rail",
        woven: "linen leaf vine braid zipper",
        plates: "tray meal deck drawer foil",
    }
    if name in simple:
        simple[name](draw)
    for painter, names in groups.items():
        if name in names.split():
            painter(draw, name)
