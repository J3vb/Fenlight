"""Siphon: an Oriel gravity emitter with an open containment cage and a three-cell power cassette.

The receiver owns separate Magazine, Bolt, Stock, Emitter, Core and Muzzle parts.
All dimensions are metres, with Blender +Y forward and the sight line at Z 0.14.
"""

import math

import gun_parts as g

BORE_Z = 0.045
SIGHT_Z = 0.14


def receiver_parts(metal, black, grey):
    """Faceted chassis and fitted side plates surround a recessed service port."""
    body = g.slab(
        "Receiver",
        [(-0.19, -0.035), (0.15, -0.035), (0.175, 0.005), (0.145, 0.083), (-0.15, 0.083), (-0.19, 0.052)],
        0.078,
        black,
        bevel=0.004,
    )
    g.cut(body, [g.slab("ServicePocket", g.rounded(-0.115, 0.012, 0.035, 0.058, 0.008), 0.026, metal, x=0.04)])
    parts = [
        g.slab(
            "LowerChassis", [(-0.17, -0.035), (0.15, -0.035), (0.12, -0.06), (-0.14, -0.06)], 0.064, grey, bevel=0.003
        ),
        g.slab("CassetteWell", g.rounded(-0.04, -0.077, 0.075, -0.035, 0.006), 0.064, metal, bevel=0.002),
        g.slab("TopBridge", [(-0.13, 0.08), (0.13, 0.08), (0.11, 0.112), (-0.10, 0.112)], 0.038, grey, bevel=0.003),
        g.slab("BridgeSlot", g.rounded(-0.075, 0.094, 0.07, 0.104, 0.003), 0.04, black),
    ]
    for side in (-1, 1):
        x = side * 0.041
        parts.append(g.slab("ServicePlate", g.rounded(-0.15, -0.027, -0.065, 0.006, 0.004), 0.004, grey, x=x))
        for y, z in ((-0.14, -0.01), (-0.075, -0.01), (0.08, 0.061), (0.11, -0.012)):
            parts.append(g.lathe("Fastener", [(0.004, -0.002), (0.004, 0.002)], (x, y, z), metal, 8, axis="x"))
    return body, parts


def grip_parts(m, receiver, metal, black, grey):
    """Swept grip with fitted ribs and an open trigger guard."""
    grip = g.contoured(
        "Grip",
        [(-0.13, -0.045), (-0.085, -0.045), (-0.112, -0.17), (-0.126, -0.193), (-0.168, -0.183)],
        0.038,
        grey,
        roll=0.011,
    )
    pieces = [
        grip,
        g.slab("GripCap", [(-0.167, -0.18), (-0.124, -0.19), (-0.125, -0.20), (-0.173, -0.189)], 0.041, black),
        g.slab(
            "TriggerGuard",
            [
                (-0.09, -0.05),
                (-0.014, -0.05),
                (-0.012, -0.105),
                (-0.103, -0.105),
                (-0.105, -0.095),
                (-0.022, -0.095),
                (-0.024, -0.05),
            ],
            0.014,
            black,
            bevel=0.0015,
        ),
        g.slab(
            "Trigger",
            [(-0.061, -0.05), (-0.052, -0.05), (-0.055, -0.075), (-0.069, -0.087), (-0.074, -0.08), (-0.063, -0.069)],
            0.007,
            metal,
        ),
    ]
    for side in (-1, 1):
        for i in range(4):
            y, z = -0.124 - i * 0.006, -0.085 - i * 0.021
            pieces.append(
                g.slab(
                    "GripRib",
                    g.rounded(y - 0.012, z - 0.004, y + 0.018, z + 0.004, 0.002),
                    0.003,
                    black,
                    x=side * 0.019,
                )
            )
    m.join_into(receiver, pieces)


def stock_parts(m, receiver, metal, black, grey):
    """Adjustable skeletal stock with a polymer cheek rest and rubber shoulder pad."""
    stock = g.slab(
        "Stock", [(-0.33, 0.073), (-0.356, 0.063), (-0.356, -0.102), (-0.33, -0.108)], 0.055, black, bevel=0.005
    )
    pieces = [
        g.slab(
            "StockRail", [(-0.334, 0.052), (-0.175, 0.048), (-0.175, 0.026), (-0.334, 0.027)], 0.025, metal, bevel=0.002
        ),
        g.slab(
            "StockBrace",
            [(-0.334, -0.065), (-0.188, -0.012), (-0.178, -0.03), (-0.334, -0.09)],
            0.023,
            metal,
            bevel=0.002,
        ),
        g.contoured("CheekRest", g.rounded(-0.329, 0.052, -0.238, 0.073, 0.005), 0.046, grey, roll=0.008),
        g.contoured(
            "ButtPad", [(-0.355, 0.064), (-0.367, 0.057), (-0.367, -0.10), (-0.355, -0.104)], 0.06, black, roll=0.006
        ),
    ]
    m.join_into(stock, pieces)
    m.attach(stock, (0, -0.19, 0.037), receiver)


def containment_cage(m, receiver, metal, black, grey, green):
    """Hollow collars and four struts reveal the contained Fenlight behind the emitter throat."""
    chamber = g.lathe(
        "Emitter", [(0.06, 0.145), (0.069, 0.16), (0.069, 0.185), (0.06, 0.196)], (0, 0, BORE_Z), grey, 24
    )
    front = g.lathe(
        "FrontCollar", [(0.061, 0.36), (0.073, 0.37), (0.073, 0.397), (0.058, 0.409)], (0, 0, BORE_Z), metal, 24
    )
    g.cut(front, [g.lathe("FrontOpening", [(0.044, 0.35), (0.044, 0.42)], (0, 0, BORE_Z), black, 24)])
    pieces = [front]
    for i in range(4):
        angle = math.pi / 4 + i * math.pi / 2
        x, z = 0.057 * math.cos(angle), BORE_Z + 0.057 * math.sin(angle)
        pieces.append(g.lathe("CageStrut", [(0.009, 0.18), (0.009, 0.375)], (x, 0, z), black, 8))
        for y in (0.21, 0.33):
            pieces.append(g.lathe("Clamp", [(0.012, y), (0.012, y + 0.013)], (x, 0, z), metal, 8))
    throat = g.lathe(
        "Throat", [(0.036, 0.39), (0.036, 0.47), (0.05, 0.49), (0.05, 0.53), (0.045, 0.54)], (0, 0, BORE_Z), black, 24
    )
    g.cut(throat, [g.lathe("Bore", [(0.028, 0.38), (0.028, 0.55)], (0, 0, BORE_Z), metal, 24)])
    pieces.append(throat)
    for y in (0.427, 0.455, 0.49):
        fin = g.lathe("InductionRing", [(0.046, y), (0.046, y + 0.012)], (0, 0, BORE_Z), metal, 24)
        g.cut(fin, [g.lathe("RingCore", [(0.035, y - 0.002), (0.035, y + 0.014)], (0, 0, BORE_Z), black, 24)])
        pieces.append(fin)
    m.join_into(chamber, pieces)
    m.attach(chamber, (0, 0.173, BORE_Z), receiver)
    core = g.lathe("Core", [(0.022, 0.195), (0.032, 0.215), (0.032, 0.34), (0.022, 0.36)], (0, 0, BORE_Z), green, 24)
    m.attach(core, (0, 0.275, BORE_Z), receiver)
    m.marker("Muzzle", (0, 0.545, BORE_Z), receiver)


def controls(m, receiver, metal, black, grey, green):
    """Three-charge cassette, reciprocating service latch and a clear iron-sight line."""
    magazine = g.slab(
        "Magazine", [(-0.033, -0.06), (0.068, -0.06), (0.074, -0.174), (-0.027, -0.174)], 0.059, grey, bevel=0.004
    )
    pieces = [g.slab("CassetteBase", g.rounded(-0.033, -0.187, 0.08, -0.169, 0.004), 0.066, black, bevel=0.002)]
    for side in (-1, 1):
        for i in range(3):
            y = -0.016 + i * 0.031
            pieces.append(
                g.slab("ChargeWindow", g.rounded(y, -0.15, y + 0.011, -0.09, 0.004), 0.002, green, x=side * 0.030)
            )
    m.join_into(magazine, pieces)
    m.attach(magazine, (0, 0.022, -0.06), receiver)
    bolt = g.slab("Bolt", g.rounded(-0.106, 0.022, 0.025, 0.048, 0.005), 0.004, metal, x=0.030)
    handle = g.lathe(
        "LatchHandle",
        [(0.007, 0.03), (0.007, 0.052), (0.01, 0.055), (0.01, 0.065)],
        (0, -0.055, 0.035),
        black,
        12,
        axis="x",
    )
    m.join_into(bolt, [handle])
    m.attach(bolt, (0.031, -0.042, 0.035), receiver)
    sights = []
    for side in (-1, 1):
        sights.append(
            g.slab(
                "RearSightEar", g.rounded(-0.098, 0.111, -0.079, SIGHT_Z + 0.009, 0.003), 0.005, black, x=side * 0.011
            )
        )
        sights.append(
            g.slab(
                "FrontSightEar",
                [(0.355, 0.09), (0.377, 0.09), (0.372, SIGHT_Z + 0.009), (0.362, SIGHT_Z + 0.009)],
                0.004,
                black,
                x=side * 0.013,
            )
        )
    sights += [
        g.slab("RearSightBridge", g.rounded(-0.098, SIGHT_Z + 0.007, -0.079, SIGHT_Z + 0.012, 0.002), 0.026, black),
        g.slab("FrontPost", [(0.363, 0.10), (0.369, 0.10), (0.367, SIGHT_Z), (0.365, SIGHT_Z)], 0.003, metal),
    ]
    m.join_into(receiver, sights)
    g.add_inlays(m, receiver, g.rounded(-0.15, 0.07, 0.11, 0.072, 0.0008), 0.001, 0.039, metal)


def build(m) -> None:
    """Assemble the fixed Prototype using the shared gun finish palette and runtime pivots."""
    metal = m.material("GunMetal", m.GUN_METAL, metallic=0.8, roughness=0.4)
    black = m.material("MatteBlack", m.MATTE_BLACK, roughness=0.75)
    grey = m.material("GreyPolymer", m.srgb("#5F6D68"), roughness=0.85)
    green = m.material("OpticGlass", m.srgb("#8DFF3A"), roughness=0.4)
    receiver, parts = receiver_parts(metal, black, grey)
    m.join_into(receiver, parts)
    grip_parts(m, receiver, metal, black, grey)
    stock_parts(m, receiver, metal, black, grey)
    containment_cage(m, receiver, metal, black, grey, green)
    controls(m, receiver, metal, black, grey, green)
    g.stamp(m, "siphon", "Receiver", (-0.039, -0.085, 0.019), 0.085)
