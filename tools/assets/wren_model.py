"""Wren MP: compact machine pistol, grip-fed extended magazine and hinged skeleton brace.

The runtime Bolt marker drives the separate Slide and its iron sights. All other
mechanical parts keep their own useful pivots beneath the static Receiver.
"""

import gun_parts as g

BORE_Z = 0.027
SIGHT_Z = 0.055


def frame(m, metal, black, polymer):
    """Short dust cover and a sculpted lower with an open trigger guard."""
    receiver = g.slab(
        "Receiver",
        [(-0.107, -0.012), (-0.095, -0.021), (0.10, -0.021), (0.13, -0.008), (0.13, 0.01), (-0.107, 0.01)],
        0.038,
        polymer,
        bevel=0.002,
    )
    parts = [
        g.slab("DustRail", g.teeth(0.053, 0.123, -0.024, -0.019, 0.014), 0.024, black),
        g.slab(
            "TriggerGuard",
            [
                (-0.025, -0.017),
                (-0.015, -0.06),
                (0.031, -0.06),
                (0.046, -0.047),
                (0.046, -0.016),
                (0.038, -0.016),
                (0.037, -0.043),
                (0.027, -0.052),
                (-0.009, -0.052),
                (-0.017, -0.017),
            ],
            0.013,
            black,
            bevel=0.0015,
        ),
        g.slab("Beavertail", g.rounded(-0.118, -0.018, -0.075, -0.006, 0.005), 0.032, black, bevel=0.001),
    ]
    for side in (-1, 1):
        for y in (-0.071, 0.012, 0.09):
            ends = sorted((side * 0.018, side * 0.0205))
            parts.append(g.lathe("FramePin", [(0.003, end) for end in ends], (0, y, -0.005), metal, 12, axis="x"))
        parts.append(
            g.slab(
                "SlideCatch",
                g.rounded(-0.049, -0.009, -0.02, -0.003, 0.002, steps=1),
                0.003,
                black,
                x=side * 0.0205,
                bevel=0.0007,
            )
        )
    selector = g.lathe("Selector", [(0.007, -0.023), (0.007, -0.02)], (0, -0.078, -0.005), metal, 16, axis="x")
    parts.append(selector)
    m.join_into(receiver, parts)
    return receiver


def grip(m, receiver, black, polymer, checker):
    """A lightly raked hollow grip receives the magazine rather than a forward well."""
    outline = [
        (-0.081, -0.012),
        (-0.034, -0.012),
        (-0.035, -0.043),
        (-0.048, -0.083),
        (-0.057, -0.12),
        (-0.102, -0.12),
        (-0.108, -0.108),
        (-0.094, -0.056),
    ]
    part = g.contoured("Grip", outline, 0.036, polymer, roll=0.011)
    core = [(-0.077, -0.008), (-0.044, -0.008), (-0.063, -0.124), (-0.093, -0.124)]
    g.cut(part, [g.slab("MagazineWell", core, 0.026, black)])
    panels = []
    panel = [(-0.08, -0.034), (-0.047, -0.034), (-0.064, -0.109), (-0.095, -0.109), (-0.098, -0.10)]
    for side in (-1, 1):
        panels.append(g.slab("GripPanel", panel, 0.002, checker, x=side * 0.018, bevel=0.001))
    for z in (-0.048, -0.063, -0.078):
        y = -0.04 + (z + 0.043) * 0.28
        panels.append(
            g.slab(
                "FingerRib",
                g.rounded(y - 0.004, z - 0.003, y + 0.001, z + 0.003, 0.002),
                0.032,
                black,
                bevel=0.0005,
            )
        )
    m.join_into(part, panels)
    m.attach(part, (0, -0.057, -0.012), receiver)


def slide(m, receiver, metal, black):
    """A real ejection opening, through muzzle clearance and cut cocking serrations."""
    part = g.slab(
        "Slide",
        [
            (-0.106, 0.013),
            (0.143, 0.013),
            (0.151, 0.019),
            (0.151, 0.035),
            (0.141, 0.043),
            (-0.097, 0.043),
            (-0.106, 0.035),
        ],
        0.034,
        metal,
        bevel=0.0015,
    )
    cutters = [
        g.lathe("MuzzleClearance", [(0.0105, 0.114), (0.0105, 0.154)], (0, 0, BORE_Z), black, 24),
        g.slab("EjectionCut", g.rounded(-0.018, 0.021, 0.036, 0.05, 0.003), 0.026, black, x=0.015),
    ]
    for side in (-1, 1):
        for i in range(7):
            y = -0.095 + i * 0.006
            cutters.append(
                g.slab(
                    "Serration",
                    [(y, 0.017), (y + 0.0025, 0.017), (y + 0.007, 0.039), (y + 0.0045, 0.039)],
                    0.003,
                    black,
                    x=side * 0.017,
                )
            )
    g.cut(part, cutters)
    bolt = m.marker("Bolt", (0, 0, BORE_Z), parent=receiver)
    m.attach(part, (0, 0, BORE_Z), bolt)
    iron_sights(m, part, metal, black)
    return part


def iron_sights(m, slide_part, metal, black):
    """Wide rear notch and a guarded front blade aligned at the fixed ADS height."""
    rear = g.slab("IronSights", g.rounded(-0.093, 0.042, -0.078, 0.046, 0.001, steps=1), 0.024, black, bevel=0.0005)
    pieces = []
    for side in (-1, 1):
        pieces.append(
            g.slab(
                "RearEar",
                g.rounded(-0.092, 0.044, -0.079, 0.057, 0.001, steps=1),
                0.006,
                black,
                x=side * 0.0075,
                bevel=0.0005,
            )
        )
        pieces.append(
            g.slab(
                "FrontGuard",
                [(0.12, 0.043), (0.132, 0.043), (0.131, 0.058), (0.123, 0.058)],
                0.003,
                black,
                x=side * 0.008,
                bevel=0.0005,
            )
        )
    pieces += [
        g.slab(
            "FrontBlade",
            [(0.123, 0.043), (0.13, 0.043), (0.129, SIGHT_Z), (0.125, SIGHT_Z)],
            0.003,
            metal,
            bevel=0.0005,
        ),
        g.slab("SightBase", g.rounded(0.118, 0.042, 0.134, 0.046, 0.001, steps=1), 0.023, black, bevel=0.0005),
    ]
    m.join_into(rear, pieces)
    m.attach(rear, (0, -0.085, 0.043), slide_part)


def barrel(m, receiver, metal, black):
    """Machined crown around a real bore, protruding just beyond the compact slide."""
    tube = g.lathe(
        "Barrel",
        [(0.009, -0.018), (0.009, 0.145), (0.0105, 0.148), (0.0105, 0.163), (0.009, 0.167)],
        (0, 0, BORE_Z),
        black,
        24,
    )
    bore = [(0.0045, -0.02), (0.0045, 0.163), (0.0053, 0.167), (0.0053, 0.17)]
    g.cut(tube, [g.lathe("BoreCut", bore, (0, 0, BORE_Z), metal, 24)])
    m.attach(tube, (0, 0.145, BORE_Z), receiver)
    m.marker("Muzzle", (0, 0.169, BORE_Z), parent=receiver)


def magazine(m, receiver, metal, black):
    """A straight 20-round grip magazine with recessed witness holes and a broad floorplate."""
    part = g.slab(
        "Magazine", [(-0.076, -0.013), (-0.045, -0.013), (-0.076, -0.201), (-0.108, -0.201)], 0.024, metal, bevel=0.0015
    )
    cutters = []
    for side in (-1, 1):
        for i in range(5):
            z = -0.126 - i * 0.013
            y = -0.074 + (z + 0.013) * 0.165
            ends = sorted((side * 0.010, side * 0.014))
            cutters.append(g.lathe("WitnessCut", [(0.002, end) for end in ends], (0, y, z), black, 12, axis="x"))
    g.cut(part, cutters)
    floor = g.slab(
        "Floorplate",
        [(-0.112, -0.199), (-0.072, -0.199), (-0.071, -0.209), (-0.114, -0.209)],
        0.031,
        black,
        bevel=0.0015,
    )
    m.join_into(part, [floor])
    m.attach(part, (0, -0.06, -0.013), receiver)


def brace(m, receiver, metal, black, polymer):
    """A deployed folding brace: vertical hinge, open skeleton and a slotted polymer cuff."""
    part = g.slab(
        "Brace",
        [
            (-0.109, 0.008),
            (-0.111, 0.018),
            (-0.29, 0.018),
            (-0.315, 0.005),
            (-0.315, -0.052),
            (-0.299, -0.058),
            (-0.283, -0.035),
            (-0.122, -0.014),
        ],
        0.014,
        metal,
        bevel=0.002,
    )
    opening = [(-0.137, 0.006), (-0.282, 0.006), (-0.299, -0.004), (-0.297, -0.032), (-0.283, -0.024), (-0.136, -0.004)]
    g.cut(part, [g.slab("BraceWindow", opening, 0.03, black, bevel=0.001)])
    cuff = g.slab("Stock", g.rounded(-0.321, -0.065, -0.299, 0.02, 0.006), 0.035, polymer, bevel=0.002)
    g.cut(cuff, [g.slab("StrapSlot", g.rounded(-0.316, -0.037, -0.305, -0.008, 0.003), 0.05, black)])
    hinge = g.lathe("BraceHinge", [(0.012, -0.016), (0.012, 0.017)], (0, -0.109, 0), black, 20, axis="z")
    pin = g.lathe("HingePin", [(0.005, -0.018), (0.005, 0.019)], (0, -0.109, 0), metal, 16, axis="z")
    latch = g.slab("BraceLatch", g.rounded(-0.124, -0.008, -0.113, 0.005, 0.002), 0.005, black, x=-0.015, bevel=0.001)
    m.join_into(part, [hinge, pin, latch])
    m.attach(part, (0, -0.109, 0), receiver)
    m.attach(cuff, (0, -0.309, -0.02), part)


def trigger(m, receiver, metal, black):
    """Curved trigger suspended inside the guard, plus a recessed magazine catch."""
    part = g.slab(
        "Trigger",
        [
            (-0.005, -0.018),
            (0.002, -0.018),
            (0.0, -0.032),
            (-0.007, -0.045),
            (-0.012, -0.046),
            (-0.014, -0.041),
            (-0.007, -0.029),
        ],
        0.007,
        metal,
        bevel=0.0008,
    )
    m.attach(part, (0, -0.002, -0.019), receiver)
    catch = g.slab(
        "MagazineCatch", g.rounded(-0.046, -0.031, -0.033, -0.02, 0.003), 0.003, black, x=-0.019, bevel=0.0007
    )
    m.join_into(receiver, [catch])


def build(m) -> None:
    """Build from the shared helpers, preserving animation names and the sight line."""
    metal = m.material("GunMetal", m.GUN_METAL, metallic=0.8, roughness=0.4)
    black = m.material("MatteBlack", m.MATTE_BLACK, roughness=0.75)
    color = m.srgb("#5F6D68")
    polymer = m.material("GreyPolymer", color, roughness=0.8)
    checker = m.material("GreyPolymerKnurled", m.srgb("#2F393B"), roughness=0.85)
    receiver = frame(m, metal, black, polymer)
    grip(m, receiver, black, polymer, checker)
    slide_part = slide(m, receiver, metal, black)
    barrel(m, receiver, metal, black)
    magazine(m, receiver, metal, black)
    brace(m, receiver, metal, black, polymer)
    trigger(m, receiver, metal, black)
    g.add_inlays(m, slide_part, g.rounded(0.045, 0.035, 0.129, 0.037, 0.0008), 0.0007, 0.0171, metal)
    g.stamp(m, "wren_mp", "Slide", (-0.017, 0.055, 0.026), 0.044)
