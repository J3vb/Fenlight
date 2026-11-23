"""AR-17 rifle: tan skeleton stock and grip, black quad-rail handguard, birdcage hider, taped mag, Oriel red dot.

Static parts join into `Receiver`. `Magazine`, `Bolt`, `Barrel` (with `MuzzleBrake`),
`SightGlass` and the `ReticleMount` marker stay separate nodes for code. Gun forward is Blender +Y.
Worn materials and the `Markings` atlas follow docs/plans/guns-concept.md.
"""

import math

import gun_parts as g

AXIS_Z = 0.016  # barrel and handguard centre height
EYE_Z = 0.09  # aim line: WeaponData.ads_position.y is -EYE_Z
RAIL_TOP = 0.059


def upper(m, metal, black):
    """Flat-top upper with a recessed ejection port, brass deflector and full-length rail."""
    receiver = g.slab(
        "Receiver",
        [(-0.17, -0.004), (0.17, -0.004), (0.17, 0.046), (-0.152, 0.046), (-0.17, 0.034)],
        0.05,
        black,
        bevel=0.002,
    )
    g.cut(receiver, [g.slab("PortCut", g.rounded(-0.03, 0.002, 0.065, 0.034, 0.004), 0.018, black, x=0.028)])
    parts = [
        g.slab("RailBase", [(-0.168, 0.046), (0.475, 0.046), (0.475, 0.051), (-0.168, 0.051)], 0.024, black),
        g.slab("RailTeeth", g.teeth(-0.165, 0.47, 0.051, 0.059), 0.021, black),
        g.slab(
            "Deflector",
            [(-0.07, 0.0), (-0.035, 0.0), (-0.035, 0.03), (-0.05, 0.042), (-0.07, 0.042)],
            0.008,
            metal,
            x=0.027,
            bevel=0.002,
        ),
        g.lathe("DustCoverHinge", [(0.002, -0.03), (0.002, 0.065)], (0.026, 0, 0.001), black, 10),
        g.lathe(
            "ForwardAssist",
            [(0.009, -0.11), (0.009, -0.07), (0.0065, -0.065), (0.0065, -0.05)],
            (0.03, 0.0, 0.028),
            metal,
            segments=16,
        ),
        g.slab("BoltRelease", [(-0.13, 0.0), (-0.1, 0.0), (-0.1, 0.012), (-0.13, 0.018)], 0.004, metal, x=-0.027),
        g.slab(
            "ChargeHandle",
            [(-0.205, 0.035), (-0.165, 0.035), (-0.165, 0.046), (-0.205, 0.046)],
            0.036,
            black,
            bevel=0.002,
        ),
        g.slab("ChargeLatch", [(-0.2, 0.035), (-0.178, 0.035), (-0.175, 0.045), (-0.2, 0.046)], 0.008, black, x=-0.022),
    ]
    for x in (-1, 1):
        parts.append(g.lathe(f"ChargeWing{x}", [(0.006, -0.205), (0.006, -0.185)], (x * 0.022, 0.0, 0.04), black, 8))
    m.join_into(receiver, parts)
    return receiver


def lower(m, metal, black, tan):
    """Lower with flared mag well, trigger guard, trigger, tan finger-groove grip, selector and pins."""
    grip = [
        (-0.09, -0.048),
        (-0.124, -0.048),
        (-0.134, -0.06),
        (-0.17, -0.152),
        (-0.166, -0.168),
        (-0.128, -0.168),
        (-0.119, -0.154),
        (-0.118, -0.136),
        (-0.109, -0.126),
        (-0.108, -0.106),
        (-0.099, -0.096),
        (-0.098, -0.08),
        (-0.091, -0.07),
    ]
    guard = [
        (0.016, -0.05),
        (0.016, -0.086),
        (-0.082, -0.086),
        (-0.096, -0.05),
        (-0.088, -0.05),
        (-0.077, -0.079),
        (0.009, -0.079),
        (0.009, -0.05),
    ]
    parts = [
        g.slab(
            "Lower",
            [
                (-0.168, -0.004),
                (0.122, -0.004),
                (0.122, -0.026),
                (0.114, -0.09),
                (0.02, -0.09),
                (0.016, -0.05),
                (-0.13, -0.05),
                (-0.168, -0.028),
            ],
            0.046,
            black,
            bevel=0.002,
        ),
        g.slab(
            "WellFlare", [(0.018, -0.084), (0.118, -0.084), (0.12, -0.094), (0.016, -0.094)], 0.05, black, bevel=0.002
        ),
        g.slab("Grip", grip, 0.032, tan, bevel=0.005),
        g.slab("TriggerGuard", guard, 0.012, black, bevel=0.0015),
        g.slab(
            "Trigger",
            [(-0.035, -0.05), (-0.029, -0.05), (-0.031, -0.064), (-0.039, -0.076), (-0.044, -0.073), (-0.037, -0.063)],
            0.006,
            metal,
        ),
        g.lathe("MagRelease", [(0.007, 0.024), (0.007, 0.03)], (0.0, 0.03, -0.03), metal, 12, axis="x"),
    ]
    for side in (-1, 1):
        parts.append(
            g.slab(
                f"GripPanel{side}",
                [(-0.122, -0.064), (-0.156, -0.144), (-0.14, -0.158), (-0.114, -0.1), (-0.106, -0.074)],
                0.002,
                m.material("TanKnurledWorn", m.TAN, roughness=0.85),
                x=side * 0.0165,
            )
        )
        for y, z in ((-0.15, 0.0), (0.105, 0.0), (-0.045, -0.035), (-0.003, -0.035)):
            parts.append(
                g.lathe(f"Pin{side}{y}", [(0.004, -0.0015), (0.004, 0.0015)], (side * 0.024, y, z), metal, 10, axis="x")
            )
    parts.append(g.lathe("Selector", [(0.009, -0.004), (0.009, 0.0)], (-0.0235, -0.09, -0.028), metal, 12, axis="x"))
    parts.append(
        g.slab(
            "SelectorLever",
            [(-0.093, -0.03), (-0.068, -0.024), (-0.068, -0.02), (-0.09, -0.024)],
            0.003,
            metal,
            x=-0.028,
        )
    )
    return parts


def rail(name: str, y0: float, y1: float, angle: float, black):
    """A toothed rail section on one flat of the handguard, turned `angle` about the barrel axis."""
    part = g.slab(name, g.teeth(y0, y1, 0.0295, 0.04), 0.021, black)
    part.rotation_euler = (0.0, angle, 0.0)
    part.location = (0.0, 0.0, AXIS_Z)
    return part


def handguard(m, black):
    """Black quad-rail handguard: long side slots, rail sections at the front, flip-up front sight."""
    flat = math.pi / 8
    guard = g.lathe(
        "Handguard",
        [(0.03, 0.17), (0.033, 0.175), (0.033, 0.465), (0.03, 0.475)],
        (0, 0, AXIS_Z),
        black,
        8,
        turn=flat,
    )
    cuts = [g.lathe("GuardCore", [(0.025, 0.165), (0.025, 0.48)], (0, 0, AXIS_Z), black, 8, turn=flat)]
    for i in range(3):
        y = 0.2 + i * 0.062
        cuts.append(g.slab(f"SlotCut{i}", g.rounded(y, 0.008, y + 0.05, 0.024, 0.006), 0.08, black))
    g.cut(guard, cuts)
    sight = g.slab("FrontSight", [(0.432, 0.059), (0.472, 0.059), (0.47, 0.068), (0.436, 0.068)], 0.018, black)
    ears = []
    for side in (-1, 1):
        ear = g.slab(
            f"SightEar{side}",
            [(0.437, 0.066), (0.469, 0.066), (0.464, 0.104), (0.444, 0.104)],
            0.003,
            black,
            x=side * 0.0065,
        )
        g.cut(ear, [g.slab("EarWindow", g.rounded(0.447, 0.071, 0.461, 0.098, 0.004), 0.04, black)])
        ears.append(ear)
    parts = [
        guard,
        rail("RailBottom", 0.38, 0.46, math.pi, black),
        rail("RailLeft", 0.385, 0.46, -math.pi / 2, black),
        rail("RailRight", 0.385, 0.46, math.pi / 2, black),
        g.lathe("BarrelNut", [(0.026, 0.165), (0.026, 0.172)], (0, 0, AXIS_Z), black, 16),
        sight,
        *ears,
        g.lathe("SightPost", [(0.0016, 0.066), (0.0012, 0.084)], (0, 0.454, 0), black, 6, axis="z"),
        g.slab("SightHinge", [(0.462, 0.059), (0.474, 0.059), (0.474, 0.066), (0.462, 0.066)], 0.024, black),
        g.slab(
            "RearSight", [(-0.15, 0.059), (-0.12, 0.059), (-0.125, 0.068), (-0.15, 0.068)], 0.02, black, bevel=0.001
        ),
        g.lathe("InnerBarrel", [(0.009, 0.17), (0.009, 0.475)], (0, 0, AXIS_Z), black, 12),
    ]
    return parts


def stock(m, metal, black, tan):
    """Buffer tube, castle nut, tan skeleton stock with an open triangle, lever and rubber pad."""
    frame = g.slab(
        "Stock",
        [
            (-0.25, 0.038),
            (-0.3, 0.046),
            (-0.398, 0.048),
            (-0.402, -0.074),
            (-0.386, -0.084),
            (-0.372, -0.074),
            (-0.26, -0.008),
            (-0.25, 0.0),
        ],
        0.042,
        tan,
        bevel=0.004,
    )
    g.cut(
        frame,
        [
            g.slab("StockWindow", [(-0.29, -0.006), (-0.383, -0.006), (-0.383, -0.06)], 0.06, tan),
            g.slab("SlingSlot", g.rounded(-0.392, -0.06, -0.384, -0.03, 0.003), 0.06, tan),
        ],
    )
    return [
        g.lathe("BufferTube", [(0.0155, -0.17), (0.0155, -0.39)], (0, 0, 0.018), metal, 20),
        g.lathe("CastleNut", [(0.02, -0.175), (0.02, -0.188)], (0, 0, 0.018), black, 12),
        frame,
        g.slab("StockLever", [(-0.288, -0.014), (-0.262, -0.009), (-0.262, -0.003), (-0.288, -0.008)], 0.046, black),
        g.contoured(
            "ButtPad",
            [(-0.4, 0.05), (-0.414, 0.05), (-0.418, -0.075), (-0.403, -0.088), (-0.388, -0.084)],
            0.046,
            black,
            roll=0.006,
        ),
        g.lathe("SlingCup", [(0.007, 0.0), (0.007, 0.004)], (0.022, -0.22, 0.018), metal, 12, axis="x"),
    ]


def magazine(m, black, markings, receiver):
    """Curved 30-round box magazine with side ribs and a band of tape; the origin sits at its feed lip."""
    front = [(0.104, -0.03), (0.106, -0.09), (0.114, -0.14), (0.128, -0.185)]
    rear = [(0.058, -0.185), (0.044, -0.14), (0.034, -0.09), (0.032, -0.03)]
    mag = g.slab("Magazine", front + rear, 0.034, black, bevel=0.002)
    parts = [
        g.slab("MagBase", [(0.126, -0.183), (0.135, -0.198), (0.05, -0.198), (0.056, -0.183)], 0.04, black, bevel=0.002)
    ]
    rib = [(0.094, -0.05), (0.098, -0.1), (0.106, -0.15), (0.096, -0.155), (0.088, -0.105), (0.084, -0.05)]
    parts += [g.slab("MagRib", rib, 0.037, black), g.slab("MagRib2", [(y - 0.03, z) for y, z in rib], 0.037, black)]
    for side in (-1, 1):
        parts.append(g.marking(f"MagTape{side}", (0.062, -0.174, 0.116, -0.16), side * 0.017, side, "tape", markings))
    m.join_into(mag, parts)
    m.attach(mag, (0, 0.068, -0.03), receiver)


def barrel(m, metal, black, receiver):
    """Barrel node with a gas block step and a birdcage flash hider as `MuzzleBrake`."""
    run = [(0.0095, 0.0), (0.0095, 0.03), (0.0105, 0.03), (0.0105, 0.05), (0.008, 0.055), (0.008, 0.11)]
    pipe = g.lathe("Barrel", run, (0, 0.475, AXIS_Z), metal, 16)
    m.attach(pipe, (0, 0.475, AXIS_Z), receiver)
    hider = [(0.0095, 0.108), (0.0115, 0.112), (0.0115, 0.148), (0.0105, 0.152)]
    brake = g.lathe("MuzzleBrake", hider, (0, 0.475, AXIS_Z), black, 16)
    ports = []
    for i in range(3):
        port = g.slab(f"CagePort{i}", g.rounded(0.592, -0.0025, 0.62, 0.0025, 0.002), 0.03, black)
        port.rotation_euler = (0.0, math.pi / 3 * i, 0.0)
        port.location = (0.0, 0.0, AXIS_Z)
        ports.append(port)
    g.cut(brake, [g.lathe("BoreCut", [(0.0055, 0.575), (0.0055, 0.635)], (0, 0, AXIS_Z), black, 16), *ports])
    m.attach(brake, (0, 0.583, AXIS_Z), pipe)


def build(m) -> None:
    metal = m.material("GunMetalWorn", m.GUN_METAL, metallic=0.8, roughness=0.4)
    black = m.material("MatteBlackWorn", m.MATTE_BLACK, roughness=0.75)
    tan = m.material("TanWorn", m.TAN, roughness=0.8)
    glass = m.material("SightGlass", m.LENS, metallic=0.3, roughness=0.05)
    markings = m.material("Markings", m.MATTE_BLACK, roughness=0.7)
    receiver = upper(m, metal, black)
    logos = [g.marking(f"Logo{s}", (0.03, -0.074, 0.098, -0.05), s * 0.023, s, "logo", markings) for s in (-1, 1)]
    m.join_into(receiver, lower(m, metal, black, tan) + handguard(m, black) + stock(m, metal, black, tan) + logos)
    m.join_into(receiver, g.red_dot(m, -0.01, RAIL_TOP, EYE_Z, black, glass, markings, receiver))
    magazine(m, black, markings, receiver)
    barrel(m, metal, black, receiver)
    bolt = g.slab("Bolt", g.rounded(-0.015, 0.012, 0.045, 0.026, 0.003), 0.002, metal, x=0.022)
    m.attach(bolt, (0.0275, 0.015, 0.019), receiver)
    m.marker("Muzzle", (0, 0.627, AXIS_Z), parent=receiver)
    g.add_inlays(m, receiver, g.rounded(-0.145, 0.038, 0.14, 0.040, 0.001), 0.001, 0.0252, metal)
    g.stamp(m, "rifle_ar", "Receiver", (-0.025, -0.1, 0.026), 0.085)
