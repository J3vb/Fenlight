"""Oriel Cryo Lance: field refrigeration rifle with a removable coolant tank and frosted condenser coils."""

import math

import bpy
import gun_parts as g

BORE_Z = 0.035
SIGHT_Z = 0.105


def glow_zone(obj):
    """Keep ordinary surfaces unpainted and encode this Prototype emitter separately from rarity inlay."""
    return g.paint(obj, 1 / 3)


def receiver_parts(metal, black, grey):
    """Faceted pressure housing, recessed service panel and large guarded controls."""
    upper = g.slab(
        "UpperHousing",
        [(-0.16, -0.018), (0.15, -0.018), (0.19, 0.004), (0.19, 0.064), (0.14, 0.085), (-0.12, 0.085), (-0.16, 0.065)],
        0.064,
        grey,
        bevel=0.004,
    )
    cuts = [g.slab("PanelPocket", g.rounded(-0.115, 0.006, 0.105, 0.062, 0.01), 0.012, metal, x=0.032)]
    g.cut(upper, cuts)
    parts = [upper, g.slab("ServicePlate", g.rounded(-0.104, 0.014, 0.092, 0.054, 0.006), 0.004, black, x=0.027)]
    for y in (-0.12, 0.13):
        for x in (-1, 1):
            parts.append(
                g.lathe("HousingScrew", [(0.004, -0.002), (0.004, 0.002)], (x * 0.033, y, 0.036), metal, 8, axis="x")
            )
    for y in (-0.075, -0.045, -0.015):
        parts.append(
            g.slab(
                "PanelLouvre",
                [(y, 0.019), (y + 0.018, 0.019), (y + 0.018, 0.025), (y, 0.025)],
                0.003,
                metal,
                x=0.03,
                bevel=0.001,
            )
        )
    # A folded instrument surround on the opposite flank breaks up the broad casing.
    bezel = [(0.012, 0.003), (0.124, 0.003), (0.15, 0.021), (0.15, 0.052), (0.139, 0.059), (0.012, 0.059)]
    parts.append(g.slab("InstrumentSurround", bezel, 0.0032, black, x=-0.032))
    for index in range(4):
        y = 0.032 + index * 0.024
        stripe = [(y, 0.018), (y + 0.007, 0.018), (y + 0.019, 0.044), (y + 0.012, 0.044)]
        parts.append(g.slab("EnamelIndex", stripe, 0.0009, metal, x=-0.0338))
    return parts + lower_parts(metal, black, grey)


def lower_parts(metal, black, grey):
    """Insulated pistol grip and oversize glove-friendly trigger guard."""
    parts = [
        g.slab("Rail", g.teeth(-0.12, 0.16, 0.083, 0.093, 0.025), 0.026, black, bevel=0.0006),
        g.contoured(
            "Grip",
            [
                (-0.12, -0.018),
                (-0.074, -0.018),
                (-0.085, -0.06),
                (-0.105, -0.11),
                (-0.13, -0.174),
                (-0.165, -0.172),
                (-0.17, -0.155),
            ],
            0.035,
            black,
            roll=0.011,
        ),
        g.slab(
            "Guard",
            [
                (-0.073, -0.019),
                (0.009, -0.019),
                (0.009, -0.068),
                (-0.069, -0.068),
                (-0.09, -0.026),
                (-0.082, -0.026),
                (-0.064, -0.06),
                (0.001, -0.06),
                (0.001, -0.019),
            ],
            0.015,
            metal,
            bevel=0.0015,
        ),
    ]
    for x in (-1, 1):
        parts.append(
            g.slab(
                "GripPad",
                [(-0.117, -0.047), (-0.1, -0.047), (-0.136, -0.15), (-0.155, -0.15)],
                0.003,
                grey,
                x=x * 0.018,
                bevel=0.0015,
            )
        )
    return parts


def stock_parts(m, receiver, metal, black, grey):
    """Open refrigeration-tool stock with a cheek rest and insulated rubber butt."""
    stock = g.slab(
        "Stock",
        [(-0.4, 0.07), (-0.38, 0.078), (-0.15, 0.06), (-0.15, 0.022), (-0.35, 0.035), (-0.36, -0.077), (-0.4, -0.078)],
        0.045,
        black,
        bevel=0.003,
    )
    parts = [g.slab("CheekRest", g.rounded(-0.37, 0.056, -0.21, 0.083, 0.009), 0.052, grey, bevel=0.002)]
    parts.append(
        g.slab(
            "LowerBrace", [(-0.37, -0.07), (-0.36, -0.052), (-0.16, 0.005), (-0.16, -0.01)], 0.02, metal, bevel=0.002
        )
    )
    for i in range(4):
        z = -0.065 + i * 0.027
        parts.append(
            g.slab(
                "ButtRib",
                [(-0.404, z), (-0.396, z), (-0.396, z + 0.014), (-0.404, z + 0.014)],
                0.052,
                black,
                bevel=0.002,
            )
        )
    m.join_into(stock, parts)
    m.attach(stock, (0, -0.15, 0.04), receiver)


def coil(m, metal):
    """One continuous capped helical condenser tube, light frost colour over dark inner barrel."""
    curve = bpy.data.curves.new("CondenserCoils", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = 0.004
    curve.bevel_resolution = 1
    curve.use_fill_caps = True
    spline = curve.splines.new("POLY")
    count = 85
    spline.points.add(count - 1)
    for i, point in enumerate(spline.points):
        angle = i / (count - 1) * math.tau * 6
        point.co = (0.029 * math.cos(angle), 0.21 + i / (count - 1) * 0.24, BORE_Z + 0.029 * math.sin(angle), 1)
    obj = bpy.data.objects.new("CondenserCoils", curve)
    bpy.context.scene.collection.objects.link(obj)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    obj.data.materials.append(metal)
    return obj


def barrel_parts(m, receiver, metal, black, frost):
    """Bored pressure barrel in an open condenser cage, with heavy threaded muzzle collar."""
    barrel = g.lathe(
        "Barrel",
        [(0.017, 0.16), (0.017, 0.195), (0.012, 0.2), (0.012, 0.46), (0.018, 0.465), (0.018, 0.49), (0.016, 0.505)],
        (0, 0, BORE_Z),
        metal,
        24,
    )
    g.cut(barrel, [g.lathe("Bore", [(0.006, 0.155), (0.006, 0.51)], (0, 0, BORE_Z), black, 16)])
    pieces = []
    for y in (0.196, 0.46):
        ring = g.lathe(
            "CageRing",
            [(0.037, y), (0.039, y + 0.003), (0.039, y + 0.015), (0.037, y + 0.018)],
            (0, 0, BORE_Z),
            black,
            16,
        )
        g.cut(ring, [g.lathe("CageCore", [(0.032, y - 0.001), (0.032, y + 0.02)], (0, 0, BORE_Z), black, 16)])
        pieces.append(ring)
    for x in (-1, 1):
        pieces.append(g.lathe("CageRod", [(0.003, 0.2), (0.003, 0.472)], (x * 0.037, 0, BORE_Z), metal, 8))
    for y in (0.476, 0.485, 0.494):
        pieces.append(g.lathe("MuzzleRib", [(0.019, y), (0.019, y + 0.003)], (0, 0, BORE_Z), black, 16))
    m.join_into(barrel, pieces)
    g.cut(barrel, [g.lathe("CrownBore", [(0.006, 0.47), (0.006, 0.51)], (0, 0, BORE_Z), black, 16)])
    m.attach(barrel, (0, 0.17, BORE_Z), receiver)
    condenser = glow_zone(coil(m, frost))
    m.attach(condenser, (0, 0.2, BORE_Z), receiver)
    m.marker("Muzzle", (0, 0.506, BORE_Z), parent=receiver)


def coolant_parts(m, receiver, metal, black, grey):
    """Rounded removable coolant flask, retaining straps, fill valve and pressure gauge."""
    tank = g.lathe(
        "Magazine",
        [(0.023, -0.02), (0.037, -0.01), (0.04, 0.0), (0.04, 0.145), (0.035, 0.158), (0.021, 0.166)],
        (0, 0, -0.099),
        grey,
        24,
    )
    parts = [
        g.lathe(
            "FillValve", [(0.011, 0.163), (0.011, 0.175), (0.016, 0.176), (0.016, 0.184)], (0, 0, -0.099), metal, 12
        )
    ]
    for y in (0.013, 0.127):
        parts.append(
            g.lathe(
                "TankStrap",
                [(0.041, y), (0.042, y + 0.003), (0.042, y + 0.013), (0.041, y + 0.016)],
                (0, 0, -0.099),
                black,
                16,
            )
        )
    for x in (-1, 1):
        parts.append(
            g.slab(
                "TankCradle",
                [
                    (0.01, -0.067),
                    (0.01, -0.025),
                    (0.147, -0.025),
                    (0.147, -0.067),
                    (0.134, -0.067),
                    (0.134, -0.04),
                    (0.023, -0.04),
                    (0.023, -0.067),
                ],
                0.006,
                metal,
                x=x * 0.028,
                bevel=0.0015,
            )
        )
    m.join_into(tank, parts)
    m.attach(tank, (0, 0.07, -0.03), receiver)


def pressure_gauge(m, receiver, metal, black, grey):
    """Raised analogue pressure dial separate from the removable flask."""
    gauge = g.lathe(
        "PressureGauge",
        [(0.019, 0.03), (0.02, 0.033), (0.02, 0.041), (0.018, 0.043)],
        (0, 0.11, 0.033),
        metal,
        20,
        axis="x",
    )
    face = g.lathe("GaugeFace", [(0.016, 0.043), (0.016, 0.044)], (0, 0.11, 0.033), grey, 20, axis="x")
    needle = g.slab(
        "GaugeNeedle", [(0.102, 0.031), (0.122, 0.038), (0.12, 0.04), (0.102, 0.033)], 0.001, black, x=0.045
    )
    m.join_into(gauge, [face, needle])
    m.attach(gauge, (0.03, 0.11, 0.033), receiver)


def controls(m, receiver, metal, black):
    """Raised open sights, charging sled and a separate trigger for the shared viewmodel."""
    bolt = g.slab("Bolt", g.rounded(-0.09, 0.03, -0.025, 0.054, 0.005), 0.008, metal, x=-0.034, bevel=0.001)
    knob = g.lathe(
        "ChargingKnob",
        [(0.006, -0.054), (0.008, -0.051), (0.008, -0.037), (0.006, -0.033)],
        (0, -0.055, 0.043),
        black,
        12,
        axis="x",
    )
    m.join_into(bolt, [knob])
    m.attach(bolt, (-0.034, -0.05, 0.043), receiver)
    trigger = g.slab(
        "Trigger",
        [(-0.052, -0.022), (-0.045, -0.022), (-0.048, -0.04), (-0.059, -0.054), (-0.065, -0.05), (-0.055, -0.037)],
        0.007,
        black,
        bevel=0.001,
    )
    m.attach(trigger, (0, -0.049, -0.022), receiver)
    sights = g.slab("IronSights", g.rounded(-0.12, 0.09, -0.096, 0.096, 0.001), 0.025, black)
    pieces = [g.slab("FrontPost", [(0.145, 0.092), (0.151, 0.092), (0.151, SIGHT_Z), (0.145, SIGHT_Z)], 0.003, metal)]
    for x in (-1, 1):
        pieces.append(
            g.slab(
                "RearEar",
                [(-0.117, 0.095), (-0.102, 0.095), (-0.102, 0.119), (-0.117, 0.119)],
                0.004,
                black,
                x=x * 0.008,
            )
        )
        pieces.append(
            g.slab(
                "FrontEar", [(0.14, 0.092), (0.157, 0.092), (0.154, 0.117), (0.143, 0.117)], 0.004, black, x=x * 0.01
            )
        )
    m.join_into(sights, pieces)
    m.attach(sights, (0, -0.11, 0.092), receiver)


def build(m) -> None:
    """Build a grounded field tool; a thin Fenlight coolant indicator carries the glow mask."""
    metal = m.material("GunMetal", m.GUN_METAL, metallic=0.8, roughness=0.4)
    black = m.material("MatteBlack", m.MATTE_BLACK, roughness=0.78)
    grey = m.material("GreyPolymer", m.srgb("#5F6D68"), roughness=0.8)
    frost = m.material("GunMetalKnurled", m.srgb("#CDEEE8"), metallic=0.4, roughness=0.75, glow=1.5)
    live = m.material("OlivePolymer", m.srgb("#8DFF3A"), roughness=0.55, glow=1.5)
    receiver = g.slab(
        "Receiver", [(-0.15, -0.017), (0.16, -0.017), (0.16, 0.005), (-0.15, 0.005)], 0.055, metal, bevel=0.002
    )
    m.join_into(receiver, receiver_parts(metal, black, grey))
    stock_parts(m, receiver, metal, black, grey)
    barrel_parts(m, receiver, metal, black, frost)
    coolant_parts(m, receiver, metal, black, grey)
    pressure_gauge(m, receiver, metal, black, grey)
    controls(m, receiver, metal, black)
    strips = []
    for side in (-1, 1):
        strip = g.slab("CoolantIndicator", g.rounded(-0.105, 0.069, 0.1, 0.072, 0.001), 0.001, live, x=side * 0.0325)
        strips.append(glow_zone(strip))
    m.join_into(receiver, strips)
    g.stamp(m, "cryo_lance", "Receiver", (-0.032, -0.085, 0.019), 0.085)
