"""Halberd LMG: mag-fed light machine gun with a hinged feed cover, carry handle, finned barrel and 100-round box.

Static parts join into `Receiver`. Code and tests need `Magazine` (the box), `Bolt` (with
`ChargingHandle`), `Stock`, `Barrel`, `CarryHandle`, `Bipod`, `Trigger` and the `Muzzle` marker.
"""

import math

import gun_parts as g

BORE_Z = 0.03
SIGHT_Z = 0.098


def receiver_parts(metal, black, olive):
    """Long receiver, raised feed cover with the rear aperture, trigger housing and grip."""
    parts = [
        g.slab(
            "Body",
            [(-0.2, -0.01), (0.2, -0.01), (0.2, 0.06), (-0.185, 0.06), (-0.2, 0.045)],
            0.064,
            black,
            bevel=0.003,
        ),
        g.slab(
            "FeedCover",
            [(-0.12, 0.058), (0.13, 0.058), (0.13, 0.068), (0.1, 0.078), (-0.09, 0.078), (-0.12, 0.07)],
            0.058,
            black,
            bevel=0.003,
        ),
        g.lathe("CoverHinge", [(0.008, -0.034), (0.008, 0.034)], (0, 0.125, 0.064), metal, 12, axis="x"),
        g.slab("CoverLatch", g.rounded(-0.135, 0.056, -0.115, 0.072, 0.003), 0.03, metal, bevel=0.0015),
        g.slab(
            "Housing",
            [(-0.16, -0.008), (0.03, -0.008), (0.026, -0.055), (-0.14, -0.055), (-0.16, -0.035)],
            0.05,
            olive,
            bevel=0.003,
        ),
        g.slab("Well", [(0.03, -0.008), (0.17, -0.008), (0.168, -0.034), (0.032, -0.034)], 0.07, black, bevel=0.003),
        g.lathe("Selector", [(0.009, -0.027), (0.009, -0.023)], (0, -0.12, -0.03), metal, 12, axis="x"),
    ]
    for x in (-1, 1):
        parts.append(
            g.slab(
                f"RearEar{x}",
                [(-0.07, 0.078), (-0.05, 0.078), (-0.052, 0.108), (-0.068, 0.108)],
                0.005,
                black,
                x=x * 0.011,
            )
        )
        for i in range(6):
            y = -0.17 + i * 0.06
            ends = sorted((x * 0.0315, x * 0.0335))
            parts.append(
                g.lathe(f"Rivet{x}{i}", [(0.004, ends[0]), (0.004, ends[1])], (0, y, 0.048), metal, 8, axis="x")
            )
    parts.append(g.slab("RearRing", [(-0.068, 0.103), (-0.052, 0.103), (-0.052, 0.109), (-0.068, 0.109)], 0.027, black))
    grip = [
        (-0.098, -0.055),
        (-0.132, -0.055),
        (-0.176, -0.16),
        (-0.172, -0.174),
        (-0.136, -0.174),
        (-0.126, -0.16),
        (-0.118, -0.125),
        (-0.108, -0.095),
        (-0.102, -0.075),
    ]
    guard = [
        (0.01, -0.055),
        (0.01, -0.094),
        (-0.084, -0.094),
        (-0.1, -0.055),
        (-0.092, -0.055),
        (-0.08, -0.086),
        (0.002, -0.086),
        (0.002, -0.055),
    ]
    parts += [
        g.contoured("Grip", grip, 0.036, olive, roll=0.011),
        g.slab("TriggerGuard", guard, 0.014, black, bevel=0.0015),
    ]
    cut_port(parts[0], metal)
    g.cut(parts[1], [g.slab("CoverChannel", g.rounded(-0.04, 0.074, 0.075, 0.084, 0.003), 0.024, black, bevel=0.001)])
    return parts


def cut_port(part, metal):
    """Cut the layered housing separately so the port exposes the inset moving bolt."""
    g.cut(part, [g.slab("EjectionPocket", g.rounded(-0.09, 0.006, 0.085, 0.044, 0.005), 0.03, metal, x=0.039)])


def flash_hider(black):
    """A bored flash hider with transverse gas ports through its walls."""
    hider = g.lathe("Hider", [(0.015, 0.76), (0.017, 0.765), (0.017, 0.81), (0.014, 0.816)], (0, 0, BORE_Z), black, 12)
    cuts = [g.lathe("Bore", [(0.008, 0.73), (0.008, 0.818)], (0, 0, BORE_Z), black, 16)]
    for y in (0.776, 0.793):
        cuts.append(g.slab("HiderPort", g.rounded(y, 0.026, y + 0.008, 0.034, 0.003), 0.05, black))
    return g.cut(hider, cuts)


def front_parts(m, receiver, metal, black, olive):
    """Perforated heat shroud over a finned quick-change barrel, flash hider and front post."""
    shroud = g.lathe(
        "Handguard",
        [(0.034, 0.2), (0.038, 0.205), (0.038, 0.47), (0.033, 0.48)],
        (0, 0, BORE_Z),
        olive,
        10,
        turn=math.pi / 10,
    )
    holes = [g.lathe("ShroudCore", [(0.029, 0.198), (0.029, 0.482)], (0, 0, BORE_Z), metal, 20)]
    for i in range(7):
        y = 0.225 + i * 0.034
        holes.append(g.slab(f"Vent{i}", g.rounded(y, 0.018, y + 0.022, 0.042, 0.009), 0.09, black))
    g.cut(shroud, holes)
    m.attach(shroud, (0, 0.2, BORE_Z), receiver)
    barrel = g.lathe(
        "Barrel",
        [(0.018, 0.47), (0.018, 0.5), (0.014, 0.503), (0.014, 0.76), (0.012, 0.763)],
        (0, 0, BORE_Z),
        metal,
        16,
    )
    g.cut(barrel, [g.lathe("Bore", [(0.008, 0.73), (0.008, 0.818)], (0, 0, BORE_Z), black, 16)])
    pieces = [g.lathe("InnerBarrel", [(0.014, 0.19), (0.014, 0.48)], (0, 0, BORE_Z), metal, 16)]
    for i in range(6):
        y = 0.52 + i * 0.022
        pieces.append(g.lathe(f"Fin{i}", [(0.0195, y), (0.0195, y + 0.006)], (0, 0, BORE_Z), metal, 16))
    pieces += [
        flash_hider(black),
        g.slab(
            "FrontBase",
            [(0.69, BORE_Z + 0.012), (0.72, BORE_Z + 0.012), (0.716, BORE_Z + 0.03), (0.694, BORE_Z + 0.03)],
            0.016,
            black,
            bevel=0.0015,
        ),
        g.slab(
            "FrontPost",
            [(0.701, BORE_Z + 0.03), (0.709, BORE_Z + 0.03), (0.708, SIGHT_Z), (0.702, SIGHT_Z)],
            0.0035,
            metal,
        ),
    ]
    for x in (-1, 1):
        pieces.append(
            g.slab(
                f"FrontEar{x}",
                [(0.696, BORE_Z + 0.028), (0.714, BORE_Z + 0.028), (0.711, SIGHT_Z + 0.008), (0.699, SIGHT_Z + 0.008)],
                0.003,
                black,
                x=x * 0.009,
            )
        )
    m.join_into(barrel, pieces)
    m.attach(barrel, (0, 0.47, BORE_Z), receiver)
    m.marker("Muzzle", (0, 0.817, BORE_Z), parent=receiver)


def handle_and_bipod(m, receiver, metal, black):
    """Carry handle over the barrel joint and a folded bipod under the shroud."""
    handle = g.slab(
        "CarryHandle",
        [
            (0.2, 0.068),
            (0.22, 0.068),
            (0.24, 0.12),
            (0.34, 0.12),
            (0.36, 0.068),
            (0.38, 0.068),
            (0.355, 0.135),
            (0.225, 0.135),
        ],
        0.018,
        black,
        x=-0.04,
        bevel=0.003,
    )
    clamp = [
        g.lathe("HandleClamp", [(0.024, 0.19), (0.024, 0.21)], (0, 0, BORE_Z + 0.02), metal, 16),
        g.slab("HandleArm", [(0.19, 0.04), (0.215, 0.04), (0.215, 0.075), (0.19, 0.075)], 0.03, metal, x=-0.03),
    ]
    m.join_into(handle, clamp)
    m.attach(handle, (-0.04, 0.2, BORE_Z + 0.02), receiver)
    bipod = g.slab("Bipod", g.rounded(0.44, -0.02, 0.47, -0.006, 0.004), 0.05, metal, bevel=0.002)
    legs = []
    for x in (-1, 1):
        legs += [
            g.lathe(f"Leg{x}", [(0.007, 0.25), (0.007, 0.455), (0.005, 0.46)], (x * 0.024, 0, -0.022), black, 10),
            g.slab(f"Foot{x}", g.rounded(0.24, -0.032, 0.262, -0.012, 0.004), 0.018, black, x=x * 0.024),
        ]
    m.join_into(bipod, legs)
    m.attach(bipod, (0, 0.455, -0.013), receiver)


def stock_parts(m, receiver, metal, black, olive):
    """Skeleton stock with a top strut, shoulder rest and a folding monopod."""
    stock = g.contoured(
        "Stock",
        [(-0.2, 0.05), (-0.43, 0.04), (-0.44, -0.1), (-0.415, -0.105), (-0.3, -0.06), (-0.2, -0.045)],
        0.048,
        olive,
        roll=0.016,
    )
    g.cut(stock, [g.slab("StockWindow", g.rounded(-0.38, -0.04, -0.24, 0.01, 0.01), 0.06, black)])
    pieces = [
        g.slab(
            "ButtPlate",
            [(-0.432, 0.044), (-0.452, 0.044), (-0.455, -0.104), (-0.436, -0.11)],
            0.054,
            black,
            bevel=0.005,
        ),
        g.lathe("Monopod", [(0.007, -0.11), (0.007, -0.04)], (0, -0.4, 0), metal, 10, axis="z"),
    ]
    m.join_into(stock, pieces)
    m.attach(stock, (0, -0.2, 0.0), receiver)


def moving_parts(m, receiver, metal, black, olive):
    """100-round box pivots at its feed end; the charging handle rides the bolt."""
    magazine = g.slab(
        "Magazine", [(0.035, -0.034), (0.165, -0.034), (0.16, -0.19), (0.04, -0.19)], 0.068, olive, bevel=0.004
    )
    pieces = [
        g.slab("MagLid", [(0.03, -0.034), (0.17, -0.034), (0.17, -0.044), (0.03, -0.044)], 0.072, black, bevel=0.002)
    ]
    for x in (-1, 1):
        pieces.append(g.slab(f"MagPanel{x}", g.rounded(0.06, -0.17, 0.14, -0.06, 0.008), 0.002, black, x=x * 0.0345))
        pieces.append(g.slab(f"MagCatch{x}", g.rounded(0.16, -0.1, 0.168, -0.06, 0.003), 0.01, metal, x=x * 0.03))
    m.join_into(magazine, pieces)
    m.attach(magazine, (0, 0.1, -0.034), receiver)
    bolt = g.slab("Bolt", g.rounded(-0.08, 0.012, 0.04, 0.04, 0.003), 0.002, metal, x=0.0265)
    m.attach(bolt, (0.0325, -0.02, 0.026), receiver)
    knob = [(0.005, 0.034), (0.005, 0.046), (0.009, 0.048), (0.009, 0.058), (0.007, 0.06)]
    handle = g.lathe("ChargingHandle", knob, (0, 0.02, 0.026), black, 12, axis="x")
    m.attach(handle, (0.04, 0.02, 0.026), bolt)
    trigger = g.slab(
        "Trigger",
        [(-0.058, -0.055), (-0.052, -0.055), (-0.054, -0.07), (-0.062, -0.082), (-0.067, -0.079), (-0.06, -0.069)],
        0.006,
        metal,
    )
    m.attach(trigger, (0, -0.055, -0.057), receiver)


def build(m) -> None:
    """Build from shared helpers supplied by build_models, keeping the runtime part names."""
    metal = m.material("GunMetal", m.GUN_METAL, metallic=0.8, roughness=0.4)
    black = m.material("MatteBlack", m.MATTE_BLACK, roughness=0.75)
    olive = m.material("OlivePolymer", m.srgb("#5F6D68"), roughness=0.85)
    receiver = g.slab("Receiver", [(-0.19, 0.0), (0.19, 0.0), (0.19, 0.05), (-0.19, 0.05)], 0.056, metal, bevel=0.001)
    cut_port(receiver, metal)
    m.join_into(receiver, receiver_parts(metal, black, olive))
    front_parts(m, receiver, metal, black, olive)
    handle_and_bipod(m, receiver, metal, black)
    stock_parts(m, receiver, metal, black, olive)
    moving_parts(m, receiver, metal, black, olive)
    g.add_inlays(m, receiver, g.rounded(-0.09, 0.065, 0.09, 0.067, 0.0008), 0.0006, 0.029, metal)
    g.stamp(m, "halberd_lmg", "Receiver", (-0.032, -0.085, 0.019), 0.085)
