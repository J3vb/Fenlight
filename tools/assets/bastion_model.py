"""Bastion belt-fed LMG: broad feed tray, exposed links and a side-mounted 150-round box.

Receiver owns static detail; Belt, FeedCover, Magazine, Bolt and the heavy barrel
remain named parts. Gun forward is Blender +Y; the bipod folds along the barrel.
"""

import math

import gun_parts as g

BORE_Z = 0.034
SIGHT_Z = 0.112


def receiver(m, metal, black, olive):
    """Deep stamped body with broad feed tray, grip and an open trigger guard."""
    body = g.slab(
        "Receiver",
        [(-0.22, -0.025), (0.19, -0.025), (0.215, 0.015), (0.2, 0.07), (-0.2, 0.07), (-0.22, 0.052)],
        0.08,
        metal,
        bevel=0.003,
    )
    parts = lower_parts(metal, black, olive)
    for side in (-1, 1):
        for i in range(4):
            parts.append(
                g.lathe(
                    f"BodyPin{side}{i}",
                    [(0.0045, -0.002), (0.0045, 0.002)],
                    (side * 0.041, -0.18 + i * 0.105, 0.05),
                    black,
                    8,
                    axis="x",
                )
            )
        ear = [(-0.17, 0.079), (-0.145, 0.079), (-0.148, 0.12), (-0.168, 0.12)]
        parts.append(g.slab(f"RearEar{side}", ear, 0.004, black, x=side * 0.014, bevel=0.001))
    port = g.slab("EjectionPocket", g.rounded(-0.07, -0.004, 0.09, 0.039, 0.005), 0.035, black, x=0.045)
    g.cut(body, [port])
    m.join_into(body, parts)
    return body


def lower_parts(metal, black, olive):
    """The lower body and trigger group keep continuous extruded outlines."""
    parts = [
        g.slab("Lower", [(-0.21, -0.023), (0.08, -0.023), (0.06, -0.064), (-0.18, -0.064)], 0.064, black, bevel=0.003),
        g.contoured(
            "Grip", [(-0.1, -0.06), (-0.145, -0.06), (-0.183, -0.172), (-0.137, -0.178)], 0.038, olive, roll=0.011
        ),
        g.slab(
            "GripHeel",
            [(-0.181, -0.16), (-0.136, -0.166), (-0.137, -0.179), (-0.186, -0.177)],
            0.042,
            black,
            bevel=0.002,
        ),
        g.slab(
            "TriggerGuard",
            [
                (0.018, -0.06),
                (0.012, -0.103),
                (-0.092, -0.103),
                (-0.108, -0.06),
                (-0.099, -0.06),
                (-0.086, -0.095),
                (0.005, -0.095),
                (0.009, -0.06),
            ],
            0.014,
            black,
            bevel=0.001,
        ),
        g.slab(
            "Trigger",
            [(-0.06, -0.062), (-0.052, -0.062), (-0.06, -0.085), (-0.071, -0.09), (-0.069, -0.081)],
            0.006,
            metal,
        ),
        g.slab(
            "FeedTray",
            [(-0.025, 0.028), (0.15, 0.028), (0.15, 0.045), (-0.025, 0.045)],
            0.13,
            black,
            x=-0.02,
            bevel=0.002,
        ),
    ]
    parts.append(g.lathe("Selector", [(0.009, -0.006), (0.009, 0.0)], (-0.032, -0.13, -0.036), metal, 12, axis="x"))
    return parts


def feed_cover(m, body, metal, black):
    """Separate hinged cover with raised reinforcement ribs and a rear latch."""
    cover = g.slab(
        "FeedCover",
        [(-0.19, 0.069), (0.18, 0.069), (0.18, 0.079), (0.145, 0.092), (-0.15, 0.092), (-0.19, 0.08)],
        0.082,
        black,
        bevel=0.002,
    )
    parts = [
        g.lathe("CoverHinge", [(0.009, -0.048), (0.009, 0.048)], (0, 0.177, 0.075), metal, 12, axis="x"),
        g.slab("CoverLatch", g.rounded(-0.205, 0.059, -0.18, 0.082, 0.004), 0.033, metal, bevel=0.001),
    ]
    for side in (-1, 1):
        parts.append(
            g.slab(
                f"CoverRib{side}",
                [(-0.13, 0.091), (0.115, 0.091), (0.105, 0.097), (-0.12, 0.097)],
                0.007,
                metal,
                x=side * 0.027,
                bevel=0.001,
            )
        )
    m.join_into(cover, parts)
    m.attach(cover, (0, 0.177, 0.075), body)


def belt_box(m, body, metal, black, olive):
    """Wide side box and ten linked rounds curve visibly from the tray into its throat."""
    box = g.slab(
        "Magazine",
        [(-0.015, -0.062), (0.16, -0.062), (0.16, -0.255), (0.135, -0.272), (0.0, -0.272), (-0.015, -0.255)],
        0.126,
        olive,
        x=-0.095,
        bevel=0.004,
    )
    parts = [
        g.slab(
            "BoxLid",
            [(-0.02, -0.055), (0.165, -0.055), (0.165, -0.072), (-0.02, -0.072)],
            0.136,
            black,
            x=-0.095,
            bevel=0.002,
        ),
        g.slab("BoxPanel", g.rounded(0.005, -0.245, 0.142, -0.092, 0.009), 0.002, black, x=-0.159),
        g.slab("BoxCatch", g.rounded(0.052, -0.119, 0.095, -0.096, 0.003), 0.005, metal, x=-0.162, bevel=0.001),
    ]
    for y in (0.02, 0.12):
        parts.append(
            g.slab(
                f"BoxRib{y}",
                [(y, -0.24), (y + 0.01, -0.24), (y + 0.01, -0.13), (y, -0.13)],
                0.004,
                olive,
                x=-0.161,
                bevel=0.001,
            )
        )
    m.join_into(box, parts)
    m.attach(box, (-0.095, 0.07, -0.055), body)


def belt(m, body, brass, black):
    """Each visible cartridge and link belongs to one continuous belt mesh."""
    rounds = []
    for i in range(10):
        angle = math.pi * 0.5 * i / 9
        x, z = -0.043 - 0.086 * math.sin(angle), 0.039 - 0.102 * (1 - math.cos(angle))
        rounds.append(
            g.lathe(
                f"Round{i}",
                [(0.0055, 0.018), (0.006, 0.02), (0.006, 0.065), (0.004, 0.07), (0.004, 0.082), (0.001, 0.09)],
                (x, 0, z),
                brass,
                8,
            )
        )
        rounds.append(
            g.slab(
                f"Link{i}",
                [(0.034, z - 0.009), (0.055, z - 0.009), (0.055, z - 0.005), (0.034, z - 0.005)],
                0.009,
                black,
                x=x,
            )
        )
    belt = rounds.pop(0)
    belt.name = "Belt"
    m.join_into(belt, rounds)
    m.attach(belt, (-0.043, 0.045, 0.039), body)


def barrel(m, body, metal, black, olive):
    """Long heavy barrel with cooling collars, a gas tube and a chunky flash hider."""
    tube = g.lathe(
        "Barrel",
        [(0.024, 0.19), (0.025, 0.23), (0.019, 0.245), (0.019, 0.65), (0.015, 0.665), (0.015, 0.805)],
        (0, 0, BORE_Z),
        metal,
        16,
    )
    pieces = [
        g.lathe("GasTube", [(0.01, 0.22), (0.01, 0.67)], (0, 0, -0.007), black, 12),
        g.lathe("GasBlock", [(0.027, 0.64), (0.027, 0.665), (0.02, 0.675)], (0, 0, BORE_Z), black, 12),
        flash_hider(black),
        g.contoured(
            "Foregrip", [(0.23, -0.025), (0.42, -0.025), (0.4, 0.014), (0.25, 0.014)], 0.062, olive, roll=0.009
        ),
        g.slab(
            "FrontPost",
            [(0.66, 0.055), (0.68, 0.055), (0.675, 0.081), (0.673, SIGHT_Z), (0.667, SIGHT_Z), (0.665, 0.081)],
            0.004,
            metal,
        ),
    ]
    for i in range(5):
        y = 0.44 + i * 0.035
        pieces.append(g.lathe(f"CoolingCollar{i}", [(0.023, y), (0.023, y + 0.008)], (0, 0, BORE_Z), metal, 16))
    for side in (-1, 1):
        pieces.append(
            g.slab(
                f"SightWing{side}",
                [(0.656, 0.06), (0.684, 0.06), (0.679, 0.12), (0.661, 0.12)],
                0.004,
                black,
                x=side * 0.012,
                bevel=0.001,
            )
        )
    m.join_into(tube, pieces)
    m.attach(tube, (0, 0.19, BORE_Z), body)
    m.marker("Muzzle", (0, 0.873, BORE_Z), parent=body)


def flash_hider(black):
    """A true bore and transverse ports let the muzzle silhouette catch the light."""
    profile = [(0.019, 0.8), (0.022, 0.805), (0.022, 0.86), (0.018, 0.87)]
    hider = g.lathe("Hider", profile, (0, 0, BORE_Z), black, 12)
    cuts = [g.lathe("Bore", [(0.009, 0.79), (0.009, 0.875)], (0, 0, BORE_Z), black, 12)]
    for i in range(3):
        y = 0.813 + i * 0.016
        cuts.append(
            g.slab(f"HiderPort{i}", g.rounded(y, BORE_Z - 0.007, y + 0.008, BORE_Z + 0.007, 0.003), 0.06, black)
        )
    return g.cut(hider, cuts)


def stock(m, body, black, olive):
    """Full shoulder stock, low offset carry handle and the rearward folded bipod."""
    stock = g.stock_shell(
        [
            (-0.475, 0.024, -0.117, 0.023, "pad"),
            (-0.471, 0.032, -0.123, 0.028, "pad"),
            (-0.459, 0.034, -0.122, 0.027, "body"),
            (-0.431, 0.046, -0.117, 0.027, "body"),
            (-0.403, 0.053, -0.105, 0.026, "body"),
            (-0.298, 0.050, -0.052, 0.024, "body"),
            (-0.218, 0.045, -0.038, 0.022, "body"),
        ],
        olive,
        black,
        olive,
    )
    cheek = g.contoured(
        "CheekRest", [(-0.4, 0.040), (-0.26, 0.038), (-0.26, 0.054), (-0.39, 0.061)], 0.049, black, roll=0.008
    )
    m.join_into(stock, [cheek])
    m.attach(stock, (0, -0.22, 0.0), body)


def furniture(m, body, metal, black):
    """Carry handle to the right leaves the sight line open; the bipod stays folded."""
    carry = g.slab(
        "CarryHandle",
        [
            (0.19, 0.056),
            (0.205, 0.056),
            (0.23, 0.127),
            (0.35, 0.127),
            (0.374, 0.056),
            (0.389, 0.056),
            (0.365, 0.144),
            (0.217, 0.144),
        ],
        0.018,
        black,
        x=0.047,
        bevel=0.003,
    )
    pads = []
    for y in (0.199, 0.38):
        pads.append(
            g.slab(
                "HandleFoot",
                [(y - 0.011, 0.025), (y + 0.011, 0.025), (y + 0.008, 0.060), (y - 0.008, 0.060)],
                0.040,
                metal,
                x=0.033,
                bevel=0.002,
            )
        )
    for i in range(6):
        y = 0.244 + i * 0.018
        pads.append(g.slab("HandleWrap", g.rounded(y, 0.124, y + 0.014, 0.147, 0.003, steps=2), 0.022, black, x=0.047))
    m.join_into(carry, pads)
    m.attach(carry, (0.047, 0.19, 0.056), body)
    bipod = g.lathe("Bipod", [(0.012, -0.042), (0.012, 0.042)], (0, 0.64, -0.015), metal, 12, axis="x")
    pieces = []
    for side in (-1, 1):
        pieces.extend(
            [
                g.lathe(f"FoldedLeg{side}", [(0.007, 0.36), (0.007, 0.63)], (side * 0.04, 0, -0.029), black, 10),
                g.slab(
                    f"BipodFoot{side}",
                    g.rounded(0.35, -0.041, 0.38, -0.018, 0.004),
                    0.025,
                    black,
                    x=side * 0.04,
                    bevel=0.002,
                ),
            ]
        )
    m.join_into(bipod, pieces)
    m.attach(bipod, (0, 0.64, -0.015), body)


def build(m) -> None:
    """Build all named parts from shared profile helpers, ready for AO and finish import."""
    metal = m.material("GunMetal", m.GUN_METAL, metallic=0.8, roughness=0.4)
    black = m.material("MatteBlack", m.MATTE_BLACK, roughness=0.75)
    olive = m.material("OlivePolymer", m.srgb("#5F6D68"), roughness=0.85)
    body = receiver(m, metal, black, olive)
    feed_cover(m, body, metal, black)
    belt_box(m, body, metal, black, olive)
    brass = m.material("Brass", m.srgb("#AE9160"), metallic=0.78, roughness=0.46)
    belt(m, body, brass, black)
    barrel(m, body, metal, black, olive)
    stock(m, body, black, olive)
    furniture(m, body, metal, black)
    bolt = g.slab("Bolt", g.rounded(-0.065, 0.005, 0.065, 0.032, 0.004), 0.003, metal, x=0.034)
    handle = g.lathe(
        "ChargingHandle",
        [(0.006, 0.044), (0.006, 0.07), (0.01, 0.07), (0.01, 0.083)],
        (0, -0.025, 0.018),
        black,
        10,
        axis="x",
    )
    m.join_into(bolt, [handle])
    m.attach(bolt, (0.043, -0.025, 0.018), body)

    g.add_inlays(m, body, g.rounded(-0.16, 0.057, 0.14, 0.059, 0.0008), 0.0008, 0.0402, metal)
    g.stamp(m, "bastion_lmg", "Receiver", (-0.04, -0.085, 0.019), 0.085)
