"""Atlas Auto: magazine-fed auto shotgun with a slab-sided receiver, ribbed handguard and ghost-ring sights.

Static parts join into `Receiver`. Code and tests need `Magazine` (a fat 10-shell box),
`Bolt` (with `ChargingHandle`), `Stock`, `Barrel`, `IronSights`, `Trigger` and the `Muzzle` marker.
"""

import gun_parts as g

BORE_Z = 0.025
SIGHT_Z = 0.078


def receiver_parts(metal, black, olive):
    """Tall receiver with a flared magazine well, carry rail and the trigger housing."""
    parts = [
        g.slab("RailBase", [(-0.14, 0.058), (0.155, 0.058), (0.155, 0.062), (-0.14, 0.062)], 0.026, black),
        g.slab("RailTeeth", g.teeth(-0.135, 0.15, 0.062, 0.069, pitch=0.012), 0.023, black),
        g.slab(
            "Lower",
            [
                (-0.16, -0.002),
                (0.155, -0.002),
                (0.15, -0.03),
                (0.14, -0.07),
                (0.03, -0.07),
                (0.026, -0.05),
                (-0.125, -0.05),
                (-0.16, -0.03),
            ],
            0.054,
            olive,
            bevel=0.003,
        ),
        g.slab(
            "WellLip", [(0.024, -0.064), (0.146, -0.064), (0.148, -0.078), (0.022, -0.078)], 0.062, black, bevel=0.002
        ),
        g.slab("PortFloor", g.rounded(-0.059, 0.013, 0.049, 0.045, 0.004), 0.001, black, x=0.0195),
        g.slab("BoltRelease", g.rounded(0.0, -0.03, 0.02, -0.018, 0.003), 0.004, metal, x=-0.028),
        g.lathe("Selector", [(0.009, -0.031), (0.009, -0.027)], (0, -0.095, -0.03), metal, 12, axis="x"),
        g.lathe("MagRelease", [(0.007, 0.027), (0.007, 0.033)], (0, 0.012, -0.04), metal, 12, axis="x"),
    ]
    for x in (-1, 1):
        parts.append(g.slab(f"SidePlate{x}", g.rounded(-0.15, 0.004, -0.075, 0.046, 0.006), 0.002, metal, x=x * 0.029))
        for i in range(4):
            y = 0.06 + i * 0.022
            parts.append(
                g.slab(f"Flute{x}{i}", g.rounded(y, -0.046, y + 0.012, -0.012, 0.004), 0.002, black, x=x * 0.027)
            )
        for y, z in ((-0.15, 0.03), (0.15, 0.03), (-0.04, -0.036), (0.01, -0.036)):
            parts.append(
                g.lathe(f"Pin{x}{y}", [(0.0045, -0.0015), (0.0045, 0.0015)], (x * 0.029, y, z), metal, 10, axis="x")
            )
    return parts


def grip_parts(black, olive):
    """Pistol grip with a palm swell and the trigger guard."""
    grip = [
        (-0.094, -0.05),
        (-0.128, -0.05),
        (-0.172, -0.156),
        (-0.168, -0.17),
        (-0.132, -0.17),
        (-0.122, -0.155),
        (-0.114, -0.12),
        (-0.104, -0.09),
        (-0.098, -0.07),
    ]
    guard = [
        (0.024, -0.05),
        (0.024, -0.09),
        (-0.08, -0.09),
        (-0.098, -0.05),
        (-0.09, -0.05),
        (-0.076, -0.082),
        (0.016, -0.082),
        (0.016, -0.05),
    ]
    return [
        g.contoured("Grip", grip, 0.036, olive, roll=0.011),
        g.slab("TriggerGuard", guard, 0.014, black, bevel=0.0015),
    ]


def front_parts(m, receiver, metal, black, olive):
    """Ribbed round handguard, heavy barrel with gas block, ported choke, and ghost-ring sights."""
    guard = handguard(olive, black)
    m.attach(guard, (0, 0.16, BORE_Z), receiver)
    barrel = g.lathe(
        "Barrel",
        [(0.017, 0.16), (0.017, 0.47), (0.014, 0.473), (0.014, 0.6), (0.0165, 0.603), (0.0165, 0.66), (0.015, 0.663)],
        (0, 0, BORE_Z),
        metal,
        20,
    )
    cutters = [g.lathe("BoreCut", [(0.0115, 0.59), (0.0115, 0.67)], (0, 0, BORE_Z), metal, 20)]
    for i in range(4):
        y = 0.61 + i * 0.012
        cutters.append(g.slab("PortCut", g.rounded(y, BORE_Z - 0.006, y + 0.007, BORE_Z + 0.006, 0.003), 0.05, metal))
    g.cut(barrel, cutters)
    choke = [
        g.lathe("GasBlock", [(0.02, 0.45), (0.02, 0.47)], (0, 0, BORE_Z), black, 16),
        g.lathe("MagTube", [(0.008, 0.44), (0.008, 0.6)], (0, 0, BORE_Z - 0.028), metal, 10),
    ]
    m.join_into(barrel, choke)
    m.attach(barrel, (0, 0.44, BORE_Z), receiver)
    m.marker("Muzzle", (0, 0.665, BORE_Z), parent=receiver)
    sights = g.slab("IronSights", [(-0.13, 0.069), (-0.09, 0.069), (-0.09, 0.074), (-0.13, 0.074)], 0.03, black)
    pieces = [g.lathe("FrontBase", [(0.009, 0.46), (0.009, 0.476)], (0, 0, BORE_Z + 0.03), black, 12)]
    for x in (-1, 1):
        pieces += [
            g.slab(
                f"RingEar{x}",
                [(-0.118, 0.074), (-0.102, 0.074), (-0.104, 0.094), (-0.116, 0.094)],
                0.005,
                black,
                x=x * 0.011,
            ),
            g.slab(
                f"FrontEar{x}",
                [(0.458, 0.046), (0.478, 0.046), (0.474, 0.086), (0.462, 0.086)],
                0.003,
                black,
                x=x * 0.009,
            ),
        ]
    pieces += [
        g.slab("RingTop", [(-0.116, 0.094), (-0.104, 0.094), (-0.104, 0.099), (-0.116, 0.099)], 0.027, black),
        g.slab("FrontPost", [(0.464, 0.046), (0.472, 0.046), (0.471, SIGHT_Z), (0.465, SIGHT_Z)], 0.0035, metal),
    ]
    m.join_into(sights, pieces)
    m.attach(sights, (0, -0.11, 0.069), receiver)


def handguard(olive, black):
    """One ribbed polymer sleeve with an open core and rounded cooling windows."""
    profile = [(0.03, 0.155), (0.034, 0.16)]
    for y in (0.19, 0.25, 0.31, 0.37, 0.42):
        profile += [(0.034, y), (0.0352, y + 0.001), (0.0352, y + 0.007), (0.034, y + 0.008)]
    profile += [(0.034, 0.44), (0.03, 0.445)]
    guard = g.lathe("Handguard", profile, (0, 0, BORE_Z), olive, 20)
    guard.data.materials.append(black)
    for face in guard.data.polygons:
        if any(y < face.center.y < y + 0.008 for y in (0.19, 0.25, 0.31, 0.37, 0.42)):
            face.material_index = 1
    cutters = [g.lathe("GuardCavity", [(0.026, 0.15), (0.026, 0.45)], (0, 0, BORE_Z), olive, 20)]
    for y in (0.205, 0.265, 0.325, 0.385):
        cutters.append(g.slab("VentCut", g.rounded(y, 0.025, y + 0.024, 0.047, 0.006), 0.09, olive))
    return g.cut(guard, cutters)


def stock_parts(m, receiver, metal, black, olive):
    """Fixed stock with a straight comb, sling loop and thick recoil pad."""
    stock = g.contoured(
        "Stock",
        [
            (-0.16, 0.046),
            (-0.4, 0.04),
            (-0.405, -0.095),
            (-0.385, -0.1),
            (-0.3, -0.06),
            (-0.2, -0.042),
            (-0.16, -0.032),
        ],
        0.046,
        olive,
        roll=0.016,
    )
    pieces = [
        g.contoured(
            "RecoilPad", [(-0.4, 0.042), (-0.425, 0.042), (-0.428, -0.098), (-0.405, -0.104)], 0.052, black, roll=0.007
        ),
        g.slab("Comb", g.rounded(-0.37, 0.04, -0.2, 0.05, 0.004), 0.04, black, bevel=0.002),
        g.lathe("SlingLoop", [(0.005, -0.03), (0.005, 0.03)], (0, -0.36, -0.07), metal, 10, axis="x"),
    ]
    m.join_into(stock, pieces)
    m.attach(stock, (0, -0.16, 0.0), receiver)


def moving_parts(m, receiver, metal, black, olive):
    """Fat box magazine pivots at its feed lips; the charging handle rides the bolt."""
    magazine = g.slab(
        "Magazine",
        [(0.03, -0.07), (0.14, -0.07), (0.15, -0.205), (0.044, -0.212)],
        0.05,
        black,
        bevel=0.003,
    )
    pieces = [
        g.slab("MagBase", [(0.04, -0.208), (0.155, -0.2), (0.157, -0.218), (0.04, -0.226)], 0.056, olive, bevel=0.003)
    ]
    for x in (-1, 1):
        for i in range(3):
            z = -0.12 - i * 0.026
            pieces.append(
                g.slab(f"MagRib{x}{i}", g.rounded(0.05, z, 0.13, z + 0.008, 0.003), 0.002, olive, x=x * 0.0255)
            )
    m.join_into(magazine, pieces)
    m.attach(magazine, (0, 0.085, -0.07), receiver)
    magazine.rotation_euler.x = 0.06
    bolt = g.slab("Bolt", g.rounded(-0.055, 0.016, 0.045, 0.042, 0.003), 0.002, metal, x=0.024)
    m.attach(bolt, (0.0305, -0.005, 0.03), receiver)
    knob = [(0.0045, 0.03), (0.0045, 0.05), (0.009, 0.052), (0.009, 0.066), (0.007, 0.068)]
    handle = g.lathe("ChargingHandle", knob, (0, 0.03, 0.03), black, 12, axis="x")
    m.attach(handle, (0.035, 0.03, 0.03), bolt)
    trigger = g.slab(
        "Trigger",
        [(-0.046, -0.05), (-0.04, -0.05), (-0.042, -0.064), (-0.05, -0.076), (-0.055, -0.073), (-0.048, -0.063)],
        0.006,
        metal,
    )
    m.attach(trigger, (0, -0.043, -0.052), receiver)


def build(m) -> None:
    """Build from shared helpers supplied by build_models, keeping the runtime part names."""
    metal = m.material("GunMetal", m.GUN_METAL, metallic=0.8, roughness=0.4)
    black = m.material("MatteBlack", m.MATTE_BLACK, roughness=0.75)
    olive = m.material("OlivePolymer", m.srgb("#5F6D68"), roughness=0.85)
    receiver = g.slab(
        "Receiver",
        [(-0.16, -0.004), (0.16, -0.004), (0.16, 0.052), (0.145, 0.058), (-0.145, 0.058), (-0.16, 0.046)],
        0.058,
        black,
        bevel=0.003,
    )
    g.cut(receiver, [g.slab("PortCut", g.rounded(-0.06, 0.012, 0.05, 0.046, 0.005), 0.022, black, x=0.03)])
    m.join_into(receiver, receiver_parts(metal, black, olive) + grip_parts(black, olive))
    front_parts(m, receiver, metal, black, olive)
    stock_parts(m, receiver, metal, black, olive)
    moving_parts(m, receiver, metal, black, olive)
    g.add_inlays(m, receiver, g.rounded(-0.13, 0.052, 0.13, 0.054, 0.0008), 0.001, 0.029, metal)
    g.stamp(m, "atlas_auto", "Receiver", (-0.027, -0.085, -0.014), 0.085)
