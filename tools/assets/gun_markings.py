"""Draws the gun markings atlas: Oriel logo, magazine tape, shell hull and brass.

One 1024 x 1024 PNG shared by the roster (docs/plans/guns-concept.md). The
`Markings` material samples it through the second UV map that `gun_parts.marking`
writes. Pure Python, no image library, so the output is the same on every machine.

    python tools/assets/gun_markings.py            # writes assets/textures/gun_markings.png
"""

import itertools
import math
import random
import struct
import sys
import zlib
from pathlib import Path

import gun_plates

SIZE = 256
OUT = Path(__file__).resolve().parents[2] / "assets" / "textures" / "gun_markings.png"

# Pixel rectangles (x0, y0, x1, y1), y down from the top of the image.
REGIONS = {
    "logo": (0, 0, 128, 48),
    "tape": (128, 0, 256, 32),
    "shell": (128, 32, 192, 64),
    "brass": (192, 32, 256, 64),
    "black": (0, 192, 64, 256),
}

REGIONS.update({name: gun_plates.rect(i) for i, name in enumerate(gun_plates.STAMPS)})

BLACK = (28, 28, 30)  # MatteBlack as it renders after the baked shading
PRINT = (176, 178, 172)
TAPE = (212, 168, 38)
SHELL = (148, 28, 26)
BRASS = (176, 134, 62)

# Stroke letters on a 4 x 6 grid, one polyline list per letter.
LETTERS = {
    "O": [[(0, 0), (4, 0), (4, 6), (0, 6), (0, 0)]],
    "R": [[(0, 6), (0, 0), (4, 0), (4, 3), (0, 3)], [(1.5, 3), (4, 6)]],
    "I": [[(0, 0), (0, 6)]],
    "E": [[(4, 0), (0, 0), (0, 6), (4, 6)], [(0, 3), (3, 3)]],
    "L": [[(0, 0), (0, 6), (4, 6)]],
}


def uv_rect(region: str) -> tuple:
    """Blender UV rectangle (u0, v0, u1, v1) of a region; v grows upwards."""
    x0, y0, x1, y1 = REGIONS[region]
    return (x0 / SIZE, 1.0 - y1 / SIZE, x1 / SIZE, 1.0 - y0 / SIZE)


def _fill(img: list, rect: tuple, color: tuple) -> None:
    x0, y0, x1, y1 = rect
    for y in range(y0, y1):
        for x in range(x0, x1):
            img[y][x] = color


def _shade(color: tuple, k: float) -> tuple:
    return tuple(max(0, min(255, round(c * k))) for c in color)


def _dot(img: list, cx: float, cy: float, r: float, color: tuple) -> None:
    for y in range(math.floor(cy - r), math.ceil(cy + r) + 1):
        for x in range(math.floor(cx - r), math.ceil(cx + r) + 1):
            if 0 <= y < len(img) and 0 <= x < len(img[y]) and (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                img[y][x] = color


def _line(img: list, a: tuple, b: tuple, r: float, color: tuple) -> None:
    steps = max(1, round(math.dist(a, b) * 2))
    for i in range(steps + 1):
        t = i / steps
        _dot(img, a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, r, color)


def _hex_ring(img: list, cx: float, cy: float, outer: float, inner: float, color: tuple) -> None:
    def inside(x: float, y: float, r: float) -> bool:
        x, y = abs(x), abs(y)
        return y <= r * math.sqrt(3) / 2 and x * math.sqrt(3) / 2 + y / 2 <= r * math.sqrt(3) / 2

    for y in range(SIZE):
        for x in range(SIZE):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            if inside(dx, dy, outer) and not inside(dx, dy, inner):
                img[y][x] = color


def _logo(img: list, rng: random.Random) -> None:
    _hex_ring(img, 22, 24, 15, 10, PRINT)
    x = 44
    for letter in "ORIEL":
        for stroke in LETTERS[letter]:
            for a, b in itertools.pairwise(stroke):
                _line(img, (x + a[0] * 3.2, 12 + a[1] * 3.2), (x + b[0] * 3.2, 12 + b[1] * 3.2), 1.3, PRINT)
        x += 5 if letter == "I" else 4 * 3.2 + 5
    _fill(img, (44, 37, 114, 39), _shade(PRINT, 0.7))
    _worn(img, REGIONS["logo"], PRINT, BLACK, 0.04, rng)


def _worn(img: list, rect: tuple, ink: tuple, base: tuple, amount: float, rng: random.Random) -> None:
    """Scuffs printed pixels back to the base colour, a few pixels at a time."""
    x0, y0, x1, y1 = rect
    for y in range(y0, y1):
        for x in range(x0, x1):
            if img[y][x] == ink and rng.random() < amount:
                img[y][x] = base


def _tape(img: list, rng: random.Random) -> None:
    x0, y0, x1, y1 = REGIONS["tape"]
    for y in range(y0, y1):
        for x in range(x0, x1):
            k = 0.92 + 0.08 * math.sin(x * 0.7 + y * 0.13) + rng.uniform(-0.04, 0.04)
            img[y][x] = _shade(TAPE, k)
    for _ in range(40):
        cx, cy = rng.uniform(x0, x1), rng.uniform(y0, y1)
        _dot(img, cx, cy, rng.uniform(0.6, 1.8), _shade(TAPE, 0.45))


def _shell(img: list, rng: random.Random) -> None:
    x0, y0, x1, y1 = REGIONS["shell"]
    for y in range(y0, y1):
        for x in range(x0, x1):
            rib = 0.8 if (x - x0) % 6 < 2 else 1.0
            img[y][x] = _shade(SHELL, rib * rng.uniform(0.95, 1.05))


def _brass(img: list) -> None:
    x0, y0, x1, y1 = REGIONS["brass"]
    for y in range(y0, y1):
        k = 0.8 + 0.4 * math.sin(math.pi * (y - y0) / (y1 - y0))
        for x in range(x0, x1):
            img[y][x] = _shade(BRASS, k)


def draw() -> list:
    rng = random.Random(72)
    img = [[BLACK] * SIZE for _ in range(SIZE)]
    _logo(img, rng)
    _tape(img, rng)
    _shell(img, rng)
    _brass(img)
    return img


def png_bytes(img: list) -> bytes:
    # Original UVs and the single-colour back of each printed plate stay in place.
    expanded = [[pixel for pixel in row for _ in range(4)] for row in img]
    img = [row.copy() for row in expanded for _ in range(4)]
    gun_plates.draw(img, _line)
    raw = b"".join(b"\x00" + bytes(c for px in row for c in px) for row in img)

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", len(img[0]), len(img), 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(png_bytes(draw()))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
