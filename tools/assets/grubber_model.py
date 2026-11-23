"""Grubber: short side-by-side break-action shotgun with a cut-down wood pistol grip.

The open twin bores, exposed action seam and broad forepiece distinguish this
sidearm from the full-stock Coachman. Bolt is the independent top locking lever.
"""

import gun_parts as g

BORE_Z = 0.032
BARREL_X = 0.015
MUZZLE_Y = 0.30
SIGHT_Z = 0.063
HINGE = (0, 0.038, 0.006)


def frame_parts(metal, black):
    """Sculpted action body with real sideplate recesses and visible hinge pins."""
    frame = g.slab(
        "Receiver",
        [
            (-0.08, -0.012),
            (0.035, -0.012),
            (0.06, 0.008),
            (0.06, 0.015),
            (-0.029, 0.016),
            (-0.031, 0.042),
            (-0.055, 0.042),
            (-0.08, 0.027),
        ],
        0.054,
        metal,
        bevel=0.003,
    )
    cuts = [
        g.slab(f"PlatePocket{side}", g.rounded(-0.065, -0.002, 0.02, 0.03, 0.006), 0.008, black, x=side * 0.029)
        for side in (-1, 1)
    ]
    g.cut(frame, cuts)
    parts = [
        g.slab("ActionTang", g.rounded(-0.099, 0.023, -0.045, 0.037, 0.004), 0.018, black, bevel=0.001),
        g.slab("BreechFace", g.rounded(-0.046, 0.0, -0.030, 0.043, 0.003), 0.052, black, bevel=0.001),
    ]
    for side in (-1, 1):
        parts.append(
            g.slab(f"SidePlate{side}", g.rounded(-0.06, 0.002, 0.015, 0.026, 0.005), 0.001, metal, x=side * 0.0255)
        )
        for y, z, r in ((0.038, 0.006, 0.008), (-0.05, 0.013, 0.003), (0.002, 0.014, 0.003)):
            ends = sorted((side * 0.026, side * 0.029))
            parts.append(g.lathe(f"Pin{side}{y}", [(r, p) for p in ends], (0, y, z), black, 12, axis="x"))
    return frame, parts


def barrels(m, receiver, metal, black):
    """Thick cut crowns and chambers; the bore is machined through each tube."""
    for side, name in ((-1, "BarrelL"), (1, "BarrelR")):
        at = (side * BARREL_X, 0, BORE_Z)
        tube = g.lathe(
            name,
            [(0.016, -0.029), (0.016, 0.085), (0.0144, 0.1), (0.0144, 0.296), (0.014, MUZZLE_Y)],
            at,
            black,
            32,
        )
        bore = [(0.0102, -0.032), (0.0102, 0.296), (0.0109, MUZZLE_Y), (0.0109, 0.302)]
        g.cut(tube, [g.lathe("BoreCut", bore, at, metal, 24)])
        crown = g.lathe("CutCrown", [(0.0145, 0.296), (0.0145, MUZZLE_Y)], at, metal, 32)
        g.cut(crown, [g.lathe("CrownCut", [(0.0102, 0.295), (0.0109, 0.302)], at, metal, 24)])
        m.join_into(tube, [crown])
        if side < 0:
            rib = g.slab("Rib", g.rounded(0.05, 0.044, 0.296, 0.051, 0.002), 0.007, black, bevel=0.0005)
            web = g.slab("BarrelWeb", [(0.047, 0.019), (0.294, 0.019), (0.294, 0.023), (0.047, 0.023)], 0.008, black)
            bead = g.lathe("SightBead", [(0.003, 0.052), (0.003, SIGHT_Z - 0.001)], (0, 0.282, 0), metal, 12, axis="z")
            m.join_into(tube, [rib, web, bead])
        m.attach(tube, (side * BARREL_X, 0.047, BORE_Z), receiver)


def grip(m, receiver, metal, black, wood, checker):
    """Saw-cut round pistol grip with inset checkering and a rubber end cap."""
    outline = [
        (-0.058, 0.027),
        (-0.088, 0.022),
        (-0.103, 0.0),
        (-0.135, -0.045),
        (-0.169, -0.102),
        (-0.162, -0.119),
        (-0.131, -0.118),
        (-0.113, -0.093),
        (-0.107, -0.071),
        (-0.092, -0.047),
        (-0.074, -0.033),
        (-0.051, -0.012),
    ]
    body = g.contoured("Grip", outline, 0.039, wood, roll=0.014)
    parts = [
        g.slab(
            "CutGripCap",
            [(-0.168, -0.1), (-0.162, -0.119), (-0.131, -0.118), (-0.128, -0.111)],
            0.041,
            black,
            bevel=0.0015,
        ),
        g.slab(
            "GripTang",
            [(-0.087, 0.016), (-0.095, 0.014), (-0.124, -0.034), (-0.115, -0.031)],
            0.019,
            metal,
            bevel=0.001,
        ),
    ]
    for side in (-1, 1):
        panel = [(-0.088, -0.013), (-0.1, -0.017), (-0.147, -0.095), (-0.134, -0.103), (-0.111, -0.064)]
        parts.append(g.slab(f"GripCheckering{side}", panel, 0.0015, checker, x=side * 0.0195, bevel=0.0005))
        ends = sorted((side * 0.0195, side * 0.021))
        parts.append(g.lathe(f"GripScrew{side}", [(0.0035, p) for p in ends], (0, -0.115, -0.062), metal, 12, axis="x"))
    m.join_into(body, parts)
    m.attach(body, (0, -0.077, 0.0), receiver)


def forepiece(m, receiver, metal, wood, checker):
    """Short splinter forepiece fits the twin barrels with separate inset grip panels."""
    outline = [(0.062, 0.014), (0.18, 0.014), (0.198, 0.0), (0.187, -0.024), (0.09, -0.032), (0.06, -0.018)]
    piece = g.contoured("Foregrip", outline, 0.055, wood, roll=0.009)
    cuts = [
        g.lathe(f"ForepieceSeat{side}", [(0.0145, 0.058), (0.0145, 0.2)], (side * BARREL_X, 0, BORE_Z), metal, 24)
        for side in (-1, 1)
    ]
    g.cut(piece, cuts)
    parts = [g.slab("ForepieceLatch", g.rounded(0.104, -0.032, 0.155, -0.026, 0.002), 0.016, metal, bevel=0.0007)]
    for side in (-1, 1):
        outline = [(0.08, -0.006), (0.174, -0.006), (0.18, -0.016), (0.094, -0.023)]
        parts.append(g.slab(f"ForepieceCheckering{side}", outline, 0.0015, checker, x=side * 0.027, bevel=0.0005))
    m.join_into(piece, parts)
    m.attach(piece, (0, 0.08, -0.005), receiver)


def controls(m, receiver, metal, black):
    """Open trigger guard, curved trigger and independent low-profile locking lever."""
    guard = [
        (-0.054, -0.01),
        (0.02, -0.01),
        (0.014, -0.042),
        (-0.009, -0.053),
        (-0.043, -0.05),
        (-0.063, -0.026),
        (-0.056, -0.025),
        (-0.04, -0.044),
        (-0.01, -0.046),
        (0.008, -0.037),
        (0.012, -0.014),
        (-0.054, -0.014),
    ]
    m.join_into(receiver, [g.slab("TriggerGuard", guard, 0.011, black, bevel=0.001)])
    trigger = g.slab(
        "Trigger",
        [(-0.016, -0.012), (-0.01, -0.012), (-0.014, -0.031), (-0.027, -0.042), (-0.032, -0.04), (-0.022, -0.028)],
        0.007,
        metal,
        bevel=0.0006,
    )
    m.attach(trigger, (0, -0.014, -0.013), receiver)
    latch = g.slab("Bolt", g.rounded(-0.075, 0.041, -0.026, 0.047, 0.002), 0.012, metal, bevel=0.0007)
    paddle = g.slab("LeverPaddle", g.rounded(-0.084, 0.044, -0.062, 0.049, 0.002), 0.025, black, bevel=0.0005)
    m.join_into(latch, [paddle])
    m.attach(latch, (0, -0.03, 0.044), receiver)


def sights(m, receiver, metal, black):
    """Shallow rear notch and tall enough bead to give a clear sight line over the rib."""
    base = g.slab("IronSights", g.rounded(-0.041, 0.043, -0.029, 0.047, 0.001), 0.024, black)
    parts = []
    for side in (-1, 1):
        parts.append(
            g.slab(f"NotchEar{side}", g.rounded(-0.039, 0.047, -0.031, 0.064, 0.001), 0.004, black, x=side * 0.006)
        )
    m.join_into(base, parts)
    m.attach(base, (0, -0.035, 0.047), receiver)


def build(m) -> None:
    """Build the cut-down sidearm from the common gun geometry tools."""
    metal = m.material("GunMetal", m.GUN_METAL, metallic=0.8, roughness=0.4)
    black = m.material("MatteBlack", m.MATTE_BLACK, roughness=0.75)
    wood = m.material("Wood", m.WOOD, roughness=0.7)
    checker = m.material("WoodKnurled", m.WOOD, roughness=0.8)
    receiver, pieces = frame_parts(metal, black)
    m.join_into(receiver, pieces)
    hinge = m.marker("Hinge", HINGE, parent=receiver)
    barrels(m, hinge, metal, black)
    m.marker("Muzzle", (0, MUZZLE_Y + 0.002 - HINGE[1], BORE_Z - HINGE[2]), parent=hinge)
    grip(m, receiver, metal, black, wood, checker)
    forepiece(m, hinge, metal, wood, checker)
    controls(m, receiver, metal, black)
    sights(m, receiver, metal, black)
    g.add_inlays(m, receiver, g.rounded(-0.055, 0.021, 0.01, 0.023, 0.0007), 0.0007, 0.0263, metal)
    g.stamp(m, "grubber_sawnoff", "Receiver", (-0.026, -0.024, 0.008), 0.044)
