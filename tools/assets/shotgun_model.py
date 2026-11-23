"""BR-12 pump shotgun (`brenner_trench`): black receiver with rail and Oriel red dot, polymer stock with a
side shell holder, polymer pump with a tan front band, bare barrel over the magazine tube.

Static parts join into `Receiver`. The pump is the `Bolt` node so the viewmodel racks it;
there is no Magazine (shells load one by one through the loading port). `LoadShell` is the one shell the
support hand carries into the port on a reload (hidden until then). `SightGlass` and the
`ReticleMount` marker stay separate. Worn materials and the `Markings` atlas follow docs/plans/guns-concept.md.
"""

import gun_markings
import gun_parts as g

BORE_Z = 0.03
TUBE_Z = -0.005
RAIL_TOP = 0.058
EYE_Z = 0.089  # aim line: WeaponData.ads_position.y is -EYE_Z


def receiver(m, metal, black):
    """Receiver with ejection and loading ports, trigger group and cross-bolt safety."""
    body = g.slab(
        "Receiver",
        [(-0.085, -0.02), (0.125, -0.02), (0.125, 0.041), (0.105, 0.047), (-0.035, 0.047), (-0.085, 0.026)],
        0.05,
        black,
        bevel=0.002,
    )
    g.cut(body, [g.slab("PortCut", g.rounded(0.0, 0.004, 0.075, 0.034, 0.004), 0.024, black, x=0.027)])
    guard = [
        (0.012, -0.02),
        (0.012, -0.058),
        (-0.062, -0.058),
        (-0.078, -0.02),
        (-0.07, -0.02),
        (-0.058, -0.051),
        (0.005, -0.051),
        (0.005, -0.02),
    ]
    parts = [
        g.slab("PortFloor", g.rounded(0.001, 0.005, 0.074, 0.033, 0.003), 0.001, black, x=0.0155),
        g.slab("RailBase", [(-0.03, 0.046), (0.12, 0.046), (0.12, 0.051), (-0.03, 0.051)], 0.024, black),
        g.slab("RailTeeth", g.teeth(-0.027, 0.115, 0.051, RAIL_TOP), 0.021, black),
        g.slab("Breech", g.rounded(0.008, 0.009, 0.068, 0.028, 0.003), 0.002, metal, x=0.019),
        g.slab("LoadingPort", [(0.02, -0.022), (0.11, -0.022), (0.11, -0.019), (0.02, -0.019)], 0.034, black),
        g.slab("TriggerPlate", [(-0.08, -0.02), (0.02, -0.02), (0.02, -0.026), (-0.08, -0.026)], 0.03, black),
        g.slab("TriggerGuard", guard, 0.012, black, bevel=0.0015),
        g.slab(
            "Trigger",
            [(-0.03, -0.026), (-0.024, -0.026), (-0.026, -0.04), (-0.034, -0.05), (-0.038, -0.047), (-0.032, -0.038)],
            0.006,
            metal,
        ),
        g.lathe("Safety", [(0.005, -0.03), (0.005, 0.03)], (0.0, 0.01, -0.023), black, 12, axis="x"),
        g.lathe("ActionRelease", [(0.004, -0.031), (0.004, -0.025)], (0.0, -0.07, -0.012), metal, 10, axis="x"),
    ]
    for side in (-1, 1):
        for y in (-0.06, 0.1):
            parts.append(
                g.lathe(
                    f"Pin{side}{y}", [(0.004, -0.0015), (0.004, 0.0015)], (side * 0.025, y, 0.0), metal, 10, axis="x"
                )
            )
    m.join_into(body, parts)
    return body


def paint(obj, region: str):
    """Gives a solid part one flat colour from the markings atlas (shell red, brass)."""
    obj.data.uv_layers.new(name="UVMap")
    layer = obj.data.uv_layers.new(name=g.MARKINGS_UV)
    u0, v0, u1, v1 = gun_markings.uv_rect(region)
    for loop in layer.data:
        loop.uv = ((u0 + u1) / 2, (v0 + v1) / 2)
    return obj


def stock(metal, black, elastic, markings):
    """Black polymer stock with a slim wrist and rubber pad, and a four-shell elastic holder on the right."""
    outline = [
        (-0.085, 0.03),
        (-0.085, -0.02),
        (-0.105, -0.032),
        (-0.145, -0.058),
        (-0.2, -0.078),
        (-0.3, -0.1),
        (-0.372, -0.11),
        (-0.372, 0.018),
        (-0.3, 0.02),
        (-0.18, 0.018),
        (-0.12, 0.022),
    ]
    parts = [
        g.contoured("Stock", outline, 0.042, black, roll=0.016),
        g.contoured(
            "ButtPad", [(-0.37, 0.02), (-0.388, 0.022), (-0.39, -0.11), (-0.37, -0.112)], 0.046, black, roll=0.006
        ),
        g.lathe("Swivel", [(0.006, -0.105), (0.006, -0.085)], (0, -0.31, 0), metal, 10, axis="z"),
        g.slab("ShellBand", g.rounded(-0.33, -0.06, -0.215, 0.0, 0.006), 0.004, elastic, x=0.023, bevel=0.001),
    ]
    for i in range(4):
        y = -0.304 + i * 0.026
        parts.append(
            paint(
                g.lathe(f"Hull{i}", [(0.0092, -0.026), (0.0092, 0.03)], (0.034, y, -0.03), markings, 12, axis="z"),
                "shell",
            )
        )
        rim = [(0.0098, -0.04), (0.0098, -0.034), (0.0094, -0.033), (0.0094, -0.026)]
        parts.append(paint(g.lathe(f"Head{i}", rim, (0.034, y, -0.03), markings, 12, axis="z"), "brass"))
    return parts


def load_shell(m, markings, body):
    """One shell pointing up the tube, origin at its middle under the loading port."""
    at = (0, 0.04, TUBE_Z - 0.03)
    hull = paint(g.lathe("LoadShell", [(0.0092, 0.012), (0.0092, 0.068)], at, markings, 12), "shell")
    rim = [(0.0098, -0.002), (0.0098, 0.004), (0.0094, 0.005), (0.0094, 0.012)]
    head = paint(g.lathe("LoadShellHead", rim, at, markings, 12), "brass")
    m.join_into(hull, [head])
    m.attach(hull, (0, 0.075, TUBE_Z - 0.03), body)


def barrel(metal, black):
    """Barrel and magazine tube with its cap, and the band that ties them together."""
    pipe = g.lathe(
        "Barrel", [(0.0125, 0.125), (0.0115, 0.13), (0.0115, 0.62), (0.0105, 0.623)], (0, 0, BORE_Z), metal, 20
    )
    g.cut(pipe, [g.lathe("BoreCut", [(0.009, 0.59), (0.009, 0.63)], (0, 0, BORE_Z), metal, 20)])
    parts = [
        pipe,
        g.lathe("MagTube", [(0.011, 0.125), (0.011, 0.52)], (0, 0, TUBE_Z), metal, 16),
        g.lathe(
            "TubeCap",
            [
                (0.012, 0.518),
                (0.0135, 0.522),
                (0.0135, 0.53),
                (0.0125, 0.532),
                (0.0135, 0.534),
                (0.0135, 0.542),
                (0.011, 0.548),
            ],
            (0, 0, TUBE_Z),
            black,
            16,
        ),
        g.slab("BarrelBand", g.rounded(0.495, -0.018, 0.515, 0.044, 0.006), 0.03, black, bevel=0.002),
    ]
    return parts


def pump(m, black, tan, body):
    """Grooved polymer pump with a smooth tan front band, and the action bars that run back into the receiver."""
    profile = [(0.019, 0.19), (0.0225, 0.196)]
    for i in range(6):
        y = 0.2 + i * 0.014
        profile += [(0.0225, y + 0.009), (0.0205, y + 0.01), (0.0205, y + 0.013), (0.0225, y + 0.014)]
    profile += [(0.0225, 0.286)]
    grip = g.lathe("Bolt", profile, (0, 0, TUBE_Z), black, 20)
    band = g.lathe("PumpBand", [(0.0225, 0.286), (0.0225, 0.33), (0.019, 0.336)], (0, 0, TUBE_Z), tan, 20)
    bars = [
        g.slab(
            f"ActionBar{s}", [(0.1, -0.012), (0.2, -0.012), (0.2, -0.004), (0.1, -0.004)], 0.002, black, x=s * 0.0125
        )
        for s in (-1, 1)
    ]
    m.join_into(grip, [band, *bars])
    m.attach(grip, (0, 0.26, TUBE_Z), body)


def build(m) -> None:
    metal = m.material("GunMetalWorn", m.GUN_METAL, metallic=0.8, roughness=0.4)
    black = m.material("MatteBlackWorn", m.MATTE_BLACK, roughness=0.75)
    tan = m.material("TanWorn", m.TAN, roughness=0.8)
    elastic = m.material("MatteBlackKnurledWorn", m.MATTE_BLACK, roughness=0.85)
    glass = m.material("SightGlass", m.LENS, metallic=0.3, roughness=0.05)
    markings = m.material("Markings", m.MATTE_BLACK, roughness=0.7)
    body = receiver(m, metal, black)
    logos = [g.marking(f"Logo{s}", (0.025, -0.017, 0.068, -0.001), s * 0.025, s, "logo", markings) for s in (-1, 1)]
    m.join_into(body, logos + stock(metal, black, elastic, markings) + barrel(metal, black))
    m.join_into(body, g.red_dot(m, 0.04, RAIL_TOP, EYE_Z, black, glass, markings, body))
    pump(m, black, tan, body)
    load_shell(m, markings, body)
    m.marker("Muzzle", (0, 0.625, BORE_Z), parent=body)
    g.add_inlays(m, body, g.rounded(-0.028, 0.040, 0.096, 0.042, 0.0008), 0.001, 0.025, metal)
    g.stamp(m, "shotgun_brenner", "Receiver", (-0.025, -0.04, 0.016), 0.085)
