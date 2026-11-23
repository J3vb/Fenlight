"""Coachman: full-stock side-by-side break-action with bored barrels and checkered wood.

The twin barrels and forepiece are separate children of Receiver. Bolt names the
opening lever for the existing viewmodel kick; loading remains a timed action.
"""

import gun_parts as g

BORE_Z = 0.044
BARREL_X = 0.018
MUZZLE_Y = 0.56
SIGHT_Z = 0.069


def receiver_parts(metal, black):
    """Machined box-lock action, standing breech, hinge pin and a real open trigger guard."""
    parts = [
        g.slab(
            "Receiver",
            [(-0.105, 0.004), (0.065, 0.004), (0.078, 0.016), (0.071, 0.05), (-0.083, 0.061), (-0.108, 0.044)],
            0.052,
            metal,
            bevel=0.003,
        ),
        g.slab("Breech", g.rounded(-0.054, 0.006, -0.042, 0.067, 0.004), 0.067, metal, bevel=0.002),
        g.slab(
            "TriggerGuard",
            [
                (0.025, 0.005),
                (0.025, -0.022),
                (0.009, -0.042),
                (-0.06, -0.042),
                (-0.079, -0.026),
                (-0.086, 0.005),
                (-0.078, 0.005),
                (-0.071, -0.022),
                (-0.057, -0.034),
                (0.004, -0.034),
                (0.018, -0.019),
                (0.018, 0.005),
            ],
            0.013,
            black,
            bevel=0.0015,
        ),
        g.slab("Tang", g.rounded(-0.156, 0.035, -0.084, 0.048, 0.004), 0.019, metal, bevel=0.001),
    ]
    for side in (-1, 1):
        parts.append(
            g.slab("ActionPanel", g.rounded(-0.087, 0.014, 0.036, 0.043, 0.007), 0.002, black, x=side * 0.0262)
        )
        for y, z, radius in ((0.042, 0.018, 0.008), (-0.071, 0.024, 0.004), (-0.015, 0.031, 0.003)):
            profile = [(radius, end) for end in sorted((side * 0.027, side * 0.029))]
            pin = g.lathe("ActionPin", profile, (0, y, z), metal, 12, axis="x")
            parts.append(pin)
    return parts


def barrel(m, receiver, side, metal, black):
    """Tapered tube with an open chamber and muzzle crown, supported by a long central rib."""
    x = side * BARREL_X
    tube = g.lathe(
        "BarrelL" if side < 0 else "BarrelR",
        [(0.017, -0.043), (0.017, 0.043), (0.0145, 0.12), (0.0125, 0.553), (0.012, MUZZLE_Y)],
        (x, 0, BORE_Z),
        metal,
        32,
    )
    core = [(0.0102, -0.046), (0.0095, 0.006), (0.0095, 0.556), (0.0103, 0.561)]
    g.cut(tube, [g.lathe("BoreCut", core, (x, 0, BORE_Z), black, 24)])
    collar = g.lathe("ChamberBand", [(0.0175, -0.04), (0.0175, -0.031)], (x, 0, BORE_Z), black, 24)
    g.cut(collar, [g.lathe("BandCore", [(0.015, -0.042), (0.015, -0.029)], (x, 0, BORE_Z), black, 24)])
    m.join_into(tube, [collar])
    m.attach(tube, (x, -0.035, BORE_Z), receiver)


def rib_parts(metal, black):
    """Raised sight rib, bead and a lower joining rib between the two independent tubes."""
    rib = g.slab("SightRib", [(0.028, 0.056), (0.551, 0.055), (0.551, 0.06), (0.028, 0.063)], 0.011, black, bevel=0.001)
    vents = [
        g.slab("RibVent", g.rounded(0.09 + i * 0.07, 0.057, 0.14 + i * 0.07, 0.059, 0.0008), 0.02, black)
        for i in range(6)
    ]
    g.cut(rib, vents)
    return [
        rib,
        g.slab("LowerRib", [(0.025, 0.027), (0.55, 0.03), (0.55, 0.034), (0.025, 0.032)], 0.012, metal),
        g.lathe(
            "FrontBead",
            [(0.003, 0.059), (0.003, SIGHT_Z - 0.002), (0.0015, SIGHT_Z)],
            (0, 0.536, 0),
            metal,
            12,
            axis="z",
        ),
    ]


def stock_parts(m, receiver, black, wood, checker):
    """Sculpted full shoulder stock with a swept wrist, cheek comb and fitted rubber butt pad."""
    stock = g.stock_shell(
        [
            (-0.458, 0.008, -0.095, 0.017, "pad"),
            (-0.454, 0.017, -0.101, 0.022, "pad"),
            (-0.441, 0.021, -0.101, 0.024, "wood"),
            (-0.427, 0.028, -0.102, 0.024, "wood"),
            (-0.365, 0.035, -0.103, 0.025, "wood"),
            (-0.293, 0.040, -0.086, 0.024, "wood"),
            (-0.246, 0.040, -0.065, 0.021, "wood"),
            (-0.225, 0.038, -0.050, 0.019, "wood"),
        ],
        wood,
        black,
        checker,
    )
    # The carved cheek tapers into a separate checkered wrist shaped to the glove.
    wrist = g.slab(
        "Wrist",
        [
            (-0.103, 0.040),
            (-0.150, 0.029),
            (-0.210, 0.041),
            (-0.246, 0.039),
            (-0.246, -0.066),
            (-0.205, -0.046),
            (-0.171, -0.022),
            (-0.148, -0.039),
            (-0.124, -0.027),
            (-0.107, 0.005),
        ],
        0.045,
        wood,
        bevel=0.005,
    )
    panels = [wrist]
    for side in (-1, 1):
        panels.append(
            g.slab(
                "WristCheckering",
                [
                    (-0.115, 0.023),
                    (-0.15, 0.014),
                    (-0.177, -0.008),
                    (-0.151, -0.027),
                    (-0.126, -0.016),
                ],
                0.001,
                checker,
                x=side * 0.0226,
            )
        )
    m.join_into(stock, panels)
    m.attach(stock, (0, -0.107, 0.015), receiver)


def forepiece(m, receiver, metal, wood, checker):
    """Rounded wood fore-end under the barrel block, checkered panels and a release latch."""
    fore = g.contoured(
        "Foregrip",
        [(0.064, 0.018), (0.257, 0.025), (0.28, 0.014), (0.267, -0.006), (0.112, -0.018), (0.067, -0.007)],
        0.052,
        wood,
        roll=0.009,
    )
    parts = [g.slab("ReleaseLatch", g.rounded(0.128, -0.018, 0.194, -0.013, 0.002), 0.016, metal)]
    for side in (-1, 1):
        parts.append(
            g.slab(
                "ForeCheckering",
                [(0.095, 0.01), (0.25, 0.014), (0.24, -0.002), (0.116, -0.01)],
                0.001,
                checker,
                x=side * 0.0262,
            )
        )
    m.join_into(fore, parts)
    m.attach(fore, (0, 0.16, 0.01), receiver)


def moving_parts(m, receiver, metal, black):
    """Opening lever and independent twin triggers; the Muzzle marker sits between the bores."""
    lever = g.slab(
        "Bolt",
        [(-0.092, 0.06), (-0.046, 0.06), (-0.045, 0.067), (-0.093, 0.068), (-0.107, 0.064)],
        0.012,
        black,
        bevel=0.0015,
    )
    m.attach(lever, (0, -0.05, 0.062), receiver)
    knob = g.lathe(
        "LeverKnob", [(0.005, -0.013), (0.006, -0.005), (0.005, 0.002)], (0, -0.096, 0.064), metal, 12, axis="x"
    )
    m.attach(knob, (0, -0.096, 0.064), lever)
    for index, y in enumerate((-0.019, -0.044)):
        trigger = g.slab(
            "Trigger" if index == 0 else "RearTrigger",
            [
                (y, 0.002),
                (y + 0.006, 0.002),
                (y + 0.003, -0.014),
                (y - 0.007, -0.027),
                (y - 0.012, -0.024),
                (y - 0.004, -0.013),
            ],
            0.006,
            metal,
            bevel=0.0008,
        )
        m.attach(trigger, (0, y, 0), receiver)
    m.marker("Muzzle", (0, MUZZLE_Y + 0.002, BORE_Z), parent=receiver)


def build(m) -> None:
    """Build a restrained wood-and-gunmetal break action using the shared gun shape helpers."""
    metal = m.material("GunMetal", m.GUN_METAL, metallic=0.8, roughness=0.4)
    black = m.material("MatteBlack", m.MATTE_BLACK, roughness=0.75)
    wood = m.material("Wood", m.WOOD, roughness=0.7)
    checker = m.material("WoodKnurled", m.WOOD, roughness=0.8)
    receiver, *pieces = receiver_parts(metal, black)
    m.join_into(receiver, pieces + rib_parts(metal, black))
    for side in (-1, 1):
        barrel(m, receiver, side, metal, black)
    stock_parts(m, receiver, black, wood, checker)
    forepiece(m, receiver, metal, wood, checker)
    moving_parts(m, receiver, metal, black)
    g.add_inlays(m, receiver, g.rounded(-0.078, 0.046, 0.027, 0.048, 0.0008), 0.001, 0.0262, metal)
    g.stamp(m, "coachman_2b", "Receiver", (-0.0272, -0.015, 0.019), 0.044)
