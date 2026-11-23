"""Surface texture sets tile without seams and stay inside the repo size budget."""

import os
import sys
import zlib
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import gun_surface
import surface_textures as st

BUDGET_BYTES = 25 * 1024 * 1024
SIZE = 256


def test_committed_weapon_detail_tile_matches_all_three_generated_channels():
    encoded = gun_surface.OUT.read_bytes()
    length = int.from_bytes(encoded[33:37], "big")
    tile = gun_surface.surface_tile()
    height, width, channels = tile.shape
    rows = np.frombuffer(zlib.decompress(encoded[41 : 41 + length]), np.uint8).reshape(height, 1 + width * channels)
    assert (rows[:, 0] == 1).all()
    decoded = np.cumsum(rows[:, 1:].reshape(tile.shape), axis=1) % 256
    np.testing.assert_array_equal(decoded, tile)
    config = gun_surface.OUT.with_suffix(".png.import").read_text()
    assert "compress/mode=2" in config
    assert "mipmaps/generate=true" in config


@pytest.mark.parametrize("name", sorted(st.SETS))
def test_set_tiles_without_a_seam(name):
    """Rolled by half a tile, the old edge sits mid-image; its step must look like any other column or row."""
    albedo, height, _rough, _metal, _strength = st.SETS[name][0](SIZE)
    for field in (np.asarray(albedo, float), np.asarray(height, float)):
        for axis in (0, 1):
            steps = np.abs(np.diff(np.roll(field, SIZE // 2, axis=axis), axis=axis)).mean(axis=1 - axis)
            seam = steps[SIZE // 2 - 1]
            others = np.delete(steps, SIZE // 2 - 1)
            assert seam <= others.max() * 1.05 + 1e-6, f"{name} axis {axis}: seam {seam:.4f}, max {others.max():.4f}"


@pytest.mark.parametrize("name", sorted(st.SETS))
def test_committed_maps_exist_at_the_set_size(name):
    n = st.SETS[name][1]
    for kind, size in (("albedo", n), ("normal", n), ("orm", n // 2)):
        data = (st.OUT / f"{name}_{kind}.png").read_bytes()
        assert data[:8] == b"\x89PNG\r\n\x1a\n"
        assert int.from_bytes(data[16:20], "big") == size and int.from_bytes(data[20:24], "big") == size


def test_texture_folder_stays_inside_the_budget():
    total = sum(f.stat().st_size for f in Path(st.OUT).glob("*.png"))
    assert total < BUDGET_BYTES, f"{total / 1e6:.1f} MB of textures, budget {BUDGET_BYTES / 1e6:.0f} MB"


def test_png_writer_round_trips(tmp_path):
    rgb = np.random.default_rng(1).integers(0, 256, (6, 7, 3), dtype=np.uint8)
    out = tmp_path / "t.png"
    st.write_png(out, rgb)
    data = out.read_bytes()
    length = int.from_bytes(data[33:37], "big")
    assert data[37:41] == b"IDAT"
    rows = np.frombuffer(zlib.decompress(data[41 : 41 + length]), np.uint8).reshape(6, 1 + 7 * 3)
    assert (rows[:, 0] == 1).all()
    decoded = np.cumsum(rows[:, 1:].reshape(6, 7, 3).astype(np.int64), axis=1) % 256
    assert (decoded == rgb).all()


@pytest.mark.parametrize("name", sorted(st.DECALS))
def test_decals_fade_out_at_their_edges(name):
    rgba = st.build_decal(name)
    border = np.concatenate([rgba[0, :, 3], rgba[-1, :, 3], rgba[:, 0, 3], rgba[:, -1, 3]])
    assert border.max() < 40, f"{name}: decal edge alpha {border.max()} would show a hard border"
    assert rgba[..., 3].max() > 150, f"{name}: decal is nearly invisible"
    data = (st.OUT / f"decal_{name}.png").read_bytes()
    assert data[25] == 6, "decals are RGBA"
