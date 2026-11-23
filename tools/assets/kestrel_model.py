"""VX-9 SMG (`kestrel_smg`): black and tan, Oriel red dot, vertical foregrip, curved taped mag, flash hider.

Static parts join into `Receiver`. Code needs `Magazine`, `Bolt` (with `ChargingHandle`),
`Barrel`, `FoldingStock`, `Grip`, `Trigger`, the `Muzzle` marker, `SightGlass` and `ReticleMount`.
Worn materials and the `Markings` atlas follow docs/plans/guns-concept.md.
"""

import math

import gun_parts as g

BORE_Z = 0.008
RAIL_TOP = 0.046
EYE_Z = 0.077  # aim line: WeaponData.ads_position.y is -EYE_Z


def body(m, metal, black):
    """Upper with ejection port and charging slot, lower with flared mag well, fore-end and rail."""
    receiver = g.slab(
        "Receiver",
        [(-0.14, -0.01), (0.13, -0.01), (0.13, 0.022), (0.115, 0.034), (-0.125, 0.034), (-0.14, 0.024)],
        0.05,
        black,
        bevel=0.002,
    )
    g.cut(
        receiver,
        [
            g.slab("PortCut", g.rounded(-0.012, 0.0, 0.064, 0.027, 0.004), 0.024, metal, x=0.027),
            g.slab("HandleCut", g.rounded(-0.095, 0.014, -0.02, 0.022, 0.003), 0.022, metal, x=0.027),
        ],
    )
    parts = [
        g.slab(
            "Lower",
            [
                (-0.135, -0.009),
                (0.125, -0.009),
                (0.12, -0.035),
                (0.092, -0.045),
                (0.09, -0.07),
                (0.02, -0.07),
                (0.018, -0.045),
                (-0.115, -0.045),
                (-0.135, -0.03),
            ],
            0.046,
            black,
            bevel=0.002,
        ),
        g.slab(
            "WellLip", [(0.018, -0.066), (0.092, -0.066), (0.094, -0.075), (0.016, -0.075)], 0.05, black, bevel=0.0015
        ),
        fore_end(black),
        *foregrip(black),
        g.slab("RailBase", [(-0.125, 0.034), (0.3, 0.034), (0.3, 0.039), (-0.125, 0.039)], 0.024, black),
        g.slab("RailTeeth", g.teeth(-0.122, 0.295, 0.039, 0.046), 0.021, black),
        g.slab("PortFloor", g.rounded(-0.011, 0.001, 0.063, 0.026, 0.003), 0.001, black, x=0.0155),
        g.slab("HandleFloor", g.rounded(-0.094, 0.015, -0.021, 0.021, 0.002), 0.001, black, x=0.0165),
        g.lathe("MagRelease", [(0.006, 0.023), (0.006, 0.029)], (0, 0.1, -0.035), metal, 12, axis="x"),
        g.lathe("Selector", [(0.008, -0.027), (0.008, -0.023)], (0, -0.07, -0.025), metal, 12, axis="x"),
        g.slab(
            "SelectorLever",
            [(-0.075, -0.027), (-0.05, -0.02), (-0.05, -0.016), (-0.073, -0.022)],
            0.003,
            metal,
            x=-0.028,
        ),
    ]
    for x in (-1, 1):
        for y, z in ((-0.12, 0.0), (0.105, 0.0), (-0.03, -0.035)):
            parts.append(
                g.lathe(f"Pin{x}{y}", [(0.0035, -0.0015), (0.0035, 0.0015)], (x * 0.024, y, z), metal, 10, axis="x")
            )
    m.join_into(receiver, parts)
    return receiver


def fore_end(mat):
    """Hollow octagonal sleeve with through-vents and a barrel visible inside (black on the VX-9)."""
    guard = g.lathe(
        "Handguard",
        [(0.028, 0.128), (0.031, 0.133), (0.031, 0.302), (0.028, 0.308)],
        (0, 0, BORE_Z),
        mat,
        8,
        turn=math.pi / 8,
    )
    cutters = [g.lathe("GuardCavity", [(0.023, 0.12), (0.023, 0.32)], (0, 0, BORE_Z), mat, 8, turn=math.pi / 8)]
    for i in range(4):
        y = 0.145 + i * 0.036
        cutters.append(g.slab("VentCut", g.rounded(y, 0.001, y + 0.024, 0.015, 0.005), 0.08, mat))
    return g.cut(guard, cutters)


def foregrip(black):
    """Vertical foregrip on a rail clamp at the front of the fore-end; the support hand stays behind it."""
    clamp = g.slab("GripClamp", [(0.269, -0.017), (0.301, -0.017), (0.299, -0.03), (0.271, -0.03)], 0.03, black)
    body = [(0.012, -0.026), (0.0135, -0.034), (0.0135, -0.086), (0.0155, -0.09), (0.0155, -0.097), (0.011, -0.1)]
    grip = g.lathe("Foregrip", body, (0, 0.285, 0), black, 12, axis="z")
    rings = [
        g.lathe(
            f"GripRing{i}",
            [(0.0142, -0.046 - i * 0.012), (0.0142, -0.04 - i * 0.012)],
            (0, 0.285, 0),
            black,
            12,
            axis="z",
        )
        for i in range(3)
    ]
    return [clamp, grip, *rings]


def lower_controls(m, receiver, metal, black):
    """Trigger guard joins the body; grip and trigger keep their own pivots."""
    guard = [
        (0.012, -0.045),
        (0.012, -0.08),
        (-0.062, -0.08),
        (-0.075, -0.045),
        (-0.067, -0.045),
        (-0.056, -0.073),
        (0.005, -0.073),
        (0.005, -0.045),
    ]
    m.join_into(receiver, [g.slab("TriggerGuard", guard, 0.012, black, bevel=0.0015)])
    grip_shape = [
        (-0.075, -0.044),
        (-0.107, -0.044),
        (-0.148, -0.142),
        (-0.144, -0.156),
        (-0.11, -0.156),
        (-0.1, -0.142),
        (-0.095, -0.12),
        (-0.088, -0.105),
        (-0.084, -0.085),
        (-0.078, -0.068),
    ]
    grip = g.contoured("Grip", grip_shape, 0.032, black, roll=0.011)
    panels = [
        g.slab(
            f"GripPanel{x}",
            [(-0.103, -0.055), (-0.138, -0.14), (-0.12, -0.148), (-0.096, -0.09), (-0.088, -0.062)],
            0.002,
            m.material("MatteBlackKnurledWorn", m.MATTE_BLACK, roughness=0.75),
            x=x * 0.0165,
        )
        for x in (-1, 1)
    ]
    m.join_into(grip, panels)
    m.attach(grip, (0, -0.09, -0.045), receiver)
    trigger = g.slab(
        "Trigger",
        [(-0.03, -0.045), (-0.024, -0.045), (-0.026, -0.058), (-0.034, -0.069), (-0.039, -0.066), (-0.032, -0.057)],
        0.006,
        metal,
    )
    m.attach(trigger, (0, -0.028, -0.047), receiver)


def stock(m, receiver, metal, black, tan):
    """Skeleton stock folding on a real hinge pivot, with cheek rest and a tan butt pad."""
    hinge_at = (0, -0.145, -0.006)
    folding = g.lathe("FoldingStock", [(0.016, -0.03), (0.016, 0.03)], hinge_at, metal, 16, axis="z")
    parts = [
        g.slab(
            "ButtFrame",
            [(-0.325, 0.032), (-0.345, 0.032), (-0.35, -0.072), (-0.325, -0.066)],
            0.045,
            black,
            bevel=0.003,
        ),
        g.contoured(
            "ButtPad", [(-0.345, 0.034), (-0.36, 0.034), (-0.364, -0.075), (-0.349, -0.077)], 0.049, tan, roll=0.006
        ),
        g.contoured("CheekRest", g.rounded(-0.31, 0.012, -0.2, 0.03, 0.006), 0.042, black, roll=0.008),
    ]
    for x in (-1, 1):
        parts += [
            g.slab(
                f"TopStrut{x}",
                [(-0.15, 0.002), (-0.33, 0.016), (-0.33, 0.026), (-0.15, 0.012)],
                0.008,
                black,
                x=x * 0.018,
                bevel=0.0015,
            ),
            g.slab(
                f"LowStrut{x}",
                [(-0.155, -0.018), (-0.33, -0.06), (-0.33, -0.05), (-0.15, -0.008)],
                0.008,
                black,
                x=x * 0.018,
                bevel=0.0015,
            ),
        ]
    m.join_into(folding, parts)
    m.attach(folding, hinge_at, receiver)


def moving_parts(m, receiver, metal, black, markings):
    """Curved magazine with tape (origin at the feed lip), charging handle parented to its sliding bolt."""
    front = [(0.083, -0.05), (0.085, -0.12), (0.089, -0.18), (0.095, -0.224)]
    rear = [(0.035, -0.23), (0.031, -0.18), (0.028, -0.12), (0.027, -0.05)]
    magazine = g.slab("Magazine", front + rear, 0.03, black, bevel=0.002)
    parts = [
        g.slab("MagBase", [(0.03, -0.228), (0.1, -0.222), (0.101, -0.235), (0.031, -0.241)], 0.036, black, bevel=0.002)
    ]
    for side in (-1, 1):
        parts.append(g.marking(f"MagTape{side}", (0.034, -0.15, 0.09, -0.128), side * 0.015, side, "tape", markings))
    m.join_into(magazine, parts)
    m.attach(magazine, (0, 0.055, -0.065), receiver)
    bolt = g.slab("Bolt", g.rounded(-0.005, 0.004, 0.05, 0.023, 0.003), 0.002, metal, x=0.020)
    m.attach(bolt, (0.0275, 0.022, 0.013), receiver)
    knob = [(0.004, 0.026), (0.004, 0.036), (0.007, 0.038), (0.007, 0.046), (0.005, 0.048)]
    handle = g.lathe("ChargingHandle", knob, (0, -0.06, 0.018), black, 12, axis="x")
    m.attach(handle, (0.03, -0.06, 0.018), bolt)


def barrel(m, receiver, metal, black):
    """Short barrel with a slotted flash hider (`MuzzleCap`)."""
    run = [(0.011, -0.12), (0.011, 0.085)]
    pipe = g.lathe("Barrel", run, (0, 0.25, BORE_Z), metal, 16)
    hider = [(0.011, 0.08), (0.013, 0.084), (0.013, 0.11), (0.0115, 0.113)]
    muzzle_cap = g.lathe("MuzzleCap", hider, (0, 0.25, BORE_Z), black, 16)
    ports = []
    for i in range(3):
        port = g.slab(f"CagePort{i}", g.rounded(0.342, BORE_Z - 0.0022, 0.366, BORE_Z + 0.0022, 0.0018), 0.03, black)
        port.rotation_euler = (0.0, math.pi / 3 * i, 0.0)
        port.location = (0.0, 0.0, BORE_Z)
        ports.append(port)
    g.cut(muzzle_cap, ports)
    for part in (pipe, muzzle_cap):
        g.cut(part, [g.lathe("BoreCut", [(0.0045, 0.318), (0.0045, 0.37)], (0, 0, BORE_Z), black, 16)])
    m.join_into(pipe, [muzzle_cap])
    m.attach(pipe, (0, 0.25, BORE_Z), receiver)
    m.marker("Muzzle", (0, 0.364, BORE_Z), parent=receiver)


def build_kestrel_smg(m):
    """Build in metres along Blender +Y (Godot -Z), keeping the shared animation nodes."""
    metal = m.material("GunMetalWorn", m.GUN_METAL, metallic=0.8, roughness=0.4)
    black = m.material("MatteBlackWorn", m.MATTE_BLACK, roughness=0.75)
    tan = m.material("TanWorn", m.TAN, roughness=0.8)
    glass = m.material("SightGlass", m.LENS, metallic=0.3, roughness=0.05)
    markings = m.material("Markings", m.MATTE_BLACK, roughness=0.7)
    receiver = body(m, metal, black)
    logos = [g.marking(f"Logo{s}", (-0.056, -0.03, 0.01, -0.009), s * 0.023, s, "logo", markings) for s in (-1, 1)]
    m.join_into(receiver, logos)
    m.join_into(receiver, g.red_dot(m, -0.02, RAIL_TOP, EYE_Z, black, glass, markings, receiver))
    lower_controls(m, receiver, metal, black)
    stock(m, receiver, metal, black, tan)
    moving_parts(m, receiver, metal, black, markings)
    barrel(m, receiver, metal, black)
    g.add_inlays(m, receiver, g.rounded(-0.112, 0.029, 0.098, 0.031, 0.0008), 0.001, 0.025, metal)
    g.stamp(m, "kestrel_smg", "Receiver", (-0.025, -0.085, 0.019), 0.085)
