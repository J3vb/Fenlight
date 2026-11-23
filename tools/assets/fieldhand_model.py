"""Fieldhand: wood-stock lever rifle with an eight-round tube and open loading gate.

The loop lever and breech bolt remain separate; the fixed MagazineTube never
drops during the one-round reload. Irons sit on the 68 mm ADS eye line.
"""

import gun_parts as g

BORE_Z = 0.025
SIGHT_Z = 0.068


def action(metal, black):
    """Bevelled receiver with recessed side gate, visible breech and screw heads."""
    receiver = g.slab(
        "Receiver",
        [(-0.16, -0.028), (0.115, -0.028), (0.135, -0.006), (0.125, 0.05), (-0.145, 0.05), (-0.16, 0.027)],
        0.047,
        metal,
        bevel=0.003,
    )
    cuts = [
        g.slab("GateCut", g.rounded(-0.005, -0.012, 0.092, 0.017, 0.008), 0.013, metal, x=0.023),
        g.slab("BreechCut", g.rounded(-0.115, 0.025, 0.048, 0.048, 0.007), 0.04, metal, x=0.018),
    ]
    g.cut(receiver, cuts)
    parts = [
        g.slab("GateSpring", g.rounded(0.002, -0.009, 0.087, 0.012, 0.006), 0.003, black, x=0.018),
        g.slab("Tang", [(-0.245, 0.019), (-0.146, 0.019), (-0.146, 0.032), (-0.245, 0.025)], 0.023, metal),
    ]
    for side in (-1, 1):
        for y, z in ((-0.135, -0.01), (-0.09, 0.008), (0.108, -0.014)):
            ends = sorted((side * 0.0235, side * 0.025))
            parts.append(g.lathe("ActionScrew", [(0.0035, p) for p in ends], (0, y, z), black, 12, axis="x"))
    return receiver, parts


def stock(m, receiver, wood, black, checker):
    """Slim dropped comb, rounded wrist and thick rubber butt pad."""
    body = g.stock_shell(
        [
            (-0.490, -0.010, -0.104, 0.018, "pad"),
            (-0.486, -0.004, -0.109, 0.022, "pad"),
            (-0.476, -0.002, -0.110, 0.023, "wood"),
            (-0.448, 0.003, -0.109, 0.023, "wood"),
            (-0.374, 0.006, -0.085, 0.023, "wood"),
            (-0.310, 0.009, -0.065, 0.021, "wood"),
            (-0.265, 0.014, -0.054, 0.0235, "wood"),
            (-0.241, 0.019, -0.055, 0.0235, "panel"),
            (-0.212, 0.025, -0.070, 0.0235, "panel"),
            (-0.195, 0.024, -0.076, 0.0235, "panel"),
            (-0.177, 0.021, -0.066, 0.0235, "wood"),
            (-0.150, 0.017, -0.027, 0.0235, "wood"),
        ],
        wood,
        black,
        checker,
        wrist=-0.282,
    )
    m.attach(body, (0, -0.16, -0.013), receiver)


def fore_end(m, receiver, metal, wood, checker):
    """Rounded checkered wood fore-end, bounded by metal bands around barrel and tube."""
    body = g.contoured(
        "Foregrip",
        [(0.13, -0.012), (0.43, -0.012), (0.448, -0.025), (0.438, -0.05), (0.15, -0.05), (0.13, -0.039)],
        0.05,
        wood,
        roll=0.009,
    )
    parts = []
    for side in (-1, 1):
        parts.append(
            g.slab("ForeCheckering", g.rounded(0.17, -0.041, 0.404, -0.023, 0.006), 0.001, checker, x=side * 0.0251)
        )
    for y in (0.145, 0.43):
        band = g.slab("BarrelBand", g.rounded(y - 0.008, -0.052, y + 0.008, 0.038, 0.006), 0.054, metal, bevel=0.001)
        parts.append(band)
    m.join_into(body, parts)
    m.attach(body, (0, 0.13, -0.02), receiver)


def barrel(m, receiver, metal, black):
    """Long octagonal barrel with a bored crown and a capped fixed magazine tube below."""
    body = g.lathe(
        "Barrel",
        [(0.019, 0.115), (0.019, 0.155), (0.014, 0.56), (0.013, 0.585)],
        (0, 0, BORE_Z),
        metal,
        8,
        turn=0.392699,
    )
    g.cut(body, [g.lathe("BoreCut", [(0.0045, 0.11), (0.0045, 0.583), (0.0057, 0.587)], (0, 0, BORE_Z), metal, 16)])
    m.attach(body, (0, 0.12, BORE_Z), receiver)
    tube = g.lathe(
        "MagazineTube",
        [(0.0105, 0.12), (0.0105, 0.545), (0.0115, 0.548), (0.0115, 0.557), (0.01, 0.56)],
        (0, 0, -0.014),
        black,
        20,
    )
    m.attach(tube, (0, 0.12, -0.014), receiver)
    m.marker("Muzzle", (0, 0.587, BORE_Z), parent=receiver)


def sights(m, receiver, black):
    """Open buckhorn rear notch and narrow front blade on an unobstructed eye line."""
    parts = [
        g.slab("SightRamp", [(0.51, 0.037), (0.57, 0.037), (0.57, 0.051), (0.548, 0.051)], 0.014, black, bevel=0.001)
    ]
    parts.append(
        g.slab(
            "IronSights", [(0.545, 0.05), (0.565, 0.05), (0.56, SIGHT_Z), (0.551, SIGHT_Z)], 0.003, black, bevel=0.0005
        )
    )
    for side in (-1, 1):
        parts.append(
            g.slab(
                "RearNotch",
                [(-0.11, 0.048), (-0.096, 0.048), (-0.096, 0.072), (-0.11, 0.072)],
                0.003,
                black,
                x=side * 0.005,
            )
        )
    root = parts.pop(1)
    m.join_into(root, parts)
    m.attach(root, (0, -0.103, SIGHT_Z), receiver)


def moving_parts(m, receiver, metal, black):
    """Hollow loop lever, separate trigger, sliding breech and a knurled hammer spur."""
    lever = g.slab("Lever", g.rounded(-0.183, -0.095, 0.003, -0.022, 0.022), 0.012, metal, bevel=0.001)
    g.cut(lever, [g.slab("LoopCut", g.rounded(-0.17, -0.083, -0.01, -0.034, 0.017), 0.02, metal)])
    m.attach(lever, (0, -0.035, -0.025), receiver)
    trigger = g.slab(
        "Trigger",
        [(-0.045, -0.027), (-0.038, -0.027), (-0.041, -0.047), (-0.058, -0.065), (-0.064, -0.06), (-0.05, -0.044)],
        0.006,
        black,
        bevel=0.0006,
    )
    m.attach(trigger, (0, -0.042, -0.027), receiver)
    bolt = g.slab("Bolt", g.rounded(-0.127, 0.028, 0.044, 0.043, 0.004), 0.028, black, bevel=0.001)
    hammer = g.slab(
        "Hammer",
        [(-0.151, 0.03), (-0.14, 0.029), (-0.139, 0.048), (-0.15, 0.057), (-0.163, 0.054), (-0.16, 0.047)],
        0.008,
        metal,
        bevel=0.001,
    )
    m.join_into(bolt, [hammer])
    m.attach(bolt, (0, -0.12, 0.035), receiver)


def build(m) -> None:
    """Build an original tube-fed lever rifle from the shared gun-shape helpers."""
    metal = m.material("GunMetal", m.GUN_METAL, metallic=0.8, roughness=0.4)
    black = m.material("MatteBlack", m.MATTE_BLACK, roughness=0.75)
    wood = m.material("Wood", m.WOOD, roughness=0.7)
    checker = m.material("WoodKnurled", m.WOOD, roughness=0.8)
    receiver, parts = action(metal, black)
    m.join_into(receiver, parts)
    stock(m, receiver, wood, black, checker)
    fore_end(m, receiver, metal, wood, checker)
    barrel(m, receiver, metal, black)
    sights(m, receiver, black)
    moving_parts(m, receiver, metal, black)
    g.add_inlays(m, receiver, g.rounded(-0.13, 0.018, -0.03, 0.02, 0.0008), 0.001, 0.0237, metal)
    g.stamp(m, "fieldhand_lever", "Receiver", (-0.0235, -0.085, 0.028), 0.085)
