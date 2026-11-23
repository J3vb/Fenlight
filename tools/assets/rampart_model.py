"""Rampart BR: a slab-sided battle rifle, fixed stock and short twenty-round magazine.

The thick ventilated handguard, exposed gas block and square brake give the
heavy rifle a silhouette distinct from the lighter burst rifles and SMGs.
"""

import gun_parts as g

BORE_Z = 0.025
SIGHT_Z = 0.105


def receiver_parts(m, metal, black, polymer):
    """Stepped receiver with a recessed right-side ejection pocket and a flared well."""
    receiver = g.slab(
        "Receiver",
        [(-0.2, -0.014), (0.15, -0.014), (0.15, 0.052), (0.12, 0.06), (-0.18, 0.06), (-0.2, 0.038)],
        0.062,
        metal,
        bevel=0.0025,
    )
    g.cut(receiver, [g.slab("EjectionPocket", g.rounded(-0.055, 0.008, 0.065, 0.043, 0.005), 0.028, black, x=0.033)])
    lower = g.slab(
        "Lower",
        [
            (-0.19, -0.012),
            (0.145, -0.012),
            (0.14, -0.065),
            (0.12, -0.074),
            (0.012, -0.074),
            (-0.005, -0.047),
            (-0.17, -0.047),
            (-0.19, -0.032),
        ],
        0.056,
        black,
        bevel=0.002,
    )
    parts = [lower, g.slab("WellRim", g.rounded(0.008, -0.08, 0.144, -0.066, 0.003), 0.062, black, bevel=0.001)]
    parts.extend(receiver_details(metal, black, polymer))
    m.join_into(receiver, parts)
    return receiver


def receiver_details(metal, black, polymer):
    """Bilateral inlays and receiver controls remain crisp at inspection distance."""
    parts = []
    for side in (-1, 1):
        for y, z in ((-0.166, 0.017), (0.122, 0.018), (-0.13, -0.028)):
            parts.append(
                g.lathe("ReceiverPin", [(0.0045, -0.002), (0.0045, 0.002)], (side * 0.031, y, z), black, 12, axis="x")
            )
        parts.append(
            g.slab(
                "LowerPanel",
                g.rounded(-0.157, -0.038, -0.067, -0.017, 0.006),
                0.002,
                polymer,
                x=side * 0.0285,
                bevel=0.0,
            )
        )
    parts.append(g.lathe("SafetyHub", [(0.009, -0.034), (0.009, -0.028)], (0, -0.12, -0.024), metal, 16, axis="x"))
    parts.append(
        g.slab(
            "SafetyLever",
            [(-0.126, -0.026), (-0.094, -0.01), (-0.091, -0.016), (-0.119, -0.033)],
            0.003,
            black,
            x=-0.036,
            bevel=0.001,
        )
    )
    return parts


def grip(m, receiver, black, polymer):
    """Broad pistol grip with grip panels and an open trigger guard."""
    grip = g.contoured(
        "Grip",
        [
            (-0.105, -0.045),
            (-0.145, -0.043),
            (-0.2, -0.167),
            (-0.193, -0.182),
            (-0.156, -0.182),
            (-0.144, -0.163),
            (-0.137, -0.135),
            (-0.124, -0.112),
            (-0.118, -0.083),
        ],
        0.036,
        polymer,
        roll=0.011,
    )
    pieces = [
        g.slab("GripCap", g.rounded(-0.2, -0.187, -0.152, -0.174, 0.004), 0.04, black, bevel=0.001),
        trigger_guard(black),
    ]
    knurled = m.material("GunMetalKnurled", m.GUN_METAL, metallic=0.8, roughness=0.5)
    for side in (-1, 1):
        pieces.append(
            g.slab(
                "GripPanel",
                [(-0.141, -0.068), (-0.181, -0.161), (-0.16, -0.169), (-0.131, -0.102)],
                0.0015,
                knurled,
                x=side * 0.0185,
                bevel=0.0,
            )
        )
    m.join_into(grip, pieces)
    m.attach(grip, (0, -0.125, -0.045), receiver)


def trigger_guard(black):
    """The open guard shell leaves a clear opening around the separate trigger."""
    return g.slab(
        "TriggerGuard",
        [
            (-0.113, -0.045),
            (-0.102, -0.088),
            (0.006, -0.088),
            (0.012, -0.049),
            (0.003, -0.049),
            (-0.003, -0.078),
            (-0.096, -0.078),
            (-0.104, -0.045),
        ],
        0.014,
        black,
        bevel=0.0015,
    )


def stock(m, receiver, black, polymer):
    """Deep fixed buttstock with a raised cheek saddle, recessed panels and rubber pad."""
    butt = g.slab(
        "Stock",
        [
            (-0.195, 0.039),
            (-0.43, 0.047),
            (-0.48, 0.034),
            (-0.483, -0.107),
            (-0.45, -0.113),
            (-0.325, -0.057),
            (-0.27, -0.028),
            (-0.195, -0.025),
        ],
        0.051,
        polymer,
        bevel=0.004,
    )
    cuts = [
        g.slab("StockPocket", g.rounded(-0.434, -0.043, -0.304, -0.008, 0.008), 0.017, black, x=side * 0.027)
        for side in (-1, 1)
    ]
    g.cut(butt, cuts)
    pad = g.contoured(
        "ButtPad",
        [(-0.478, 0.038), (-0.493, 0.037), (-0.498, -0.109), (-0.483, -0.115), (-0.475, -0.104)],
        0.057,
        black,
        roll=0.006,
    )
    cheek = g.contoured("CheekRest", g.rounded(-0.423, 0.035, -0.24, 0.058, 0.008), 0.048, black, roll=0.008)
    parts = [pad, cheek]
    for z in (-0.084, -0.034, 0.016):
        parts.append(g.slab("PadRib", g.rounded(-0.497, z, -0.492, z + 0.007, 0.002), 0.059, black))
    for side in (-1, 1):
        loop = g.lathe(
            "SlingSocket", [(0.009, -0.002), (0.009, 0.002)], (side * 0.027, -0.441, -0.055), black, 16, axis="x"
        )
        parts.append(loop)
    m.join_into(butt, parts)
    m.attach(butt, (0, -0.195, 0), receiver)


def handguard(m, receiver, metal, black, polymer):
    """Boxy ventilated shell with a visible inner barrel and underside finger ribs."""
    shell = g.slab(
        "Handguard",
        [(0.145, -0.02), (0.408, -0.02), (0.42, -0.005), (0.42, 0.054), (0.405, 0.062), (0.145, 0.062)],
        0.069,
        polymer,
        bevel=0.0025,
    )
    cuts = [g.slab("HandguardCore", [(0.142, -0.009), (0.425, -0.009), (0.425, 0.049), (0.142, 0.049)], 0.051, black)]
    for y in (0.175, 0.226, 0.277, 0.328, 0.379):
        cuts.append(g.slab("Vent", g.rounded(y, 0.022, y + 0.026, 0.043, 0.005), 0.09, black))
    g.cut(shell, cuts)
    pieces = [
        g.slab("RailBase", g.rounded(-0.18, 0.06, 0.412, 0.066, 0.002), 0.025, black),
        g.slab("RailTeeth", g.teeth(-0.175, 0.41, 0.066, 0.074, pitch=0.017), 0.024, black),
    ]
    for y in (0.174, 0.234, 0.294, 0.354):
        pieces.append(g.slab("GripRib", g.rounded(y, -0.025, y + 0.017, -0.015, 0.003), 0.073, black))
    m.join_into(shell, pieces)
    m.attach(shell, (0, 0.145, BORE_Z), receiver)
    barrel = g.lathe(
        "Barrel",
        [(0.011, 0.14), (0.011, 0.43), (0.014, 0.433), (0.014, 0.451), (0.011, 0.455), (0.011, 0.576)],
        (0, 0, BORE_Z),
        metal,
        20,
    )
    g.cut(barrel, [g.lathe("BoreCut", [(0.0047, 0.54), (0.0047, 0.58)], (0, 0, BORE_Z), black, 16)])
    m.attach(barrel, (0, 0.43, BORE_Z), receiver)
    gas = g.lathe("GasTube", [(0.006, 0.145), (0.006, 0.46)], (0, 0, 0.046), black, 12)
    block = g.slab("GasBlock", g.rounded(0.435, 0.012, 0.458, 0.065, 0.005), 0.033, black, bevel=0.001)
    m.join_into(barrel, [gas, block])
    return barrel


def brake_and_sights(m, receiver, barrel, metal, black):
    """Ported square brake, protected front blade and a functional rear aperture."""
    brake = g.slab(
        "MuzzleBrake", g.rounded(0.572, BORE_Z - 0.02, 0.638, BORE_Z + 0.02, 0.004), 0.036, metal, bevel=0.001
    )
    cuts = [g.lathe("BrakeBore", [(0.0047, 0.57), (0.0047, 0.642)], (0, 0, BORE_Z), black, 16)]
    for y in (0.584, 0.609):
        cuts.append(g.slab("BrakePort", g.rounded(y, BORE_Z - 0.005, y + 0.014, BORE_Z + 0.005, 0.002), 0.05, black))
    g.cut(brake, cuts)
    m.attach(brake, (0, 0.572, BORE_Z), barrel)
    sights = g.slab("IronSights", g.rounded(-0.167, 0.074, -0.13, 0.082, 0.003), 0.036, black, bevel=0.001)
    aperture = g.lathe("RearAperture", [(0.013, -0.154), (0.013, -0.145)], (0, 0, SIGHT_Z), black, 24)
    g.cut(aperture, [g.lathe("Peep", [(0.0045, -0.157), (0.0045, -0.142)], (0, 0, SIGHT_Z), metal, 16)])
    pieces = [
        aperture,
        g.slab("RearPedestal", g.rounded(-0.16, 0.08, -0.14, 0.096, 0.002), 0.018, black),
        g.slab("FrontPost", [(0.443, 0.064), (0.451, 0.064), (0.449, SIGHT_Z), (0.445, SIGHT_Z)], 0.004, metal),
    ]
    for side in (-1, 1):
        pieces.append(
            g.slab(
                "FrontEar",
                [(0.435, 0.06), (0.459, 0.06), (0.455, 0.116), (0.439, 0.116)],
                0.004,
                black,
                x=side * 0.012,
                bevel=0.001,
            )
        )
    m.join_into(sights, pieces)
    m.attach(sights, (0, -0.15, 0.074), receiver)
    m.marker("Muzzle", (0, 0.64, BORE_Z), parent=receiver)


def moving_parts(m, receiver, metal, black):
    """A broad short magazine and bolt face sitting inside the machined receiver pocket."""
    magazine = g.slab(
        "Magazine",
        [(0.019, -0.069), (0.127, -0.069), (0.132, -0.185), (0.116, -0.195), (0.025, -0.195)],
        0.041,
        metal,
        bevel=0.002,
    )
    parts = [g.slab("MagBase", g.rounded(0.02, -0.203, 0.138, -0.19, 0.003), 0.046, black, bevel=0.001)]
    for side in (-1, 1):
        for y in (0.038, 0.066, 0.094):
            parts.append(
                g.slab(
                    "MagRib", g.rounded(y, -0.181, y + 0.007, -0.086, 0.003), 0.002, black, x=side * 0.021, bevel=0.0
                )
            )
    m.join_into(magazine, parts)
    m.attach(magazine, (0, 0.075, -0.07), receiver)
    bolt = g.slab("Bolt", g.rounded(-0.046, 0.013, 0.053, 0.037, 0.004), 0.002, metal, x=0.021)
    m.attach(bolt, (0.021, 0.004, 0.025), receiver)
    handle = g.lathe(
        "ChargingHandle",
        [(0.0045, 0.021), (0.0045, 0.041), (0.008, 0.043), (0.008, 0.059), (0.006, 0.062)],
        (0, 0.031, 0.026),
        black,
        16,
        axis="x",
    )
    m.attach(handle, (0.03, 0.031, 0.026), bolt)
    trigger = g.slab(
        "Trigger",
        [(-0.071, -0.047), (-0.064, -0.047), (-0.066, -0.063), (-0.079, -0.075), (-0.086, -0.07), (-0.074, -0.06)],
        0.007,
        metal,
        bevel=0.0007,
    )
    m.attach(trigger, (0, -0.068, -0.047), receiver)


def build(m) -> None:
    """Build the original heavy rifle using the shared gun geometry and finish pipeline."""
    metal = m.material("GunMetal", m.GUN_METAL, metallic=0.8, roughness=0.4)
    black = m.material("MatteBlack", m.MATTE_BLACK, roughness=0.75)
    polymer = m.material("OlivePolymer", m.srgb("#5F6D68"), roughness=0.8)
    receiver = receiver_parts(m, metal, black, polymer)
    grip(m, receiver, black, polymer)
    stock(m, receiver, black, polymer)
    barrel = handguard(m, receiver, metal, black, polymer)
    brake_and_sights(m, receiver, barrel, metal, black)
    moving_parts(m, receiver, metal, black)
    g.add_inlays(m, receiver, g.rounded(-0.166, 0.048, 0.105, 0.051, 0.001), 0.001, 0.0312, metal)
    g.stamp(m, "rampart_br", "Receiver", (-0.031, -0.085, 0.019), 0.085)
