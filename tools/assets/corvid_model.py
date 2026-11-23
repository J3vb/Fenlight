"""Corvid .338: bolt-action sniper with a thumbhole stock, fluted heavy barrel, big brake and a 5-25x optic.

Static parts join into `Receiver`. Code and tests need `Stock`, `Optic`, `OpticGlass`,
`ScopeLensMount`, `Barrel` (with `MuzzleBrake`), `Magazine`, `Bolt` (with `ChargingHandle`,
the bolt handle), `Trigger` and the `Muzzle` marker.
"""

import math

import gun_parts as g

BORE_Z = 0.018
SCOPE_Z = 0.09


def action_parts(metal, black):
    """Round action on a recoil lug, top rail, bolt shroud and the magazine well."""
    parts = [
        g.lathe("Action", [(0.02, -0.16), (0.023, -0.155), (0.023, 0.12), (0.02, 0.125)], (0, 0, BORE_Z), metal, 24),
        g.lathe("Shroud", [(0.014, -0.2), (0.018, -0.195), (0.018, -0.16)], (0, 0, BORE_Z), black, 16),
        g.slab("RailBase", [(-0.15, 0.038), (0.13, 0.038), (0.13, 0.05), (-0.15, 0.05)], 0.026, black),
        g.slab("RailTeeth", g.teeth(-0.145, 0.125, 0.05, 0.057, pitch=0.012), 0.022, black),
        g.slab("Lug", [(0.08, -0.004), (0.1, -0.004), (0.1, -0.022), (0.08, -0.022)], 0.04, metal, bevel=0.0015),
        g.slab(
            "WellLip", [(0.006, -0.052), (0.096, -0.052), (0.098, -0.062), (0.004, -0.062)], 0.05, black, bevel=0.0015
        ),
    ]
    g.cut(parts[0], [g.slab("PortCut", g.rounded(-0.07, 0.008, 0.03, 0.035, 0.006), 0.035, metal, x=0.0255)])
    for x in (-1, 1):
        for y in (-0.12, 0.09):
            parts.append(
                g.lathe(f"Screw{x}{y}", [(0.004, -0.0015), (0.004, 0.0015)], (x * 0.025, y, -0.01), metal, 10, axis="x")
            )
    return parts


def stock_parts(m, receiver, metal, black, tan):
    """Thumbhole stock with adjustable cheek piece, flat forend and a recoil pad."""
    outline = [
        (0.42, -0.005),
        (0.42, -0.03),
        (0.12, -0.05),
        (0.09, -0.062),
        (0.01, -0.062),
        (-0.02, -0.05),
        (-0.08, -0.05),
        (-0.1, -0.16),
        (-0.096, -0.172),
        (-0.13, -0.172),
        (-0.14, -0.16),
        (-0.13, -0.1),
        (-0.15, -0.045),
        (-0.24, -0.045),
        (-0.36, -0.06),
        (-0.44, -0.11),
        (-0.46, -0.1),
        (-0.45, 0.03),
        (-0.3, 0.03),
        (-0.24, 0.0),
        (-0.15, 0.0),
        (-0.15, -0.005),
    ]
    stock = g.slab("Stock", outline, 0.05, tan, bevel=0.004)
    g.cut(stock, [g.slab("ThumbholeCut", g.rounded(-0.143, -0.047, -0.098, -0.011, 0.01), 0.07, tan)])
    guard = [
        (0.016, -0.05),
        (0.016, -0.09),
        (-0.06, -0.09),
        (-0.07, -0.06),
        (-0.062, -0.06),
        (-0.054, -0.082),
        (0.008, -0.082),
        (0.008, -0.05),
    ]
    pieces = [
        g.contoured("CheekPiece", g.rounded(-0.4, 0.03, -0.26, 0.05, 0.008), 0.044, black, roll=0.008),
        g.contoured(
            "RecoilPad",
            [(-0.448, 0.032), (-0.47, 0.032), (-0.472, -0.104), (-0.46, -0.112), (-0.444, -0.105)],
            0.054,
            black,
            roll=0.007,
        ),
        g.slab("TriggerGuard", guard, 0.014, black, bevel=0.0015),
    ]
    for y in (-0.37, -0.29):
        pieces.append(g.lathe(f"CheekPost{y}", [(0.005, 0.02), (0.005, 0.034)], (0, y, 0), metal, 10, axis="z"))
    for x in (-1, 1):
        pieces.append(g.slab(f"Stipple{x}", g.rounded(-0.13, -0.155, -0.11, -0.08, 0.006), 0.002, black, x=x * 0.0255))
    vents = []
    for i in range(4):
        y = 0.18 + i * 0.055
        vents.append(g.slab(f"VentCut{i}", g.rounded(y, -0.024, y + 0.035, -0.011, 0.005), 0.07, tan))
    g.cut(stock, vents)
    pieces.append(g.lathe("SlingStud", [(0.005, -0.04), (0.005, -0.03)], (0, 0.38, 0), metal, 10, axis="z"))
    pieces.append(g.inspection_plate(m, "corvid_338", (-0.025, -0.195, -0.011), 0.085))
    m.join_into(stock, pieces)
    m.attach(stock, (0, -0.15, 0.0), receiver)


def scope_parts(m, receiver, metal, black, glass):
    """Long 5-25x optic on two rings; the rear lens mount matches the picture-in-picture disc."""
    tube = [
        (0.018, -0.126),
        (0.02, -0.12),
        (0.02, -0.075),
        (0.016, -0.066),
        (0.0145, -0.05),
        (0.0145, 0.2),
        (0.017, 0.22),
        (0.028, 0.28),
        (0.029, 0.35),
        (0.0275, 0.356),
    ]
    optic = g.lathe("Optic", tube, (0, 0, SCOPE_Z), black, 28)
    knob = [(0.008, 0.0), (0.008, 0.024), (0.012, 0.025), (0.012, 0.04), (0.0105, 0.042)]
    pieces = [
        g.lathe("Saddle", [(0.018, 0.03), (0.018, 0.075)], (0, 0, SCOPE_Z), black, 16),
        g.lathe("Elevation", knob, (0, 0.052, SCOPE_Z), metal, 16, axis="z"),
        g.lathe("Windage", knob, (0, 0.052, SCOPE_Z), metal, 16, axis="x"),
        g.lathe("SideFocus", [(r * 1.4, -a) for r, a in knob], (0, 0.052, SCOPE_Z), metal, 16, axis="x"),
        g.lathe("Magnifier", [(0.0215, -0.06), (0.0215, -0.04)], (0, 0, SCOPE_Z), metal, 24),
    ]
    for y in (-0.03, 0.18):
        pieces += [
            g.lathe(f"Ring{y}", [(0.0175, y - 0.01), (0.0175, y + 0.01)], (0, 0, SCOPE_Z), metal, 20),
            g.slab(
                f"RingBase{y}",
                [(y - 0.014, 0.057), (y + 0.014, 0.057), (y + 0.01, 0.076), (y - 0.01, 0.076)],
                0.028,
                black,
                bevel=0.002,
            ),
            g.lathe(f"RingBolt{y}", [(0.004, 0.014), (0.004, 0.02)], (0, y, 0.066), metal, 8, axis="x"),
        ]
    m.join_into(optic, pieces)
    m.attach(optic, (0, 0.06, SCOPE_Z), receiver)
    g.lathe("OpticGlass", [(0.0255, 0.3565), (0.0255, 0.3575)], (0, 0, SCOPE_Z), glass, 24, parent=receiver)
    m.marker("ScopeLensMount", (0, -0.128, SCOPE_Z), parent=receiver)


def barrel_parts(m, receiver, metal, black):
    """Fluted heavy barrel and a big three-port brake."""
    barrel = g.lathe(
        "Barrel",
        [(0.02, 0.12), (0.02, 0.17), (0.016, 0.2), (0.016, 0.78), (0.013, 0.785), (0.013, 0.8)],
        (0, 0, BORE_Z),
        metal,
        16,
    )
    flutes = []
    for i in range(6):
        flute = g.slab(f"FluteCut{i}", g.rounded(0.24, -0.003, 0.72, 0.003, 0.0029), 0.008, metal, x=0.018)
        flute.rotation_euler = (0.0, i * math.pi / 3, 0.0)
        flute.location = (0.0, 0.0, BORE_Z)
        flutes.append(flute)
    g.cut(barrel, flutes)
    m.attach(barrel, (0, 0.12, BORE_Z), receiver)
    brake = g.lathe(
        "MuzzleBrake", [(0.019, 0.796), (0.021, 0.8), (0.021, 0.875), (0.019, 0.88)], (0, 0, BORE_Z), metal, 16
    )
    cuts = [g.lathe("BoreCut", [(0.007, 0.79), (0.007, 0.89)], (0, 0, BORE_Z), metal, 16)]
    for i in range(3):
        y = 0.806 + i * 0.023
        cuts.append(g.slab(f"PortCut{i}", g.rounded(y, BORE_Z - 0.009, y + 0.016, BORE_Z + 0.009, 0.004), 0.06, metal))
    g.cut(brake, cuts)
    m.attach(brake, (0, 0.84, BORE_Z), barrel)
    m.marker("Muzzle", (0, 0.882, BORE_Z), parent=receiver)


def moving_parts(m, receiver, metal, black):
    """Bolt body with its handle and knob; flush 5-round magazine pivots at its feed end."""
    bolt = g.lathe("Bolt", [(0.0125, -0.155), (0.0125, 0.03)], (0, 0, BORE_Z + 0.008), metal, 16)
    m.attach(bolt, (0, -0.1, BORE_Z + 0.008), receiver)
    arm = [(0.004, 0.0), (0.004, 0.04)]
    handle = g.lathe("ChargingHandle", arm, (0, -0.135, BORE_Z + 0.008), metal, 10, axis="x")
    m.join_into(
        handle,
        [
            g.lathe(
                "Knob",
                [(0.006, 0.0), (0.011, 0.008), (0.011, 0.022), (0.006, 0.028)],
                (0.04, -0.135, BORE_Z + 0.008),
                black,
                16,
                axis="x",
            )
        ],
    )
    m.attach(handle, (0.012, -0.135, BORE_Z + 0.008), bolt)
    magazine = g.slab(
        "Magazine", [(0.012, -0.05), (0.09, -0.05), (0.092, -0.1), (0.014, -0.1)], 0.04, black, bevel=0.002
    )
    m.join_into(
        magazine,
        [
            g.slab(
                "MagBase",
                [(0.008, -0.098), (0.096, -0.098), (0.096, -0.108), (0.008, -0.108)],
                0.046,
                metal,
                bevel=0.002,
            )
        ],
    )
    m.attach(magazine, (0, 0.05, -0.05), receiver)
    trigger = g.slab(
        "Trigger",
        [(-0.028, -0.05), (-0.022, -0.05), (-0.024, -0.064), (-0.031, -0.076), (-0.036, -0.073), (-0.03, -0.063)],
        0.006,
        metal,
    )
    m.attach(trigger, (0, -0.025, -0.052), receiver)


def build(m) -> None:
    """Build from shared helpers supplied by build_models, keeping the runtime part names."""
    metal = m.material("GunMetal", m.GUN_METAL, metallic=0.8, roughness=0.4)
    black = m.material("MatteBlack", m.MATTE_BLACK, roughness=0.75)
    tan = m.material("Tan", m.TAN, roughness=0.8)
    glass = m.material("OpticGlass", m.LENS, metallic=0.3, roughness=0.05)
    receiver = g.slab(
        "Receiver", [(-0.15, -0.005), (0.12, -0.005), (0.12, 0.012), (-0.15, 0.012)], 0.04, metal, bevel=0.001
    )
    m.join_into(receiver, action_parts(metal, black))
    stock_parts(m, receiver, metal, black, tan)
    scope_parts(m, receiver, metal, black, glass)
    barrel_parts(m, receiver, metal, black)
    moving_parts(m, receiver, metal, black)
    g.add_inlays(m, receiver, g.rounded(-0.14, 0.041, 0.09, 0.043, 0.001), 0.001, 0.0132, metal)
