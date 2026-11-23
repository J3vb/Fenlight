"""Mako PDW: compact burst PDW with a sloped polymer body, 40-round magazine and rod stock.

Static parts join into `Receiver`. Code and tests need `Magazine`, `Bolt` (with
`ChargingHandle`), `Stock`, `IronSights`, `Foregrip`, `Trigger` and the `Muzzle` marker.
"""

import math

import gun_parts as g

BORE_Z = 0.02
SIGHT_Z = 0.068


def body(metal, black, tan):
    """Black upper with rail and port over a tan lower that sweeps forward into the handguard."""
    parts = [
        g.slab(
            "Upper",
            [(-0.13, 0.0), (0.13, 0.0), (0.13, 0.042), (0.11, 0.046), (-0.115, 0.046), (-0.13, 0.034)],
            0.046,
            black,
            bevel=0.002,
        ),
        g.slab("RailBase", [(-0.115, 0.046), (0.125, 0.046), (0.125, 0.05), (-0.115, 0.05)], 0.024, black),
        g.slab("RailTeeth", g.teeth(-0.11, 0.12, 0.05, 0.057), 0.021, black),
        g.slab(
            "Lower",
            [
                (-0.13, 0.002),
                (0.215, 0.002),
                (0.235, -0.006),
                (0.235, -0.028),
                (0.09, -0.034),
                (0.085, -0.05),
                (0.012, -0.05),
                (0.008, -0.04),
                (-0.1, -0.04),
                (-0.13, -0.022),
            ],
            0.05,
            tan,
            bevel=0.003,
        ),
        handguard(metal, tan),
        g.slab(
            "WellLip", [(0.008, -0.044), (0.09, -0.044), (0.092, -0.056), (0.006, -0.056)], 0.046, black, bevel=0.0015
        ),
        g.lathe("Selector", [(0.008, -0.027), (0.008, -0.023)], (0, -0.085, -0.02), metal, 12, axis="x"),
        g.lathe("MagRelease", [(0.006, 0.025), (0.006, 0.03)], (0, 0.0, -0.03), metal, 12, axis="x"),
    ]
    for x in (-1, 1):
        parts.append(g.slab(f"BodyPanel{x}", g.rounded(-0.1, -0.034, -0.02, -0.01, 0.005), 0.002, black, x=x * 0.0255))
        for y, z in ((-0.115, 0.02), (0.11, 0.02), (-0.06, -0.025), (0.06, -0.02)):
            parts.append(
                g.lathe(f"Pin{x}{y}", [(0.0035, -0.0015), (0.0035, 0.0015)], (x * 0.026, y, z), metal, 10, axis="x")
            )
    cut_port(parts[0], metal)
    return parts


def cut_port(part, metal):
    """Recess each closed receiver layer before the static parts are joined."""
    g.cut(part, [g.slab("EjectionPocket", g.rounded(-0.04, 0.008, 0.035, 0.034, 0.004), 0.024, metal, x=0.028)])


def handguard(metal, tan):
    """A ventilated polymer shell with wall thickness and a separate inner barrel."""
    shroud = g.lathe(
        "Handguard",
        [(0.024, 0.13), (0.027, 0.135), (0.027, 0.235), (0.024, 0.24)],
        (0, 0, BORE_Z),
        tan,
        8,
        turn=math.pi / 8,
    )
    cutters = [g.lathe("ShroudCore", [(0.020, 0.128), (0.020, 0.242)], (0, 0, BORE_Z), metal, 16)]
    for i in range(3):
        y = 0.145 + i * 0.03
        cutters.append(g.slab(f"Vent{i}", g.rounded(y, 0.012, y + 0.02, 0.028, 0.005), 0.07, metal))
    g.cut(shroud, cutters)
    return shroud


def lower_parts(black, tan):
    """Pistol grip with finger grooves and an integral trigger guard."""
    grip = [
        (-0.083, -0.04),
        (-0.118, -0.04),
        (-0.16, -0.148),
        (-0.156, -0.162),
        (-0.124, -0.162),
        (-0.116, -0.148),
        (-0.112, -0.128),
        (-0.104, -0.116),
        (-0.1, -0.098),
        (-0.092, -0.084),
        (-0.088, -0.066),
    ]
    guard = [
        (0.006, -0.04),
        (0.006, -0.07),
        (-0.072, -0.07),
        (-0.088, -0.04),
        (-0.08, -0.04),
        (-0.068, -0.063),
        (-0.001, -0.063),
        (-0.001, -0.04),
    ]
    return [
        g.contoured("Grip", grip, 0.032, tan, roll=0.011),
        g.slab("GripCap", [(-0.124, -0.158), (-0.157, -0.158), (-0.158, -0.167), (-0.123, -0.167)], 0.034, black),
        g.slab("TriggerGuard", guard, 0.012, black, bevel=0.0015),
    ]


def front_parts(m, receiver, metal, black, tan):
    """Short barrel with a three-prong flash hider, sights on the rail and an angled foregrip."""
    barrel = g.lathe(
        "Barrel",
        [(0.011, 0.235), (0.011, 0.25), (0.009, 0.253), (0.009, 0.3), (0.0105, 0.302), (0.0105, 0.31)],
        (0, 0, BORE_Z),
        metal,
        16,
    )
    hider = g.lathe("Hider", [(0.012, 0.31), (0.013, 0.314), (0.013, 0.345), (0.011, 0.349)], (0, 0, BORE_Z), black, 16)
    g.cut(barrel, [g.lathe("Bore", [(0.006, 0.275), (0.006, 0.351)], (0, 0, BORE_Z), black, 16)])
    cutters = [g.lathe("Bore", [(0.006, 0.275), (0.006, 0.351)], (0, 0, BORE_Z), black, 16)]
    for i in range(3):
        slot = g.slab(f"ProngGap{i}", g.rounded(0.322, -0.0025, 0.351, 0.0025, 0.002), 0.02, black, x=0.01)
        slot.rotation_euler = (0.0, i * 2 * math.pi / 3, 0.0)
        slot.location = (0.0, 0.0, BORE_Z)
        cutters.append(slot)
    g.cut(hider, cutters)
    m.join_into(barrel, [hider, g.lathe("InnerBarrel", [(0.009, 0.13), (0.009, 0.24)], (0, 0, BORE_Z), metal, 16)])
    m.attach(barrel, (0, 0.24, BORE_Z), receiver)
    sights = g.slab(
        "IronSights",
        [
            (-0.105, 0.057),
            (-0.075, 0.057),
            (-0.075, 0.062),
            (-0.082, 0.062),
            (-0.088, 0.058),
            (-0.098, 0.058),
            (-0.105, 0.062),
        ],
        0.024,
        black,
    )
    pieces = []
    for x in (-1, 1):
        pieces += [
            g.slab(
                f"RearEar{x}",
                [(-0.098, 0.057), (-0.088, 0.057), (-0.088, 0.08), (-0.098, 0.08)],
                0.004,
                black,
                x=x * 0.0065,
            ),
            g.slab(
                f"FrontEar{x}",
                [(0.098, 0.057), (0.118, 0.057), (0.114, 0.078), (0.102, 0.078)],
                0.003,
                black,
                x=x * 0.008,
            ),
        ]
    pieces += [
        g.slab("RearBridge", [(-0.098, 0.08), (-0.088, 0.08), (-0.088, 0.084), (-0.098, 0.084)], 0.017, black),
        g.slab("FrontBase", [(0.096, 0.057), (0.12, 0.057), (0.12, 0.061), (0.096, 0.061)], 0.022, black),
        g.slab("FrontPost", [(0.105, 0.06), (0.111, 0.06), (0.11, SIGHT_Z), (0.106, SIGHT_Z)], 0.003, metal),
    ]
    m.join_into(sights, pieces)
    m.attach(sights, (0, -0.093, 0.057), receiver)
    foregrip = g.contoured(
        "Foregrip",
        [(0.15, -0.006), (0.215, -0.006), (0.21, -0.022), (0.175, -0.07), (0.158, -0.074), (0.15, -0.064)],
        0.03,
        tan,
        roll=0.009,
    )
    m.attach(foregrip, (0, 0.18, -0.006), receiver)
    m.marker("Muzzle", (0, 0.35, BORE_Z), parent=receiver)


def stock_parts(m, receiver, metal, black):
    """Two-rod collapsible stock with a rubber butt pad and cheek rest."""
    butt = g.slab(
        "Stock",
        [(-0.31, 0.038), (-0.33, 0.04), (-0.338, -0.085), (-0.322, -0.09), (-0.31, -0.06)],
        0.042,
        black,
        bevel=0.004,
    )
    pieces = [
        g.contoured(
            "ButtPad", [(-0.333, 0.038), (-0.343, 0.038), (-0.346, -0.084), (-0.336, -0.088)], 0.046, black, roll=0.006
        )
    ]
    for x in (-1, 1):
        pieces.append(g.lathe(f"Rod{x}", [(0.0055, -0.31), (0.0055, -0.125)], (x * 0.016, 0, 0.022), metal, 10))
    pieces.append(g.lathe("RodLow", [(0.006, -0.31), (0.006, -0.125)], (0, 0, -0.022), metal, 10))
    pieces.append(g.contoured("CheekRest", g.rounded(-0.31, 0.03, -0.24, 0.042, 0.005), 0.04, black, roll=0.008))
    m.join_into(butt, pieces)
    m.attach(butt, (0, -0.13, 0.0), receiver)


def moving_parts(m, receiver, metal, black, tan):
    """Magazine pivots at its feed lips; the left-side charging handle rides with the bolt."""
    magazine = g.slab(
        "Magazine",
        [(0.016, -0.05), (0.082, -0.05), (0.094, -0.22), (0.032, -0.222)],
        0.034,
        black,
        bevel=0.002,
    )
    pieces = [
        g.slab("MagBase", [(0.028, -0.218), (0.1, -0.216), (0.101, -0.23), (0.027, -0.232)], 0.04, tan, bevel=0.002),
    ]
    for x in (-1, 1):
        pieces.append(g.slab(f"MagWindow{x}", g.rounded(0.04, -0.2, 0.05, -0.07, 0.004), 0.002, tan, x=x * 0.0172))
    m.join_into(magazine, pieces)
    m.attach(magazine, (0, 0.05, -0.05), receiver)
    bolt = g.slab("Bolt", g.rounded(-0.03, 0.012, 0.025, 0.03, 0.003), 0.002, metal, x=0.0185)
    m.attach(bolt, (0.0245, 0.0, 0.021), receiver)
    knob = [(0.004, 0.024), (0.004, 0.04), (0.007, 0.042), (0.007, 0.052), (0.005, 0.054)]
    handle = g.lathe("ChargingHandle", knob, (0, 0.012, 0.022), black, 12, axis="x")
    m.attach(handle, (0.03, 0.012, 0.022), bolt)
    trigger = g.slab(
        "Trigger",
        [(-0.044, -0.04), (-0.038, -0.04), (-0.04, -0.052), (-0.047, -0.062), (-0.052, -0.06), (-0.046, -0.051)],
        0.006,
        metal,
    )
    m.attach(trigger, (0, -0.041, -0.042), receiver)


def build(m) -> None:
    """Build from shared helpers supplied by build_models, keeping the runtime part names."""
    metal = m.material("GunMetal", m.GUN_METAL, metallic=0.8, roughness=0.4)
    black = m.material("MatteBlack", m.MATTE_BLACK, roughness=0.75)
    tan = m.material("Tan", m.TAN, roughness=0.8)
    receiver = g.slab(
        "Receiver", [(-0.12, 0.004), (0.12, 0.004), (0.12, 0.04), (-0.12, 0.04)], 0.04, metal, bevel=0.001
    )
    cut_port(receiver, metal)
    m.join_into(receiver, body(metal, black, tan) + lower_parts(black, tan))
    front_parts(m, receiver, metal, black, tan)
    stock_parts(m, receiver, metal, black)
    moving_parts(m, receiver, metal, black, tan)
    g.add_inlays(m, receiver, g.rounded(-0.105, 0.039, 0.105, 0.041, 0.0008), 0.0006, 0.023, metal)
    g.stamp(m, "mako_pdw", "Receiver", (-0.023, -0.085, 0.019), 0.085)
