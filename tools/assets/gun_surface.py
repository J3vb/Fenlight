"""Bake one seamless detail tile shared by the steel, moulded polymer and walnut finishes."""

from pathlib import Path

import numpy as np
from surface_textures import coords, fbm, streaks, write_png

OUT = Path(__file__).resolve().parents[2] / "assets/textures/weapons/surface_detail.png"


def surface_tile(size: int = 512) -> np.ndarray:
    u, v = coords(size)
    # Rubbed machining lines interrupted by patches and a few diagonal hairlines.
    steel = streaks(size, 20, 210, 32, 16)
    mask = fbm(size, 2, 19, 67)
    scratches = np.maximum(0, np.cos(2 * np.pi * (u * 3 + v * 59 + mask * 0.4))) ** 20
    steel = 0.17 + steel * 0.71 - scratches * np.clip((mask - 0.52) * 3, 0, 1) * 0.5
    # A bead-blasted mould surface with fine pores in the plateaux.
    grit = fbm(size, 29, 140, 45, beta=0.5)
    pits = np.clip((0.48 - grit) * 4.6, 0, 1)
    polymer = 0.73 - pits * 0.58 + (fbm(size, 100, 240, 46) - 0.5) * 0.16
    # Long earlywood bands curl around the figure. Narrow, broken vessels follow the grain.
    wave = fbm(size, 1, 4, 72) + 0.16 * fbm(size, 4, 13, 73)
    bands = 0.5 + 0.5 * np.cos(2 * np.pi * (v * 7 + 1.4 * wave))
    pores = np.clip((streaks(size, 20, 170, 78, 8) - 0.51) * 3.4, 0, 1)
    wood = 0.76 - bands**3 * 0.35 - pores**2 * 0.35 + (wave - 0.5) * 0.14
    tile = np.stack((steel, polymer, wood), axis=-1)
    return np.rint(np.clip(tile, 0, 1) * 255).astype(np.uint8)


if __name__ == "__main__":
    write_png(OUT, surface_tile())
