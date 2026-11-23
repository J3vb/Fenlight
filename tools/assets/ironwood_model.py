"""Ironwood .50: long semi-auto anti-materiel rifle with a vented chassis and a deep brake.

The action, safety, guard and grip join Receiver; the stock, scope, barrel,
magazine, bolt and trigger preserve their own inspectable nodes and pivots.
"""

import math

import gun_parts as g

BORE_Z = 0.018
SCOPE_Z = 0.09


def action(metal, black):
    """Wide rectangular action with a recessed right ejection port and its machined controls."""
    upper = g.slab(
        "Receiver",
        [(-0.19, -0.008), (0.18, -0.008), (0.18, 0.033), (0.15, 0.046), (-0.17, 0.046), (-0.19, 0.03)],
        0.064,
        black,
        bevel=0.002,
    )
    g.cut(upper, [g.slab("PortCut", g.rounded(-0.09, 0.005, 0.08, 0.033, 0.005), 0.028, metal, x=0.035)])
    pieces = [
        g.slab("Lower", g.rounded(-0.17, -0.046, 0.135, -0.005, 0.006), 0.056, metal, bevel=0.0015),
        g.slab("Rail", g.teeth(-0.17, 0.17, 0.046, 0.057, pitch=0.016), 0.024, black),
        g.slab("WellLip", g.rounded(0.008, -0.057, 0.12, -0.04, 0.003), 0.061, black, bevel=0.001),
        g.slab(
            "Guard",
            [
                (0.005, -0.046),
                (0.005, -0.086),
                (-0.08, -0.086),
                (-0.105, -0.046),
                (-0.096, -0.046),
                (-0.075, -0.078),
                (-0.003, -0.078),
                (-0.003, -0.046),
            ],
            0.014,
            black,
            bevel=0.0015,
        ),
    ]
    for side in (-1, 1):
        for y in (-0.15, 0.125):
            ends = sorted((side * 0.031, side * 0.034))
            pieces.append(
                g.lathe(f"ActionPin{side}{y}", [(0.004, end) for end in ends], (0, y, 0.016), metal, 10, axis="x")
            )
        pieces.append(
            g.slab(f"Safety{side}", g.rounded(-0.13, -0.026, -0.095, -0.018, 0.003), 0.005, black, x=side * 0.03)
        )
    return upper, pieces


def furniture(m, receiver, black, tan):
    """Angular fixed chassis stock and a full pistol grip; a high cheek rest follows the optic."""
    stock = g.slab(
        "Stock",
        [
            (-0.18, 0.015),
            (-0.265, 0.015),
            (-0.32, 0.034),
            (-0.425, 0.034),
            (-0.425, -0.112),
            (-0.38, -0.11),
            (-0.28, -0.06),
            (-0.18, -0.045),
        ],
        0.049,
        tan,
        bevel=0.004,
    )
    g.cut(stock, [g.slab("StockWindow", g.rounded(-0.375, -0.065, -0.245, -0.014, 0.012), 0.065, tan)])
    m.join_into(
        stock,
        [
            g.contoured("CheekRest", g.rounded(-0.408, 0.029, -0.284, 0.048, 0.006), 0.052, black, roll=0.008),
            g.contoured("ButtPad", g.rounded(-0.443, -0.114, -0.425, 0.038, 0.007), 0.058, black, roll=0.006),
        ],
    )
    m.attach(stock, (0, -0.18, 0), receiver)
    grip = g.contoured(
        "Grip",
        [
            (-0.11, -0.04),
            (-0.157, -0.04),
            (-0.196, -0.162),
            (-0.181, -0.176),
            (-0.144, -0.174),
            (-0.13, -0.11),
            (-0.12, -0.098),
        ],
        0.038,
        tan,
        roll=0.011,
    )
    panels = [
        g.slab(f"GripPanel{side}", g.rounded(-0.18, -0.154, -0.146, -0.074, 0.007), 0.002, black, x=side * 0.0195)
        for side in (-1, 1)
    ]
    m.join_into(receiver, [grip, *panels])


def fore_end(metal, tan):
    """Hollow octagonal shroud with real transverse slots around the free-floating barrel."""
    shell = g.lathe(
        "Handguard",
        [(0.038, 0.175), (0.042, 0.19), (0.042, 0.54), (0.037, 0.56)],
        (0, 0, BORE_Z),
        tan,
        8,
        turn=math.pi / 8,
    )
    cuts = [g.lathe("CoreCut", [(0.032, 0.17), (0.032, 0.565)], (0, 0, BORE_Z), metal, 16)]
    for i in range(5):
        y = 0.21 + i * 0.06
        cuts.append(g.slab(f"SideVent{i}", g.rounded(y, BORE_Z - 0.01, y + 0.038, BORE_Z + 0.01, 0.005), 0.1, metal))
    g.cut(shell, cuts)
    return shell


def barrel(m, receiver, metal, black):
    """Stepped long barrel with an open bore and a broad three-chamber muzzle brake."""
    tube = g.lathe(
        "Barrel",
        [(0.022, 0.16), (0.022, 0.23), (0.018, 0.27), (0.018, 0.99), (0.016, 1.0), (0.016, 1.014)],
        (0, 0, BORE_Z),
        metal,
        20,
    )
    g.cut(tube, [g.lathe("BarrelBore", [(0.0065, 0.155), (0.0065, 1.02)], (0, 0, BORE_Z), metal, 16)])
    brake = g.slab(
        "MuzzleBrake", g.rounded(1.01, BORE_Z - 0.028, 1.105, BORE_Z + 0.028, 0.005), 0.076, black, bevel=0.002
    )
    cuts = [g.lathe("BrakeBore", [(0.0075, 1.005), (0.0075, 1.11)], (0, 0, BORE_Z), metal, 16)]
    for i in range(3):
        y = 1.02 + i * 0.026
        cuts.append(
            g.slab(f"BrakePort{i}", g.rounded(y, BORE_Z - 0.015, y + 0.015, BORE_Z + 0.015, 0.004), 0.09, metal)
        )
    g.cut(brake, cuts)
    m.attach(tube, (0, 0.18, BORE_Z), receiver)
    m.attach(brake, (0, 1.01, BORE_Z), tube)
    m.marker("Muzzle", (0, 1.107, BORE_Z), parent=receiver)


def optic(m, receiver, metal, black, glass):
    """Four-power scope with two rings, turrets and the same lens line as the Corvid."""
    scope = g.lathe(
        "Optic",
        [
            (0.021, -0.126),
            (0.022, -0.12),
            (0.022, -0.08),
            (0.016, -0.055),
            (0.016, 0.18),
            (0.029, 0.25),
            (0.03, 0.32),
            (0.028, 0.325),
        ],
        (0, 0, SCOPE_Z),
        black,
        24,
    )
    parts = [
        g.lathe("Elevation", [(0.011, 0.012), (0.011, 0.032)], (0, 0.04, SCOPE_Z), metal, 16, axis="z"),
        g.lathe("Windage", [(0.01, 0.012), (0.01, 0.034)], (0, 0.04, SCOPE_Z), metal, 16, axis="x"),
        g.lathe("ZoomRing", [(0.023, -0.073), (0.023, -0.055)], (0, 0, SCOPE_Z), metal, 24),
    ]
    for y in (-0.025, 0.15):
        parts += [
            g.lathe(f"Ring{y}", [(0.02, y - 0.009), (0.02, y + 0.009)], (0, 0, SCOPE_Z), metal, 20),
            g.slab(f"Mount{y}", g.rounded(y - 0.014, 0.055, y + 0.014, 0.079, 0.003), 0.032, black, bevel=0.0015),
        ]
    m.join_into(scope, parts)
    m.attach(scope, (0, 0.055, SCOPE_Z), receiver)
    g.lathe("OpticGlass", [(0.026, 0.3255), (0.026, 0.3265)], (0, 0, SCOPE_Z), glass, 24, parent=receiver)
    m.marker("ScopeLensMount", (0, -0.128, SCOPE_Z), parent=receiver)


def moving_parts(m, receiver, metal, black):
    """Reciprocating bolt, short side charger, six-round box and a hooked trigger."""
    bolt = g.slab("Bolt", g.rounded(-0.087, 0.009, 0.075, 0.03, 0.004), 0.017, metal, x=0.02)
    m.attach(bolt, (0.02, -0.04, 0.018), receiver)
    handle = g.lathe(
        "ChargingHandle",
        [(0.004, 0.026), (0.004, 0.045), (0.007, 0.047), (0.007, 0.057)],
        (0, -0.06, 0.018),
        black,
        12,
        axis="x",
    )
    m.attach(handle, (0.026, -0.06, 0.018), bolt)
    magazine = g.slab(
        "Magazine", [(0.015, -0.05), (0.116, -0.05), (0.125, -0.15), (0.021, -0.15)], 0.05, black, bevel=0.003
    )
    ribs = [
        g.slab(f"MagazineRib{side}", g.rounded(0.033, -0.134, 0.104, -0.073, 0.004), 0.002, metal, x=side * 0.0255)
        for side in (-1, 1)
    ]
    m.join_into(
        magazine,
        [*ribs, g.slab("MagazineBase", g.rounded(0.016, -0.16, 0.13, -0.147, 0.003), 0.056, metal, bevel=0.001)],
    )
    m.attach(magazine, (0, 0.065, -0.05), receiver)
    trigger = g.slab(
        "Trigger",
        [(-0.04, -0.046), (-0.033, -0.046), (-0.038, -0.061), (-0.05, -0.073), (-0.056, -0.07), (-0.045, -0.059)],
        0.006,
        metal,
    )
    m.attach(trigger, (0, -0.038, -0.046), receiver)


def build(m) -> None:
    """Build a distinct heavy semi-auto silhouette using the shared gun geometry helpers."""
    metal = m.material("GunMetal", m.GUN_METAL, metallic=0.8, roughness=0.4)
    black = m.material("MatteBlack", m.MATTE_BLACK, roughness=0.75)
    tan = m.material("Tan", m.TAN, roughness=0.8)
    glass = m.material("OpticGlass", m.LENS, metallic=0.3, roughness=0.05)
    receiver, pieces = action(metal, black)
    m.join_into(receiver, [*pieces, fore_end(metal, tan)])
    furniture(m, receiver, black, tan)
    barrel(m, receiver, metal, black)
    optic(m, receiver, metal, black, glass)
    moving_parts(m, receiver, metal, black)
    g.add_inlays(m, receiver, g.rounded(-0.15, 0.039, 0.12, 0.041, 0.0008), 0.001, 0.0323, metal)
    g.stamp(m, "ironwood_50", "Receiver", (-0.032, -0.085, 0.019), 0.085)
