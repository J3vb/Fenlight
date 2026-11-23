"""Hollis .44: heavy six-shot revolver with a full-lug barrel, fluted cylinder and wood grips.

Static parts join into `Receiver` (the frame). The hammer is the `Bolt` node, so the
viewmodel kick cocks it back; there is no Magazine (the cylinder loads by hand).
"""

import math

import gun_parts as g

BORE_Z = 0.04
CYL_Z = BORE_Z - 0.013
CYL_R = 0.0255
SIGHT_Z = 0.074


def frame_parts(metal, black):
    """Frame around the cylinder window, top strap with rear sight, guard and side plate."""
    parts = [
        g.slab(
            "FrameRear",
            [(-0.052, 0.0), (-0.03, 0.0), (-0.03, 0.068), (-0.04, 0.068), (-0.052, 0.05)],
            0.03,
            metal,
            bevel=0.002,
        ),
        g.slab(
            "TopStrap", [(-0.033, 0.056), (0.042, 0.056), (0.042, 0.071), (-0.033, 0.071)], 0.02, metal, bevel=0.002
        ),
        g.slab(
            "FrameFront",
            [(0.034, 0.0), (0.05, 0.0), (0.05, 0.071), (0.034, 0.071)],
            0.03,
            metal,
            bevel=0.002,
        ),
        g.slab("FrameBottom", [(-0.052, -0.004), (0.05, -0.004), (0.05, 0.0), (-0.052, 0.0)], 0.03, metal, bevel=0.001),
        g.slab(
            "TriggerGuard",
            [
                (0.022, -0.004),
                (0.022, -0.03),
                (0.005, -0.045),
                (-0.03, -0.045),
                (-0.04, -0.004),
                (-0.032, -0.004),
                (-0.025, -0.038),
                (0.002, -0.038),
                (0.015, -0.026),
                (0.015, -0.004),
            ],
            0.012,
            metal,
            bevel=0.0015,
        ),
        g.slab("SidePlate", g.rounded(-0.05, 0.002, -0.032, 0.048, 0.004), 0.002, metal, x=0.0155),
        g.slab("Latch", g.rounded(-0.046, 0.03, -0.034, 0.038, 0.002), 0.004, black, x=-0.016),
    ]
    for x in (-0.0045, 0.0045):
        parts.append(
            g.slab(
                f"RearSight{x}",
                [(-0.03, 0.07), (-0.018, 0.07), (-0.018, SIGHT_Z + 0.002), (-0.03, SIGHT_Z + 0.002)],
                0.004,
                black,
                x=x,
            )
        )
    for x in (-1, 1):
        for y, z in ((-0.044, 0.008), (-0.04, 0.04), (0.042, 0.008)):
            ends = sorted((x * 0.0145, x * 0.0165))
            parts.append(g.lathe(f"Screw{x}{y}{z}", [(0.003, end) for end in ends], (0, y, z), black, 8, axis="x"))
    g.cut(parts[2], [g.lathe("FrameBoreCut", [(0.006, 0.032), (0.006, 0.052)], (0, 0, BORE_Z), metal, 16)])
    return parts


def cylinder_parts(metal, black):
    """Six bored chambers; the top chamber follows the barrel and hammer axis above the cylinder axle."""
    profile = [(CYL_R - 0.002, -0.03), (CYL_R, -0.027), (CYL_R, 0.03), (CYL_R - 0.002, 0.033)]
    cylinder = g.lathe("Cylinder", profile, (0, 0, CYL_Z), metal, 48)
    cutters = []
    for i in range(6):
        a = math.pi / 2 + i * math.pi / 3
        at = ((CYL_R + 0.002) * math.cos(a), 0, CYL_Z + (CYL_R + 0.002) * math.sin(a))
        flute_profile = [
            (0.001, -0.022),
            (0.005, -0.018),
            (0.0058, -0.013),
            (0.0058, 0.014),
            (0.005, 0.019),
            (0.001, 0.023),
        ]
        flute = g.lathe(f"FluteCut{i}", flute_profile, at, metal, 16)
        mouth = (0.013 * math.cos(a), 0.0, CYL_Z + 0.013 * math.sin(a))
        chamber = [(0.0055, -0.031), (0.0048, -0.028), (0.0048, 0.031), (0.0055, 0.034)]
        cutters += [flute, g.lathe(f"ChamberCut{i}", chamber, mouth, metal, 16)]
    g.cut(cylinder, cutters)
    return [cylinder, g.lathe("Pin", [(0.003, 0.033), (0.003, 0.036)], (0, 0, CYL_Z), black, 12)]


def barrel_parts(metal, black):
    """Full-lug barrel: round tube, vented top rib, underlug with ejector rod and the front blade."""
    parts = [
        g.lathe(
            "BarrelTube", [(0.011, 0.036), (0.0095, 0.054), (0.0095, 0.2), (0.008, 0.203)], (0, 0, BORE_Z), metal, 32
        ),
        g.slab("TopRib", [(0.05, 0.046), (0.2, 0.046), (0.2, 0.055), (0.05, 0.055)], 0.011, metal, bevel=0.0015),
        g.slab(
            "Underlug",
            [(0.05, 0.012), (0.196, 0.012), (0.203, 0.02), (0.203, 0.036), (0.05, 0.036)],
            0.017,
            metal,
            bevel=0.002,
        ),
        g.slab(
            "FrontSight",
            [(0.178, 0.054), (0.198, 0.054), (0.198, SIGHT_Z), (0.188, SIGHT_Z), (0.178, 0.06)],
            0.004,
            black,
        ),
        g.lathe(
            "EjectorRod", [(0.003, 0.033), (0.003, 0.06), (0.0045, 0.062), (0.0045, 0.07)], (0, 0, 0.024), metal, 12
        ),
    ]
    bore = [(0.0055, 0.035), (0.0055, 0.2015), (0.0062, 0.203), (0.0062, 0.205)]
    g.cut(parts[0], [g.lathe("BoreCut", bore, (0, 0, BORE_Z), metal, 24)])
    vents = []
    for i in range(5):
        y = 0.065 + i * 0.026
        vents.append(g.slab(f"VentCut{i}", g.rounded(y, 0.05, y + 0.016, 0.0535, 0.0015), 0.02, metal))
    g.cut(parts[1], vents)
    cuts = []
    for x in (-1, 1):
        cuts.append(g.slab(f"LugCut{x}", g.rounded(0.06, 0.016, 0.19, 0.032, 0.006), 0.004, metal, x=x * 0.009))
    g.cut(parts[2], cuts)
    return parts


def grip_parts(m, receiver, metal, wood, checker):
    """Round-butt wood grips on a metal grip frame with a lanyard ring."""
    outline = [
        (-0.03, 0.0),
        (-0.054, 0.004),
        (-0.068, -0.03),
        (-0.086, -0.075),
        (-0.092, -0.1),
        (-0.084, -0.113),
        (-0.06, -0.114),
        (-0.05, -0.1),
        (-0.042, -0.065),
        (-0.03, -0.035),
        (-0.018, -0.006),
    ]
    grip = g.contoured("Grip", outline, 0.034, wood, roll=0.014)
    pieces = [
        g.slab(
            "GripFrame",
            [(-0.054, 0.004), (-0.062, 0.004), (-0.078, -0.035), (-0.092, -0.1), (-0.087, -0.1), (-0.072, -0.035)],
            0.026,
            metal,
            bevel=0.0015,
        ),
        g.lathe("Lanyard", [(0.004, -0.008), (0.004, 0.008)], (0, -0.075, -0.112), metal, 10, axis="x"),
    ]
    for x in (-1, 1):
        pieces.append(
            g.slab(
                f"Checker{x}",
                [(-0.05, -0.02), (-0.07, -0.03), (-0.082, -0.08), (-0.068, -0.1), (-0.052, -0.09), (-0.042, -0.05)],
                0.002,
                checker,
                x=x * 0.0172,
            )
        )
        pieces.append(
            g.lathe(
                f"GripScrew{x}",
                [(0.004, end) for end in sorted((x * 0.0165, x * 0.0185))],
                (0, -0.058, -0.055),
                metal,
                12,
                axis="x",
            )
        )
    m.join_into(grip, pieces)
    m.attach(grip, (0, -0.04, 0.0), receiver)


def moving_parts(m, receiver, metal, black):
    """Hammer (the Bolt) pivots at its base; trigger in the guard; Muzzle at the crown."""
    hammer = g.slab(
        "Bolt",
        [
            (-0.05, 0.038),
            (-0.042, 0.05),
            (-0.046, 0.062),
            (-0.058, 0.069),
            (-0.064, 0.065),
            (-0.057, 0.058),
            (-0.056, 0.04),
        ],
        0.008,
        metal,
        bevel=0.001,
    )
    m.attach(hammer, (0, -0.05, 0.04), receiver)
    trigger = g.slab(
        "Trigger",
        [(-0.006, -0.004), (0.0, -0.004), (-0.004, -0.02), (-0.014, -0.033), (-0.019, -0.03), (-0.011, -0.018)],
        0.006,
        black,
    )
    m.attach(trigger, (0, -0.004, -0.004), receiver)
    m.marker("Muzzle", (0, 0.204, BORE_Z), parent=receiver)


def build(m) -> None:
    """Build from shared helpers supplied by build_models, keeping the runtime part names."""
    metal = m.material("GunMetal", m.GUN_METAL, metallic=0.8, roughness=0.4)
    black = m.material("MatteBlack", m.MATTE_BLACK, roughness=0.75)
    wood = m.material("Wood", m.WOOD, roughness=0.7)
    checker = m.material("WoodKnurled", m.WOOD, roughness=0.8)
    receiver = g.slab(
        "Receiver", [(-0.03, -0.004), (0.034, -0.004), (0.034, 0.0), (-0.03, 0.0)], 0.026, metal, bevel=0.001
    )
    m.join_into(receiver, frame_parts(metal, black) + cylinder_parts(metal, black) + barrel_parts(metal, black))
    grip_parts(m, receiver, metal, wood, checker)
    moving_parts(m, receiver, metal, black)
    g.add_inlays(m, receiver, g.rounded(-0.024, 0.064, 0.031, 0.066, 0.0008), 0.001, 0.0104, metal)
    g.stamp(m, "hollis_44", "Receiver", (-0.007, 0.1, 0.028), 0.044)
