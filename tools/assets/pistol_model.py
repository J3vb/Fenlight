"""Warden P9: a bevelled service pistol with a working slide, bored barrel and stippled grip.

The unchanged pistol ADS pose puts the sights at Z 0.046. `Bolt` carries `Slide`
and its sights for the existing firing animation; the magazine pivots at its feed lips.
"""

import gun_parts as g

BORE_Z = 0.021
SIGHT_Z = 0.046


def slide_body(metal, black):
    """Faceted slide with cut rear serrations, a recessed ejection port and muzzle opening."""
    slide = g.slab(
        "Slide",
        [
            (-0.062, 0.008),
            (0.178, 0.008),
            (0.182, 0.01),
            (0.182, 0.033),
            (0.178, 0.035),
            (-0.057, 0.035),
            (-0.062, 0.03),
        ],
        0.032,
        metal,
        bevel=0.0015,
    )
    cutters = [
        g.slab("EjectionPocket", g.rounded(0.004, 0.018, 0.048, 0.04, 0.002), 0.024, black, x=0.017),
        g.lathe("MuzzleOpening", [(0.0096, 0.154), (0.0096, 0.186)], (0, 0, BORE_Z), black, 32),
    ]
    for side in (-1, 1):
        for i in range(7):
            y = -0.052 + i * 0.0055
            cutters.append(
                g.slab(
                    f"RearSerration{side}{i}",
                    [(y, 0.012), (y + 0.0025, 0.012), (y - 0.0015, 0.032), (y - 0.004, 0.032)],
                    0.003,
                    black,
                    x=side * 0.016,
                    bevel=0.0003,
                )
            )
    g.cut(slide, cutters)
    return slide


def frame_parts(black, polymer, metal):
    """A low polymer dust cover, open trigger guard and metal controls below the slide."""
    frame = g.slab(
        "Receiver",
        [
            (-0.061, 0.006),
            (0.163, 0.006),
            (0.166, -0.004),
            (0.147, -0.013),
            (0.045, -0.013),
            (0.028, -0.018),
            (-0.009, -0.018),
            (-0.04, -0.01),
            (-0.06, -0.006),
        ],
        0.03,
        polymer,
        bevel=0.002,
    )
    guard = g.slab(
        "TriggerGuard",
        [
            (-0.012, -0.012),
            (-0.022, -0.018),
            (-0.012, -0.048),
            (0.035, -0.048),
            (0.048, -0.036),
            (0.048, -0.013),
            (0.041, -0.013),
            (0.041, -0.033),
            (0.031, -0.041),
            (-0.006, -0.041),
            (-0.014, -0.018),
        ],
        0.014,
        polymer,
        bevel=0.0012,
    )
    return frame, [guard, *frame_controls(black, metal)]


def frame_controls(black, metal):
    """Dust-cover rail, takedown lever and restrained bilateral pins."""
    parts = [
        g.slab("DustRail", g.teeth(0.065, 0.145, -0.019, -0.012, 0.012), 0.022, black, bevel=0.0004),
        g.lathe("RecoilPlug", [(0.004, 0.16), (0.004, 0.169)], (0, 0, -0.002), metal, 20),
        g.slab("SlideStop", g.rounded(-0.025, -0.006, 0.01, 0.001, 0.002), 0.004, black, x=-0.017),
        g.slab("TakeDown", g.rounded(0.019, -0.007, 0.034, -0.001, 0.0015), 0.004, metal, x=-0.016),
    ]
    for side in (-1, 1):
        parts.append(
            g.lathe(
                "FramePin", [(0.0023, -0.001), (0.0023, 0.001)], (side * 0.015, -0.012, -0.007), black, 12, axis="x"
            )
        )
    return parts


def grip_parts(m, frame, polymer, checker, black):
    """Canted grip with sculpted backstrap, inset checkered panels and a separate magazine opening."""
    grip = g.contoured(
        "Grip",
        [
            (-0.045, -0.004),
            (-0.014, -0.012),
            (-0.008, -0.024),
            (-0.014, -0.04),
            (-0.023, -0.07),
            (-0.033, -0.104),
            (-0.039, -0.11),
            (-0.075, -0.108),
            (-0.078, -0.099),
            (-0.062, -0.042),
            (-0.062, -0.016),
        ],
        0.032,
        polymer,
        roll=0.011,
    )
    g.cut(
        grip,
        [g.slab("MagazineWell", [(-0.045, -0.015), (-0.018, -0.02), (-0.043, -0.115), (-0.072, -0.115)], 0.023, black)],
    )
    pieces = []
    for side in (-1, 1):
        pieces.append(
            g.slab(
                "GripPanel",
                [(-0.051, -0.024), (-0.021, -0.03), (-0.041, -0.099), (-0.067, -0.098)],
                0.002,
                checker,
                x=side * 0.016,
                bevel=0.0007,
            )
        )
        pieces.append(
            g.lathe("GripPin", [(0.002, -0.0012), (0.002, 0.0012)], (side * 0.017, -0.047, -0.071), black, 12, axis="x")
        )
    m.join_into(grip, pieces)
    m.attach(grip, (0, -0.035, -0.018), frame)


def barrel_parts(m, frame, metal, black):
    """Fixed chamber and crowned barrel visible through actual slide openings."""
    barrel = g.lathe(
        "Barrel",
        [
            (0.008, -0.005),
            (0.0088, 0.004),
            (0.0088, 0.05),
            (0.0078, 0.056),
            (0.0078, 0.18),
            (0.0087, 0.181),
            (0.0087, 0.185),
            (0.0076, 0.187),
        ],
        (0, 0, BORE_Z),
        metal,
        32,
    )
    g.cut(barrel, [g.lathe("Bore", [(0.0045, 0.145), (0.0045, 0.19)], (0, 0, BORE_Z), black, 24)])
    m.attach(barrel, (0, 0.025, BORE_Z), frame)
    m.marker("Muzzle", (0, 0.188, BORE_Z), parent=frame)


def sights(m, slide, black, metal):
    """Open square rear notch and a slim front post on the existing ADS eye line."""
    rear = g.slab("IronSights", g.rounded(-0.052, 0.034, -0.039, 0.039, 0.001), 0.023, black, bevel=0.0005)
    pieces = []
    for side in (-1, 1):
        pieces.append(
            g.slab(
                "RearEar", g.rounded(-0.052, 0.037, -0.041, 0.048, 0.001), 0.004, black, x=side * 0.0065, bevel=0.0005
            )
        )
    pieces.append(g.slab("FrontBase", g.rounded(0.156, 0.034, 0.17, 0.039, 0.001), 0.01, black, bevel=0.0005))
    pieces.append(
        g.slab(
            "FrontPost", [(0.16, 0.038), (0.166, 0.038), (0.166, SIGHT_Z), (0.16, SIGHT_Z)], 0.0026, metal, bevel=0.0003
        )
    )
    m.join_into(rear, pieces)
    m.attach(rear, (0, -0.045, 0.035), slide)


def moving_parts(m, frame, metal, black):
    """Flush 12-round magazine and curved trigger, each with its mechanical pivot."""
    magazine = g.slab(
        "Magazine",
        [(-0.043, -0.015), (-0.019, -0.019), (-0.043, -0.11), (-0.071, -0.11)],
        0.021,
        metal,
        bevel=0.001,
    )
    floor = g.slab(
        "MagBase", [(-0.074, -0.108), (-0.037, -0.108), (-0.037, -0.117), (-0.078, -0.117)], 0.034, black, bevel=0.0015
    )
    m.join_into(magazine, [floor])
    m.attach(magazine, (0, -0.031, -0.017), frame)
    trigger = g.slab(
        "Trigger",
        [(0.002, -0.015), (0.008, -0.015), (0.007, -0.027), (0.0, -0.037), (-0.005, -0.036), (0.001, -0.026)],
        0.006,
        black,
        bevel=0.0006,
    )
    m.attach(trigger, (0, 0.005, -0.015), frame)


def build(m) -> None:
    """Build the service sidearm using the shared shapes, materials and runtime part names."""
    metal = m.material("GunMetal", m.GUN_METAL, metallic=0.8, roughness=0.4)
    black = m.material("MatteBlack", m.MATTE_BLACK, roughness=0.75)
    polymer = m.material("GreyPolymer", m.srgb("#5F6D68"), roughness=0.8)
    checker = m.material("GreyPolymerKnurled", m.srgb("#2F393B"), roughness=0.85)
    frame, details = frame_parts(black, polymer, metal)
    m.join_into(frame, details)
    grip_parts(m, frame, polymer, checker, black)
    barrel_parts(m, frame, metal, black)
    moving_parts(m, frame, metal, black)
    bolt = m.marker("Bolt", (0, -0.035, BORE_Z), parent=frame)
    slide = slide_body(metal, black)
    m.attach(slide, (0, -0.035, BORE_Z), bolt)
    sights(m, slide, black, metal)
    g.add_inlays(m, slide, g.rounded(0.06, 0.027, 0.146, 0.029, 0.0008), 0.0006, 0.016, metal)
    g.stamp(m, "warden_p9", "Slide", (-0.016, 0.085, 0.023), 0.044)
