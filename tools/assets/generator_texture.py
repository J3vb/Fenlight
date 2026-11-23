"""Paint the Halcyon diesel generator's UV atlas. Run this file to regenerate its three PBR maps."""

from pathlib import Path

SLOTS = (
    "paint",
    "steel",
    "iron",
    "head",
    "engine",
    "service",
    "radiator",
    "grille",
    "panel",
    "gauge",
    "edge",
    "endbell",
    "skid",
    "rocker",
    "cabinet",
)
SIZE = 256
ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "assets/textures/halcyon"
FONT = ROOT / "assets/fonts/AtkinsonHyperlegibleNext.ttf"
CREAM, AMBER, INK = "#e3deba", "#d8a34f", "#242d2d"


def _letter(draw, xy, words, size, color):
    from PIL import ImageFont

    draw.text(xy, words, fill=color, font=ImageFont.truetype(str(FONT), size))


def _head(d):
    d.rectangle((4, 43, 252, 193), fill="#455954")
    d.rectangle((5, 48, 11, 185), fill=AMBER)
    # The long cast head projects to a square tile. Condense the stencil here so it
    # regains normal proportions when the label spans the 1.9 m by 0.35 m front.
    from PIL import Image, ImageDraw

    stencil = Image.new("L", (600, 110))
    _letter(ImageDraw.Draw(stencil), (0, -9), "ORIEL   /   DG-4", 80, 255)
    d.bitmap((21, 64), stencil.resize((155, 115), Image.Resampling.LANCZOS), fill=CREAM)


def _engine(d):
    _letter(d, (21, 36), "AUXILIARY", 26, CREAM)
    _letter(d, (20, 65), "DIESEL", 40, CREAM)
    d.rectangle((20, 123, 226, 128), fill=AMBER)


def _service(d):
    d.rounded_rectangle((17, 13, 238, 242), 8, outline="#3f514b", width=4)
    for y in range(69, 176, 19):
        d.rounded_rectangle((37, y, 218, y + 8), 4, fill=INK)
        d.line((42, y + 9, 210, y + 9), fill="#bcc2a6", width=2)


def _radiator(d):
    d.rectangle((30, 25, 224, 126), fill="#465b53")
    # Electrical warning on the narrow radiator side.
    d.polygon(((128, 47), (207, 101), (49, 101)), fill=AMBER)
    d.polygon(((136, 63), (106, 81), (128, 81), (118, 94), (151, 76), (130, 76)), fill=INK)
    d.rectangle((30, 115, 224, 126), fill=AMBER)
    for y in range(149, 231, 14):
        d.rounded_rectangle((33, y, 220, y + 6), 3, fill=INK)


def _grille(d):
    d.rectangle((11, 11, 244, 244), fill="#1e2828")
    for y in range(16, 241, 10):
        for x in range(15 + y % 3, 241, 10):
            d.ellipse((x, y, x + 5, y + 5), fill="#556361")


def _panel(d):
    d.rectangle((8, 9, 246, 245), outline="#919a8a", width=3)
    _letter(d, (22, 99), "V       Hz      bar", 23, CREAM)
    d.rectangle((23, 145, 228, 153), fill=AMBER)
    _letter(d, (23, 163), "AUX   /   POWER", 23, CREAM)
    for x in (40, 82, 124):
        d.ellipse((x, 214, x + 12, 226), fill=AMBER)


def _gauge(d):
    import math

    d.ellipse((7, 7, 249, 249), fill="#384440")
    d.ellipse((20, 20, 236, 236), fill=CREAM, outline=INK, width=5)
    for i in range(13):
        a = math.radians(145 + i * 21)
        d.line([(128 + r * math.cos(a), 128 + r * math.sin(a)) for r in (77, 96)], fill=INK, width=5)
    d.line((128, 128, 171, 62), fill="#923e29", width=8)
    d.ellipse((119, 119, 137, 137), fill=INK)


def _edge(d):
    for x in (8, 22, 36, 197, 211, 225):
        d.polygon(((x, 35), (x + 8, 35), (x + 16, 216), (x + 8, 216)), fill=AMBER)


def _endbell(d):
    for radius in (88, 70, 52):
        d.ellipse((128 - radius, 128 - radius, 128 + radius, 128 + radius), outline="#63706b", width=4)


def _skid(d):
    for y in range(8, 252, 23):
        for x in range(5 + y % 17, 250, 30):
            d.line((x, y + 5, x + 9, y - 3), fill="#656e69", width=3)


PAINTERS = {
    "head": _head,
    "engine": _engine,
    "service": _service,
    "radiator": _radiator,
    "grille": _grille,
    "panel": _panel,
    "gauge": _gauge,
    "edge": _edge,
    "endbell": _endbell,
    "skid": _skid,
}


def _print(tile, name):
    from PIL import ImageDraw

    d = ImageDraw.Draw(tile)
    paint = PAINTERS.get(name)
    if paint:
        paint(d)
    if name in ("panel", "service", "radiator", "cabinet", "rocker"):
        for x in (19, 237):
            for y in (18, 238):
                d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=INK)
                d.line((x - 2, y + 2, x + 2, y - 2), fill="#97a098", width=2)


def _tile(name, index):
    import numpy as np
    from PIL import Image

    rng = np.random.default_rng(4190 + index)

    def noise(res):
        arr = rng.integers(0, 256, (res, res), dtype=np.uint8)
        return np.asarray(Image.fromarray(arr).resize((SIZE, SIZE), Image.Resampling.BICUBIC), dtype=float) / 255

    painted = name in ("paint", "head", "engine", "service", "radiator", "rocker", "cabinet")
    bright = name in ("steel", "endbell")
    base = (134, 152, 134) if painted else (148, 157, 155) if bright else (62, 71, 69)
    tile = Image.new("RGB", (SIZE, SIZE), base)
    _print(tile, name)
    color = np.asarray(tile, dtype=float).copy()
    broad, grain, fleck = noise(6), noise(53), noise(256)
    y, x = np.mgrid[:SIZE, :SIZE]
    edge = np.minimum.reduce((x, y, 255 - x, 255 - y))
    wear = (edge < 3 + 15 * broad) & (grain + fleck * 0.47 > 0.86)
    scratches = (np.sin(x * 0.16 + y * 1.3 + 4 * broad) > 0.95) & (grain > 0.67)
    if name == "gauge":
        wear &= edge < 6
        scratches[:] = False
    color *= (0.84 + 0.24 * broad + 0.08 * grain + 0.08 * fleck)[:, :, None]
    color[wear] = np.where((grain[wear] > 0.70)[:, None], [155, 158, 146], [112, 76, 52])
    color[scratches] = color[scratches] * 0.68 + 0.32 * np.array([180, 177, 153])
    metallic = np.full_like(broad, 65 if painted else 187 if bright else 107)
    metallic[wear] = 202
    rough = (165 if painted else 119 if bright else 180) + 52 * (grain - 0.5) + 27 * (broad - 0.5)
    rough[wear] = 180
    orm = np.stack((np.full_like(broad, 255), rough, metallic), axis=-1)
    relief = 1.8 * broad + 0.4 * grain - 0.65 * wear + 0.009 * color.mean(axis=2)
    dy, dx = np.gradient(relief)
    normal = np.stack((-dx, dy, np.ones_like(dx)), axis=-1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    return [Image.fromarray(np.clip(a, 0, 255).astype("uint8")) for a in (color, orm, (normal + 1) * 127.5)]


def generate():
    from PIL import Image

    maps = [Image.new("RGB", (4 * SIZE, 4 * SIZE)) for _ in range(3)]
    for i, name in enumerate(SLOTS):
        for atlas, tile in zip(maps, _tile(name, i), strict=True):
            atlas.paste(tile, (i % 4 * SIZE, i // 4 * SIZE))
    for atlas, channel in zip(maps, ("albedo", "orm", "normal"), strict=True):
        atlas.save(DEST / f"generator_{channel}.png")


if __name__ == "__main__":
    generate()
