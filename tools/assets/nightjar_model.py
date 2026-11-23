"""Nightjar SD: low-profile SMG with an integral suppressor, slim magazine and compact fixed stock.

The receiver's recessed ejection port exposes `Bolt`; the vented fore-end
surrounds the suppressor's rear expansion chamber. Forward is Blender +Y.
"""

import math

import gun_parts as g

BORE_Z = 0.014
SIGHT_Z = 0.067


def receiver_body(m, metal, black, grey):
    """Tapered upper with a machined ejection pocket over a short polymer lower."""
    receiver = g.slab(
        "Receiver",
        [(-0.15, -0.006), (0.17, -0.006), (0.17, 0.033), (0.14, 0.043), (-0.13, 0.043), (-0.15, 0.029)],
        0.047,
        metal,
        bevel=0.002,
    )
    pocket = g.slab("EjectionPocket", g.rounded(-0.045, 0.008, 0.045, 0.033, 0.004), 0.024, black, x=0.029)
    g.cut(receiver, [pocket])
    parts = [
        g.slab(
            "Lower",
            [
                (-0.145, -0.006),
                (0.152, -0.006),
                (0.14, -0.035),
                (0.09, -0.043),
                (0.083, -0.062),
                (0.014, -0.062),
                (0.005, -0.042),
                (-0.12, -0.042),
                (-0.145, -0.027),
            ],
            0.045,
            grey,
            bevel=0.003,
        ),
        g.slab("RailBase", [(-0.125, 0.043), (0.15, 0.043), (0.15, 0.047), (-0.125, 0.047)], 0.023, black),
        g.slab("RailTeeth", g.teeth(-0.12, 0.145, 0.047, 0.054, pitch=0.012), 0.021, black),
        g.slab(
            "WellFlare", [(0.011, -0.056), (0.087, -0.056), (0.09, -0.067), (0.008, -0.067)], 0.047, black, bevel=0.0015
        ),
    ]
    parts += controls(metal, black)
    m.join_into(receiver, parts)
    return receiver


def controls(metal, black):
    """Selector, magazine catch and receiver pins share the static body."""
    parts = [
        g.lathe("Selector", [(0.007, -0.028), (0.007, -0.023)], (0, -0.09, -0.022), metal, 12, axis="x"),
        g.slab(
            "SelectorLever",
            [(-0.093, -0.025), (-0.071, -0.019), (-0.07, -0.015), (-0.091, -0.018)],
            0.004,
            black,
            x=-0.029,
            bevel=0.0007,
        ),
        g.lathe("MagazineCatch", [(0.005, 0.022), (0.005, 0.028)], (0, 0.09, -0.039), metal, 12, axis="x"),
    ]
    for side in (-1, 1):
        for y, z in ((-0.127, 0.014), (0.12, 0.014), (-0.052, -0.026), (0.054, -0.027)):
            parts.append(
                g.lathe("Pin", [(0.0033, -0.0014), (0.0033, 0.0014)], (side * 0.024, y, z), black, 12, axis="x")
            )
    return parts


def grip(m, receiver, black, grey):
    """Raked polymer grip with inset panels and a rubber cap."""
    grip = g.contoured(
        "Grip",
        [
            (-0.08, -0.041),
            (-0.116, -0.041),
            (-0.15, -0.135),
            (-0.143, -0.153),
            (-0.11, -0.153),
            (-0.1, -0.134),
            (-0.095, -0.109),
            (-0.086, -0.085),
        ],
        0.032,
        grey,
        roll=0.011,
    )
    panels = [
        g.slab(
            "GripCap",
            [(-0.146, -0.147), (-0.108, -0.147), (-0.109, -0.158), (-0.146, -0.158)],
            0.035,
            black,
            bevel=0.002,
        )
    ]
    for side in (-1, 1):
        panels.append(
            g.slab(
                "GripPanel",
                [(-0.109, -0.053), (-0.139, -0.134), (-0.12, -0.143), (-0.101, -0.098), (-0.094, -0.062)],
                0.002,
                black,
                x=side * 0.0165,
                bevel=0.001,
            )
        )
    m.join_into(grip, panels)
    m.attach(grip, (0, -0.096, -0.043), receiver)


def trigger_guard(m, receiver, metal, black):
    """Open guard and separate curved trigger sit ahead of the pistol grip."""
    guard = g.slab(
        "TriggerGuard",
        [
            (0.008, -0.043),
            (0.008, -0.078),
            (-0.066, -0.078),
            (-0.082, -0.042),
            (-0.074, -0.042),
            (-0.06, -0.07),
            (0.0, -0.07),
            (0.0, -0.043),
        ],
        0.012,
        black,
        bevel=0.0015,
    )
    m.join_into(receiver, [guard])
    trigger = g.slab(
        "Trigger",
        [(-0.036, -0.043), (-0.03, -0.043), (-0.033, -0.055), (-0.041, -0.066), (-0.047, -0.063), (-0.038, -0.054)],
        0.006,
        metal,
        bevel=0.0007,
    )
    m.attach(trigger, (0, -0.033, -0.045), receiver)


def fore_end(m, receiver, metal, black, grey):
    """A short vented grip sleeve encloses the suppressor chamber, with an exposed front can."""
    sleeve = g.lathe(
        "Handguard",
        [(0.032, 0.15), (0.035, 0.157), (0.035, 0.27), (0.031, 0.278)],
        (0, 0, BORE_Z),
        grey,
        12,
        turn=math.pi / 12,
    )
    cutters = [g.lathe("SleeveCore", [(0.029, 0.148), (0.029, 0.28)], (0, 0, BORE_Z), metal, 24)]
    for i in range(3):
        y = 0.17 + 0.032 * i
        cutters.append(g.slab("CoolingVent", g.rounded(y, 0.008, y + 0.019, 0.023, 0.005), 0.085, black))
    g.cut(sleeve, cutters)
    m.attach(sleeve, (0, 0.157, BORE_Z), receiver)
    barrel = g.lathe("Barrel", [(0.011, 0.13), (0.011, 0.23)], (0, 0, BORE_Z), metal, 20)
    m.attach(barrel, (0, 0.15, BORE_Z), receiver)
    profile = [
        (0.026, 0.16),
        (0.028, 0.165),
        (0.028, 0.275),
        (0.027, 0.279),
        (0.027, 0.398),
        (0.026, 0.404),
        (0.023, 0.408),
        (0.023, 0.42),
        (0.021, 0.424),
    ]
    suppressor = g.lathe("Suppressor", profile, (0, 0, BORE_Z), black, 32)
    g.cut(suppressor, [g.lathe("MuzzleBore", [(0.0055, 0.385), (0.0055, 0.427)], (0, 0, BORE_Z), black, 24)])
    collars = []
    for y in (0.284, 0.302, 0.32):
        collar = g.lathe(
            "CanRing",
            [(0.0272, y), (0.0278, y + 0.001), (0.0278, y + 0.004), (0.0272, y + 0.005)],
            (0, 0, BORE_Z),
            black,
            24,
        )
        g.cut(collar, [g.lathe("RingCore", [(0.025, y - 0.001), (0.025, y + 0.006)], (0, 0, BORE_Z), black, 24)])
        collars.append(collar)
    m.join_into(suppressor, collars)
    m.attach(suppressor, (0, 0.16, BORE_Z), receiver)
    m.marker("Muzzle", (0, 0.425, BORE_Z), parent=receiver)


def stock(m, receiver, black, grey):
    """Thin fixed stock with an open lower brace and an inset cheek panel."""
    butt = g.slab(
        "Stock",
        [
            (-0.145, 0.026),
            (-0.326, 0.035),
            (-0.342, 0.019),
            (-0.342, -0.078),
            (-0.326, -0.083),
            (-0.306, -0.034),
            (-0.212, -0.018),
            (-0.145, -0.012),
        ],
        0.039,
        grey,
        bevel=0.004,
    )
    opening = g.slab(
        "StockOpening",
        [(-0.178, -0.002), (-0.304, 0.011), (-0.309, -0.016), (-0.205, -0.009)],
        0.055,
        black,
        bevel=0.003,
    )
    g.cut(butt, [opening])
    parts = [
        g.contoured(
            "ButtPad", [(-0.341, 0.028), (-0.353, 0.028), (-0.355, -0.08), (-0.341, -0.087)], 0.045, black, roll=0.006
        ),
        g.contoured("CheekRest", g.rounded(-0.313, 0.021, -0.206, 0.034, 0.004), 0.041, black, roll=0.008),
    ]
    m.join_into(butt, parts)
    m.attach(butt, (0, -0.145, 0.008), receiver)


def sights(m, receiver, metal, black):
    """Protected iron posts keep the top line low; the sight axis is 67 mm above the origin."""
    rear = g.slab(
        "IronSights", [(-0.115, 0.054), (-0.094, 0.054), (-0.096, 0.06), (-0.113, 0.06)], 0.028, black, bevel=0.001
    )
    parts = [
        g.slab("FrontBase", [(0.128, 0.05), (0.15, 0.05), (0.148, 0.057), (0.13, 0.057)], 0.027, black, bevel=0.001)
    ]
    for side in (-1, 1):
        parts.append(
            g.slab(
                "RearEar",
                [(-0.112, 0.058), (-0.099, 0.058), (-0.1, 0.073), (-0.111, 0.073)],
                0.004,
                black,
                x=side * 0.009,
                bevel=0.0007,
            )
        )
        parts.append(
            g.slab(
                "FrontEar",
                [(0.13, 0.054), (0.148, 0.054), (0.145, 0.073), (0.133, 0.073)],
                0.004,
                black,
                x=side * 0.009,
                bevel=0.0007,
            )
        )
    parts += [
        g.slab("RearBridge", [(-0.112, 0.071), (-0.1, 0.071), (-0.1, 0.075), (-0.112, 0.075)], 0.022, black),
        g.slab(
            "FrontPost",
            [(0.137, 0.056), (0.141, 0.056), (0.141, SIGHT_Z), (0.137, SIGHT_Z)],
            0.003,
            metal,
            bevel=0.0005,
        ),
    ]
    m.join_into(rear, parts)
    m.attach(rear, (0, -0.105, 0.054), receiver)


def moving_parts(m, receiver, metal, black, grey):
    """Straight 32-round magazine and a bolt sunk behind the receiver's cut-out."""
    magazine = g.slab(
        "Magazine", [(0.02, -0.057), (0.078, -0.057), (0.09, -0.207), (0.033, -0.214)], 0.031, metal, bevel=0.002
    )
    parts = [
        g.slab(
            "MagBase", [(0.028, -0.208), (0.093, -0.201), (0.096, -0.217), (0.03, -0.224)], 0.037, black, bevel=0.002
        )
    ]
    for side in (-1, 1):
        for offset in (0.0, 0.021):
            parts.append(
                g.slab(
                    "MagFlute",
                    [
                        (0.032 + offset, -0.077),
                        (0.037 + offset, -0.077),
                        (0.047 + offset, -0.194),
                        (0.041 + offset, -0.195),
                    ],
                    0.0014,
                    black,
                    x=side * 0.0159,
                    bevel=0.0005,
                )
            )
        parts.append(g.slab("MagLatch", g.rounded(0.039, -0.069, 0.06, -0.064, 0.0015), 0.001, grey, x=side * 0.016))
    m.join_into(magazine, parts)
    m.attach(magazine, (0, 0.049, -0.058), receiver)
    bolt = g.slab("Bolt", g.rounded(-0.037, 0.011, 0.038, 0.03, 0.003), 0.003, metal, x=0.0185)
    m.attach(bolt, (0.0185, 0.0, 0.02), receiver)
    handle = g.lathe(
        "ChargingHandle",
        [(0.004, 0.019), (0.004, 0.034), (0.006, 0.035), (0.006, 0.043), (0.0045, 0.045)],
        (0, -0.027, 0.023),
        black,
        12,
        axis="x",
    )
    m.attach(handle, (0.019, -0.027, 0.023), bolt)


def build(m) -> None:
    """Build the suppressed SMG using the shared finish names and moving-part contracts."""
    metal = m.material("GunMetal", m.GUN_METAL, metallic=0.8, roughness=0.45)
    black = m.material("MatteBlack", m.MATTE_BLACK, roughness=0.75)
    grey = m.material("GreyPolymer", m.srgb("#5F6D68"), roughness=0.85)
    receiver = receiver_body(m, metal, black, grey)
    grip(m, receiver, black, grey)
    trigger_guard(m, receiver, metal, black)
    fore_end(m, receiver, metal, black, grey)
    stock(m, receiver, black, grey)
    sights(m, receiver, metal, black)
    moving_parts(m, receiver, metal, black, grey)
    g.add_inlays(m, receiver, g.rounded(-0.126, 0.037, 0.125, 0.039, 0.0008), 0.0006, 0.0237, metal)
    g.stamp(m, "nightjar_sd", "Receiver", (-0.0235, -0.09, 0.019), 0.085)
