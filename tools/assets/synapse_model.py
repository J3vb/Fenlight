"""Synapse: an Oriel nerve-fed rifle with an open sample cage and exposed Fenlight.

The ordinary rifle action remains readable beneath the living side bundles.
Magazine, Bolt and Trigger keep separate pivots; the nerve mesh uses the glow zone.
"""

import math

import bpy
import gun_parts as g

BORE_Z = 0.024
SIGHT_Z = 0.084


def glow_zone(obj):
    """Keep ordinary surfaces unpainted and encode this Prototype emitter separately from rarity inlay."""
    return g.paint(obj, 1 / 3)


def nerve(name, points, radius, mat):
    """A capped, gently curved sample tube, with tapered terminal connections."""
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 3
    curve.bevel_depth = radius
    curve.bevel_resolution = 1
    curve.use_fill_caps = True
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for i, point in enumerate(spline.bezier_points):
        point.co = points[i]
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
        point.radius = 0.65 if i in (0, len(points) - 1) else 1.0
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    obj.data.materials.append(mat)
    return obj


def action(metal, black, grey):
    """Faceted upper, a recessed ejection pocket and small removable access plates."""
    upper = g.slab(
        "Upper",
        [(-0.17, -0.01), (0.135, -0.01), (0.14, 0.035), (0.115, 0.052), (-0.15, 0.052), (-0.17, 0.035)],
        0.054,
        black,
        bevel=0.0025,
    )
    pocket = g.slab("PortCut", g.rounded(-0.085, 0.014, 0.005, 0.04, 0.004), 0.022, metal, x=0.029)
    g.cut(upper, [pocket])
    pieces = [
        upper,
        g.slab("Rail", g.teeth(-0.148, 0.09, 0.054, 0.061, 0.015), 0.024, black),
        g.slab(
            "Lower",
            [(-0.16, -0.006), (0.13, -0.006), (0.115, -0.04), (0.008, -0.046), (-0.02, -0.03), (-0.15, -0.03)],
            0.05,
            grey,
            bevel=0.003,
        ),
        g.slab("Well", g.rounded(0.005, -0.052, 0.105, -0.035, 0.005), 0.056, black, bevel=0.001),
    ]
    for side in (-1, 1):
        x = side * 0.028
        pieces.append(g.slab("AccessPlate", g.rounded(-0.15, 0.0, -0.1, 0.035, 0.005), 0.002, metal, x=x))
        for y, z in ((-0.14, 0.008), (-0.115, 0.028), (0.12, 0.015)):
            pins = [(0.0035, end) for end in sorted((x, x + side * 0.002))]
            pieces.append(g.lathe("CaptiveScrew", pins, (0, y, z), metal, 10, axis="x"))
    return pieces


def furniture(m, receiver, metal, black, grey):
    """An open shoulder frame and finger-shaped grip keep the silhouette rifle-like."""
    grip = g.contoured(
        "Grip",
        [
            (-0.09, -0.026),
            (-0.128, -0.026),
            (-0.175, -0.145),
            (-0.166, -0.164),
            (-0.135, -0.164),
            (-0.127, -0.147),
            (-0.122, -0.128),
            (-0.113, -0.116),
            (-0.107, -0.09),
        ],
        0.034,
        grey,
        roll=0.011,
    )
    m.attach(grip, (0, -0.11, -0.03), receiver)
    shoulder_stock(m, receiver, metal, black, grey)
    guard = g.slab(
        "TriggerGuard",
        [
            (-0.09, -0.03),
            (-0.076, -0.068),
            (-0.01, -0.068),
            (0.006, -0.046),
            (-0.001, -0.043),
            (-0.014, -0.06),
            (-0.07, -0.06),
            (-0.081, -0.03),
        ],
        0.014,
        black,
        bevel=0.0015,
    )
    m.join_into(receiver, [guard])


def shoulder_stock(m, receiver, metal, black, grey):
    """A skeletal shoulder frame with a soft cheek rest and replaceable butt pad."""
    stock = g.slab(
        "Stock",
        [
            (-0.365, -0.083),
            (-0.365, 0.046),
            (-0.33, 0.046),
            (-0.17, 0.028),
            (-0.17, 0.012),
            (-0.321, 0.018),
            (-0.33, -0.059),
            (-0.23, -0.024),
            (-0.19, -0.024),
            (-0.19, -0.039),
            (-0.338, -0.083),
        ],
        0.035,
        metal,
        bevel=0.003,
    )
    cheek = g.contoured("Cheek", g.rounded(-0.35, 0.033, -0.235, 0.053, 0.005), 0.045, grey, roll=0.008)
    pad = g.contoured("ButtPad", g.rounded(-0.378, -0.086, -0.364, 0.049, 0.005), 0.05, black, roll=0.006)
    m.join_into(stock, [cheek, pad])
    m.attach(stock, (0, -0.18, 0.022), receiver)


def cage(metal, black, grey):
    """The open sample cage exposes the barrel and the live bundles down both sides."""
    shroud = g.lathe(
        "SampleCage",
        [(0.034, 0.125), (0.039, 0.14), (0.039, 0.345), (0.03, 0.365)],
        (0, 0, BORE_Z),
        grey,
        8,
        turn=math.pi / 8,
    )
    cutters = [g.lathe("CageCore", [(0.029, 0.12), (0.029, 0.37)], (0, 0, BORE_Z), metal, 16)]
    for y in (0.15, 0.25):
        cutters.append(g.slab("SampleWindow", g.rounded(y, 0.003, y + 0.075, 0.047, 0.006), 0.12, metal))
    g.cut(shroud, cutters)
    pieces = [shroud]
    for y in (0.138, 0.24, 0.35):
        ring = g.lathe("CageBand", [(0.04, y), (0.04, y + 0.006)], (0, 0, BORE_Z), black, 12)
        g.cut(ring, [g.lathe("BandCore", [(0.036, y - 0.001), (0.036, y + 0.007)], (0, 0, BORE_Z), black, 12)])
        pieces.append(ring)
    pieces.append(g.slab("LowerRail", g.teeth(0.165, 0.325, -0.019, -0.025, 0.02), 0.018, black))
    return pieces


def barrel(m, receiver, metal, black):
    """Turned barrel with an open crown and recessed radial brake ports."""
    tube = g.lathe(
        "Barrel",
        [(0.011, 0.115), (0.011, 0.39), (0.014, 0.395), (0.014, 0.41), (0.017, 0.415), (0.017, 0.46), (0.014, 0.468)],
        (0, 0, BORE_Z),
        metal,
        20,
    )
    cuts = [g.lathe("BoreCut", [(0.006, 0.105), (0.006, 0.47)], (0, 0, BORE_Z), black, 16)]
    for y in (0.422, 0.443):
        cuts.append(g.slab("BrakePort", g.rounded(y, 0.017, y + 0.011, 0.031, 0.003), 0.05, black))
    g.cut(tube, cuts)
    m.attach(tube, (0, 0.135, BORE_Z), receiver)
    m.marker("Muzzle", (0, 0.47, BORE_Z), parent=receiver)


def sights(m, receiver, metal, black):
    """A narrow notched rear and protected blade leave the centre sightline open."""
    pieces = []
    for side in (-1, 1):
        pieces += [
            g.slab("RearEar", g.rounded(-0.135, 0.061, -0.12, 0.093, 0.002), 0.004, black, x=side * 0.008),
            g.slab(
                "FrontEar",
                [(0.323, 0.059), (0.343, 0.059), (0.34, 0.093), (0.328, 0.093)],
                0.004,
                black,
                x=side * 0.009,
            ),
        ]
    bridge = g.slab("IronSights", g.rounded(-0.137, 0.058, -0.118, 0.066, 0.002), 0.024, black)
    pieces += [
        g.slab("FrontBase", g.rounded(0.32, 0.057, 0.345, 0.065, 0.002), 0.026, black),
        g.slab("FrontBlade", [(0.33, 0.065), (0.336, 0.065), (0.336, SIGHT_Z), (0.33, SIGHT_Z)], 0.003, metal),
    ]
    m.join_into(bridge, pieces)
    m.attach(bridge, (0, -0.128, 0.062), receiver)


def magazine(m, receiver, metal, black, grey):
    """Broad sixty-round sample magazine, ribbed with two recessed inspection strips."""
    mag = g.slab(
        "Magazine",
        [(0.014, -0.045), (0.094, -0.045), (0.112, -0.22), (0.099, -0.237), (0.03, -0.237), (0.018, -0.216)],
        0.048,
        black,
        bevel=0.0025,
    )
    pieces = [g.slab("MagFoot", g.rounded(0.027, -0.246, 0.116, -0.232, 0.004), 0.057, grey, bevel=0.0015)]
    for side in (-1, 1):
        for y in (0.033, 0.075):
            slot = g.slab("MagRecess", g.rounded(y, -0.215, y + 0.012, -0.069, 0.003), 0.006, metal, x=side * 0.025)
            g.cut(mag, [slot])
        for z in (-0.09, -0.13, -0.17, -0.21):
            pieces.append(g.slab("MagRib", g.rounded(0.05, z, 0.073, z + 0.006, 0.002), 0.002, grey, x=side * 0.0245))
    m.join_into(mag, pieces)
    m.attach(mag, (0, 0.054, -0.049), receiver)


def controls(m, receiver, metal, black):
    """The exposed bolt and charging knob move together above the trigger."""
    bolt = g.slab("Bolt", g.rounded(-0.078, 0.019, -0.003, 0.036, 0.003), 0.003, metal, x=0.021)
    knob = g.lathe(
        "ChargingHandle",
        [(0.004, 0.022), (0.004, 0.036), (0.007, 0.039), (0.007, 0.048)],
        (0, -0.045, 0.026),
        black,
        12,
        axis="x",
    )
    m.join_into(bolt, [knob])
    m.attach(bolt, (0.022, -0.045, 0.026), receiver)
    trigger = g.slab(
        "Trigger",
        [(-0.052, -0.03), (-0.045, -0.03), (-0.048, -0.045), (-0.06, -0.056), (-0.065, -0.053), (-0.055, -0.042)],
        0.006,
        metal,
        bevel=0.0007,
    )
    m.attach(trigger, (0, -0.05, -0.032), receiver)


def cabling(m, receiver, black, live):
    """Live paired trunks bifurcate into the chamber and barrel under mechanical clamps."""
    bundles = []
    fittings = []
    for side in (-1, 1):
        x = side * 0.038
        points = [
            (side * 0.026, -0.1, 0.007),
            (x, -0.045, -0.005),
            (side * 0.047, 0.07, 0.011),
            (side * 0.037, 0.18, 0.035),
            (side * 0.046, 0.27, 0.015),
            (side * 0.027, 0.35, 0.025),
        ]
        bundles.append(nerve("NerveTrunk", points, 0.0038, live))
        branch = [
            (side * 0.043, 0.065, 0.01),
            (side * 0.045, 0.13, -0.004),
            (side * 0.039, 0.22, 0.013),
            (side * 0.028, 0.29, 0.038),
        ]
        bundles.append(nerve("NerveBranch", branch, 0.002, live))
        for y in (-0.1, 0.35):
            fittings.append(
                g.lathe("SampleCoupler", [(0.008, -0.006), (0.008, 0.006)], (side * 0.029, y, 0.019), black, 12)
            )
    bundles = [glow_zone(obj) for obj in bundles]
    trunk = bundles.pop(0)
    trunk.name = "Cabling"
    m.join_into(trunk, bundles)
    m.attach(trunk, (0.038, 0.12, 0.015), receiver)
    m.join_into(receiver, fittings)


def build(m) -> None:
    """Build the fixed Prototype with small live zones rather than a full-gun glow."""
    metal = m.material("GunMetal", m.GUN_METAL, metallic=0.8, roughness=0.4)
    black = m.material("MatteBlack", m.MATTE_BLACK, roughness=0.78)
    grey = m.material("GreyPolymer", m.srgb("#5F6D68"), roughness=0.8)
    live = m.material("OlivePolymer", m.srgb("#8DFF3A"), roughness=0.55, glow=1.5)
    receiver = g.slab("Receiver", g.rounded(-0.145, -0.015, 0.125, 0.025, 0.004), 0.045, metal, bevel=0.001)
    m.join_into(receiver, action(metal, black, grey) + cage(metal, black, grey))
    furniture(m, receiver, metal, black, grey)
    barrel(m, receiver, metal, black)
    sights(m, receiver, metal, black)
    magazine(m, receiver, metal, black, grey)
    controls(m, receiver, metal, black)
    cabling(m, receiver, black, live)
    g.stamp(m, "synapse", "Receiver", (-0.027, -0.05, 0.019), 0.085)
