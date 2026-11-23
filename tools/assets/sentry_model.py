"""Sentry: compact three-round-burst rifle with an open frame stock and guarded iron sights.

Machined ports and handguard vents reveal real depth. The magazine, bolt,
charging handle and barrel keep separate pivots for the procedural viewmodel.
"""

import math

import gun_parts as g

BORE_Z = 0.018
SIGHT_Z = 0.079


def upper(m, metal, black):
    """Angular upper with a recessed right-side port and a stepped, continuous rail."""
    receiver = g.slab(
        "Receiver",
        [(-0.17, -0.006), (0.16, -0.006), (0.16, 0.04), (0.13, 0.052), (-0.145, 0.052), (-0.17, 0.035)],
        0.052,
        metal,
        bevel=0.002,
    )
    g.cut(receiver, [g.slab("PortCut", g.rounded(-0.033, 0.007, 0.065, 0.036, 0.005), 0.018, metal, x=0.028)])
    pieces = [
        g.slab("RailBase", [(-0.15, 0.052), (0.35, 0.052), (0.35, 0.057), (-0.15, 0.057)], 0.026, black),
        g.slab("RailTeeth", g.teeth(-0.145, 0.35, 0.057, 0.063, pitch=0.012), 0.022, black),
        g.slab(
            "Deflector",
            [(-0.052, 0.002), (-0.036, 0.005), (-0.036, 0.04), (-0.052, 0.043)],
            0.009,
            metal,
            x=0.027,
            bevel=0.0015,
        ),
        g.lathe("Hinge", [(0.0022, -0.033), (0.0022, 0.065)], (0.027, 0, 0.004), black, 12),
    ]
    m.join_into(receiver, pieces)
    return receiver


def lower(black, tan):
    """A compact lower with a flared magazine well and a grooved swept grip."""
    grip = [
        (-0.084, -0.047),
        (-0.12, -0.047),
        (-0.159, -0.146),
        (-0.153, -0.163),
        (-0.121, -0.163),
        (-0.116, -0.147),
        (-0.112, -0.132),
        (-0.104, -0.117),
        (-0.101, -0.098),
        (-0.092, -0.083),
        (-0.089, -0.065),
    ]
    guard = [
        (0.012, -0.046),
        (0.012, -0.081),
        (-0.078, -0.081),
        (-0.092, -0.046),
        (-0.083, -0.046),
        (-0.072, -0.073),
        (0.004, -0.073),
        (0.004, -0.046),
    ]
    return [
        g.slab(
            "Lower",
            [
                (-0.165, -0.002),
                (0.12, -0.002),
                (0.117, -0.074),
                (0.02, -0.074),
                (0.012, -0.046),
                (-0.13, -0.046),
                (-0.165, -0.028),
            ],
            0.047,
            black,
            bevel=0.002,
        ),
        g.slab(
            "WellLip", [(0.015, -0.066), (0.12, -0.066), (0.122, -0.079), (0.013, -0.079)], 0.052, black, bevel=0.002
        ),
        g.contoured("Grip", grip, 0.032, tan, roll=0.011),
        g.slab("GripCap", g.rounded(-0.156, -0.17, -0.119, -0.158, 0.004), 0.035, black, bevel=0.001),
        g.slab("TriggerGuard", guard, 0.012, black, bevel=0.0015),
    ]


def controls(m, receiver, metal, black):
    """Pins, selector, magazine release and a hooked trigger stay visible from both sides."""
    pieces = []
    for side in (-1, 1):
        for y, z in ((-0.142, 0.012), (0.127, 0.015), (-0.064, -0.026), (0.075, -0.032)):
            pieces.append(
                g.lathe("Pin", [(0.0035, -0.0015), (0.0035, 0.0015)], (side * 0.025, y, z), metal, 12, axis="x")
            )
        pieces.append(
            g.slab(
                "GripPanel",
                [(-0.118, -0.065), (-0.145, -0.14), (-0.129, -0.15), (-0.11, -0.099), (-0.106, -0.07)],
                0.0018,
                black,
                x=side * 0.016,
            )
        )
        pieces.append(
            g.lathe("Selector", [(0.008, -0.002), (0.008, 0.002)], (side * 0.026, -0.094, -0.025), metal, 12, axis="x")
        )
        pieces.append(
            g.slab(
                "SelectorLever",
                [(-0.099, -0.028), (-0.072, -0.025), (-0.072, -0.021), (-0.096, -0.02)],
                0.002,
                black,
                x=side * 0.029,
            )
        )
    pieces.append(g.lathe("MagRelease", [(0.006, 0.024), (0.006, 0.029)], (0, 0.012, -0.031), metal, 12, axis="x"))
    m.join_into(receiver, pieces)
    trigger = g.slab(
        "Trigger",
        [(-0.034, -0.046), (-0.028, -0.046), (-0.03, -0.06), (-0.039, -0.071), (-0.045, -0.068), (-0.036, -0.058)],
        0.006,
        metal,
    )
    m.attach(trigger, (0, -0.031, -0.047), receiver)


def handguard(m, receiver, metal, black, tan):
    """Octagonal fore-end with a hollow core and four open vents on each side."""
    shell = g.lathe(
        "Handguard",
        [(0.029, 0.155), (0.033, 0.164), (0.033, 0.347), (0.029, 0.356)],
        (0, 0, BORE_Z),
        tan,
        8,
        turn=math.pi / 8,
    )
    cuts = [g.lathe("CoreCut", [(0.025, 0.151), (0.025, 0.36)], (0, 0, BORE_Z), metal, 16)]
    for i in range(4):
        y = 0.175 + i * 0.043
        cuts.append(g.slab("VentCut", g.rounded(y, 0.009, y + 0.027, 0.029, 0.005), 0.09, metal))
    g.cut(shell, cuts)
    m.attach(shell, (0, 0.155, BORE_Z), receiver)
    cap = g.lathe("GuardCollar", [(0.029, 0.146), (0.029, 0.16)], (0, 0, BORE_Z), black, 16)
    m.attach(cap, (0, 0.15, BORE_Z), receiver)
    grip = g.contoured(
        "Foregrip",
        [(0.22, -0.013), (0.296, -0.013), (0.283, -0.033), (0.244, -0.067), (0.225, -0.062)],
        0.029,
        black,
        roll=0.009,
    )
    m.attach(grip, (0, 0.25, -0.013), receiver)


def stock(m, receiver, metal, black, tan):
    """Fixed triangular stock with a genuine open window, cheek rest and rubber butt pad."""
    frame = g.slab(
        "Stock",
        [
            (-0.165, 0.037),
            (-0.38, 0.044),
            (-0.399, 0.026),
            (-0.403, -0.094),
            (-0.376, -0.099),
            (-0.194, -0.043),
            (-0.165, -0.022),
        ],
        0.044,
        tan,
        bevel=0.003,
    )
    window = [(-0.222, 0.009), (-0.356, 0.014), (-0.36, -0.06), (-0.232, -0.027)]
    g.cut(frame, [g.slab("StockWindow", window, 0.075, black, bevel=0.004)])
    pieces = [
        g.contoured("CheekRest", g.rounded(-0.37, 0.036, -0.21, 0.052, 0.007), 0.045, black, roll=0.008),
        g.contoured(
            "ButtPad",
            [(-0.4, 0.04), (-0.413, 0.036), (-0.416, -0.095), (-0.403, -0.105), (-0.395, -0.095)],
            0.048,
            black,
            roll=0.006,
        ),
        g.lathe("StockHinge", [(0.012, -0.026), (0.012, 0.026)], (0, -0.174, 0.01), metal, 16, axis="x"),
    ]
    for i in range(5):
        z = -0.072 + i * 0.021
        pieces.append(
            g.slab(
                "PadRib",
                [(-0.414, z), (-0.418, z), (-0.418, z + 0.007), (-0.414, z + 0.007)],
                0.048,
                black,
                bevel=0.0008,
            )
        )
    m.join_into(frame, pieces)
    m.attach(frame, (0, -0.17, 0.012), receiver)


def magazine(m, receiver, metal, black):
    """A gently swept, ribbed 30-round magazine pivots at its feed lips."""
    mag = g.slab(
        "Magazine",
        [(0.027, -0.065), (0.109, -0.065), (0.111, -0.127), (0.13, -0.214), (0.056, -0.222), (0.034, -0.139)],
        0.035,
        metal,
        bevel=0.002,
    )
    pieces = [
        g.slab(
            "MagBase", [(0.052, -0.217), (0.132, -0.209), (0.138, -0.225), (0.051, -0.235)], 0.041, black, bevel=0.002
        )
    ]
    for side in (-1, 1):
        for y in (0.046, 0.071, 0.095):
            rib = [
                (y, -0.09),
                (y + 0.006, -0.09),
                (y + 0.01, -0.145),
                (y + 0.022, -0.201),
                (y + 0.015, -0.204),
                (y + 0.003, -0.145),
            ]
            pieces.append(g.slab("MagRib", rib, 0.0018, black, x=side * 0.018, bevel=0.0006))
    m.join_into(mag, pieces)
    m.attach(mag, (0, 0.066, -0.065), receiver)


def barrel(m, receiver, metal, black):
    """Stepped barrel and short brake have a recessed bore and two open lateral gas ports."""
    pipe = g.lathe(
        "Barrel",
        [(0.011, 0.15), (0.011, 0.36), (0.013, 0.365), (0.013, 0.38), (0.0095, 0.385), (0.0095, 0.473)],
        (0, 0, BORE_Z),
        metal,
        20,
    )
    brake = g.lathe(
        "MuzzleBrake", [(0.012, 0.466), (0.016, 0.472), (0.016, 0.515), (0.013, 0.521)], (0, 0, BORE_Z), black, 20
    )
    g.cut(pipe, [g.lathe("BoreCut", [(0.006, 0.435), (0.006, 0.525)], (0, 0, BORE_Z), black, 20)])
    cuts = [g.lathe("BoreCut", [(0.006, 0.435), (0.006, 0.525)], (0, 0, BORE_Z), black, 20)]
    for y in (0.481, 0.501):
        cuts.append(g.slab("BrakePort", g.rounded(y - 0.004, 0.013, y + 0.004, 0.023, 0.003), 0.05, metal))
    g.cut(brake, cuts)
    m.attach(pipe, (0, 0.15, BORE_Z), receiver)
    m.attach(brake, (0, 0.466, BORE_Z), pipe)
    m.marker("Muzzle", (0, 0.522, BORE_Z), parent=receiver)


def sights(m, receiver, metal, black):
    """Guarded front post and a bored rear aperture line up at the fixed sight height."""
    rear = g.lathe("IronSights", [(0.012, -0.127), (0.012, -0.116)], (0, 0, SIGHT_Z), black, 20)
    g.cut(rear, [g.lathe("SightCut", [(0.006, -0.13), (0.006, -0.112)], (0, 0, SIGHT_Z), metal, 20)])
    pieces = [
        g.slab(
            "RearBase", [(-0.132, 0.063), (-0.11, 0.063), (-0.114, 0.075), (-0.128, 0.075)], 0.021, black, bevel=0.001
        )
    ]
    for side in (-1, 1):
        pieces.append(
            g.slab(
                "FrontEar",
                [(0.311, 0.063), (0.334, 0.063), (0.33, 0.093), (0.317, 0.093)],
                0.0035,
                black,
                x=side * 0.011,
                bevel=0.001,
            )
        )
    pieces += [
        g.slab(
            "FrontBase", [(0.309, 0.061), (0.336, 0.061), (0.333, 0.068), (0.312, 0.068)], 0.028, black, bevel=0.001
        ),
        g.slab("FrontPost", [(0.319, 0.067), (0.326, 0.067), (0.324, SIGHT_Z), (0.321, SIGHT_Z)], 0.003, metal),
    ]
    m.join_into(rear, pieces)
    m.attach(rear, (0, -0.122, SIGHT_Z), receiver)


def bolt(m, receiver, metal, black):
    """The inset bolt and its knurled charging handle ride in the receiver pocket."""
    part = g.slab("Bolt", g.rounded(-0.029, 0.01, 0.057, 0.032, 0.004), 0.002, metal, x=0.0185)
    m.attach(part, (0.0185, 0.015, 0.021), receiver)
    handle = g.lathe(
        "ChargingHandle",
        [(0.004, 0.019), (0.004, 0.034), (0.007, 0.037), (0.007, 0.05), (0.005, 0.053)],
        (0, -0.015, 0.022),
        black,
        16,
        axis="x",
    )
    m.attach(handle, (0.02, -0.015, 0.022), part)


def build(m) -> None:
    """Build the original rifle silhouette and a narrow rarity inlay on each receiver side."""
    metal = m.material("GunMetal", m.GUN_METAL, metallic=0.8, roughness=0.4)
    black = m.material("MatteBlack", m.MATTE_BLACK, roughness=0.75)
    tan = m.material("Tan", m.TAN, roughness=0.8)
    receiver = upper(m, metal, black)
    m.join_into(receiver, lower(black, tan))
    controls(m, receiver, metal, black)
    handguard(m, receiver, metal, black, tan)
    stock(m, receiver, metal, black, tan)
    magazine(m, receiver, metal, black)
    barrel(m, receiver, metal, black)
    sights(m, receiver, metal, black)
    bolt(m, receiver, metal, black)
    g.add_inlays(m, receiver, g.rounded(-0.13, 0.043, 0.12, 0.045, 0.0008), 0.0006, 0.026, metal)
    g.stamp(m, "sentry_br3", "Receiver", (-0.026, -0.085, 0.019), 0.085)
