"""Bake Halcyon's freight, institutional and maintenance finishes with Pillow and NumPy."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "assets/textures/halcyon"
TILE = 256
GRID = 8
# The slot order is the UV contract with the committed models.
ROWS = (
    "steel rubber enamel laminate olive wood paper alarm",
    "orange concrete vine linen cargo freight tailgate cab",
    "windshield headlight grille hub drum keyboard document file",
    "locker sign access cold case archive console dial",
    "burner tray cup meal drawer service foil conduit",
    "braid ceramic vinyl zipper grillelight pinboard tank deck",
    "leaf tag labels vent frost hatch brushed carbon",
    "rubbermat cargo_left menu rail tinted caution cassette log",
)
SLOTS = {name: i for i, name in enumerate(" ".join(ROWS).split())}
# Base sRGB, roughness and metalness. Dielectric paint only exposes metal at chips.
FINISHES = {
    "steel": ("89948e", 116, 185),
    "rubber": ("333a39", 205, 0),
    "enamel": ("667772", 153, 16),
    "laminate": ("a8afa7", 136, 0),
    "olive": ("546252", 177, 16),
    "wood": ("91755b", 209, 0),
    "paper": ("d1cebb", 228, 0),
    "alarm": ("994c41", 159, 16),
    "orange": ("c37b3f", 150, 20),
    "concrete": ("878985", 232, 0),
    "vine": ("495438", 159, 0),
    "linen": ("b6bbb0", 225, 0),
}
GROUPS = {
    "steel": "tailgate hub dial drawer foil deck brushed rail burner tank windshield tinted",
    "rubber": "keyboard console braid vinyl zipper grille grillelight carbon rubbermat cassette",
    "enamel": "access case locker vent hatch service archive cab",
    "olive": "cargo drum conduit cargo_left",
    "paper": "freight document file cup tag labels sign log",
    "laminate": "cold ceramic tray meal pinboard frost headlight",
    "vine": "leaf",
    "alarm": "menu",
    "orange": "caution",
}
FAMILY = {tile: family for family, tiles in GROUPS.items() for tile in tiles.split()}
CREAM, INK, PATINA, AMBER = "#dbd9c9", "#263333", "#52655d", "#c68b51"


def _material(name):
    return FAMILY.get(name, name)


def _noise(rng, size):
    import numpy as np
    from PIL import Image

    field = rng.integers(0, 255, (size, size), dtype=np.uint8)
    return np.asarray(Image.fromarray(field).resize((TILE, TILE), Image.Resampling.BICUBIC)).astype(float) / 255


def _surface(name, seed):
    import numpy as np

    family = _material(name)
    rng = np.random.default_rng(seed)
    rough, metal = FINISHES[family][1:]
    cloud, fine, pores = _noise(rng, 7), _noise(rng, 46), _noise(rng, TILE)
    y, x = np.indices((TILE, TILE))
    variation = 15 * (cloud - 0.5) + 9 * (fine - 0.5) + 6 * (pores - 0.5)
    if family == "wood":
        grain = np.sin(y * 1.2 + 5 * np.sin(x / 42) + cloud * 18)
        variation += 7 * grain + (y // 47 % 3 - 1) * 8
    if family in ("linen", "vine", "rubber"):
        variation += 3 * np.cos(x * 1.5 + fine) + 3 * np.sin(y * 1.7 + cloud)
    if family == "steel":
        variation += 9 * (_noise(rng, TILE)[:, :1] - 0.5)
    if family == "concrete":
        variation += 23 * (pores - 0.5)
    raw = np.array(list(bytes.fromhex(FINISHES[family][0])))
    rgb = raw + variation[:, :, None]
    return rgb, rough + 35 * (fine - 0.5), np.full_like(cloud, metal), fine


def _tile(name, index):
    import numpy as np
    from halcyon_graphics import decorate
    from PIL import Image

    base, rough, metal, fine = _surface(name, 2453 + index)
    art = Image.fromarray(np.uint8(np.clip(base, 0, 255)))
    decorate(art, name)
    rgb = np.asarray(art).astype(float)
    original = rgb.mean(axis=2)
    rng = np.random.default_rng(3457 + index)
    speck, cloud = _noise(rng, TILE), _noise(rng, 13)
    y, x = np.indices((TILE, TILE))
    if name in ("cargo", "cargo_left"):
        # Smoke from the burning cab climbs the forward edge on each side, clear of the rear doors.
        distance = x if name == "cargo" else 255 - x
        soot = np.clip((67 - distance - 0.15 * y + 26 * cloud + 19 * fine) / 65, 0, 1)
        rgb *= (1 - 0.83 * soot)[:, :, None]
        rough += soot * 24
    if name == "cab":
        soot = np.clip((90 - y + cloud * 70) / 135, 0, 0.8)
        rgb *= (1 - 0.67 * soot)[:, :, None]
    edge = np.minimum.reduce([x, y, 255 - x, 255 - y])
    family = _material(name)
    if family in ("steel", "olive", "enamel", "orange", "alarm"):
        wear = (edge < 11 + 9 * cloud) & (speck * 0.43 + fine > 0.83)
        rgb[wear] = np.where((speck[wear] > 0.5)[:, None], [151, 149, 131], [94, 69, 50])
        metal[wear] = 187
    # Surface grime runs over ink and exposed metal. Smooth broad marks survive mipmapping.
    rgb *= (0.91 + 0.13 * cloud + 0.08 * speck)[:, :, None]
    relief = (0.005 * original + fine * 0.58 + cloud) * (0.4 if family == "paper" else 1)
    dy, dx = np.gradient(relief)
    normal = np.stack([-dx, dy, np.ones_like(dx)], axis=-1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    orm = np.stack((250 - 12 * (1 - cloud), rough, metal), axis=-1)
    return [Image.fromarray(np.uint8(np.clip(a, 0, 255))) for a in (rgb, orm, 127.5 + 127.5 * normal)]


def vapor_sprite():
    """A feathered, asymmetric wisp for the level's smoke and steam billboards."""
    import numpy as np
    from PIL import Image

    rng = np.random.default_rng(1953)
    y, x = np.mgrid[-1 : 1 : complex(TILE), -1 : 1 : complex(TILE)]
    broad, wisps = _noise(rng, 7), _noise(rng, 21)
    radius = np.hypot(x * 1.07 + 0.12 * np.sin(4 * y), y * 1.11)
    rim = np.clip((1 - radius - 0.18 * (1 - broad)) / 0.65, 0, 1)
    opacity = rim**1.5 * (0.25 + 0.55 * broad + 0.2 * wisps)
    rgba = np.full((TILE, TILE, 4), 255, dtype=np.uint8)
    rgba[:, :, 3] = np.uint8(255 * opacity)
    Image.fromarray(rgba).save(DEST / "vapor_wisp.png", optimize=True)


def generate():
    import numpy as np
    from PIL import Image

    vapor_sprite()
    maps = [Image.new("RGB", (TILE * GRID, TILE * GRID)) for _ in range(3)]
    for name, i in SLOTS.items():
        for atlas, tile in zip(maps, _tile(name, i), strict=True):
            atlas.paste(tile, (i % GRID * TILE, i // GRID * TILE))
    for atlas, channel in zip(maps, ("albedo", "orm", "normal"), strict=True):
        # Keep full resolution for small type. The smoother relief and sheen need half as many texels per axis.
        output = atlas if channel == "albedo" else atlas.resize((1024, 1024), Image.Resampling.LANCZOS)
        if channel == "normal":
            vectors = np.asarray(output).astype(float) / 127.5 - 1
            vectors /= np.linalg.norm(vectors, axis=2, keepdims=True).clip(1e-5)
            output = Image.fromarray(np.uint8(np.clip(127.5 * (vectors + 1), 0, 255)))
        output.save(DEST / f"facility_{channel}.png", compress_level=9)
    # One compact reference for standalone Blender / glTF viewers. Godot shares the full PBR maps.
    maps[0].resize((1024, 1024), Image.Resampling.LANCZOS).save(
        DEST / "facility_preview.jpg", quality=78, optimize=True
    )


if __name__ == "__main__":
    generate()
