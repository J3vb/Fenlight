"""Shape tools for detailed guns: side profiles, turned parts and rail teeth.

Guns read as real guns mostly from their side silhouette and their round parts.
`slab` extrudes a side outline (points in Y forward, Z up) across X, `lathe`
turns a radius profile around the Y axis. Both return a plain mesh object with
the material set, like `box` and `cylinder` in build_models.py.
"""

import itertools
import math

import bpy

# isort: split
# bpy must load before bmesh.
import bmesh
import gun_markings

MARKINGS_UV = "Markings"


def _object(name: str, bm, mat, parent):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    obj.parent = parent
    return obj


def _bevel(obj, width: float) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = width
    mod.segments = 2
    mod.limit_method = "ANGLE"
    mod.use_clamp_overlap = True
    mod.harden_normals = not bpy.context.scene.get("unfinished", False)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=1e-5)
    bm.to_mesh(obj.data)
    bm.free()


def slab(name: str, outline: list, width: float, mat, x: float = 0.0, bevel: float = 0.0, parent=None):
    """Extrudes the side `outline` [(y, z), ...] to a part `width` thick, centred on `x`."""
    bm = bmesh.new()
    face = bm.faces.new([bm.verts.new((x - width / 2, y, z)) for y, z in outline])
    geom = bmesh.ops.extrude_face_region(bm, geom=[face])["geom"]
    moved = [v for v in geom if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(width, 0.0, 0.0), verts=moved)
    obj = _object(name, bm, mat, parent)
    if bevel > 0.0:
        _bevel(obj, bevel)
    return obj


def contoured(name: str, outline: list, width: float, mat, roll: float):
    """Roll the shoulders of a grip, pad or wooden stock into its side profile.

    Each station retains the drawn outline. The long side rolls over the same
    distance as the short one, so the highlight follows the whole piece.
    """
    ys, zs = zip(*outline, strict=True)
    cy, cz = (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2
    ry, rz = max(ys) - cy, max(zs) - cz
    roll = min(roll, width * 0.47, ry * 0.75, rz * 0.75)
    bm = bmesh.new()
    rings = []
    for side in (-1, 1):
        for angle in (90, 65, 35, 0) if side < 0 else (0, 35, 65, 90):
            theta = math.radians(angle)
            x = side * (width * 0.5 - roll * (1.0 - math.sin(theta)))
            inset = roll * (1.0 - math.cos(theta))
            rings.append([bm.verts.new((x, y - (y - cy) * inset / ry, z - (z - cz) * inset / rz)) for y, z in outline])
    for a, b in itertools.pairwise(rings):
        for i in range(len(outline)):
            bm.faces.new((a[i - 1], a[i], b[i], b[i - 1]))
    bm.faces.new(rings[0])
    bm.faces.new(rings[-1])
    return _object(name, bm, mat, None)


def stock_shell(stations: list, body, rubber, checkering, wrist: float | None = None):
    """Loft the wrist and cheek through oval sections. The pad meets the same rim
    and the patterned panels occupy faces of the shell so they follow its curve.
    Stations run heel to nose: centre Y, top, bottom, half width, finish of next span.
    """
    bm = bmesh.new()
    rings = []
    count = 20
    for y, top, bottom, width, _finish in stations:
        ring = []
        # The sculpted cheek blends into the flatter wrist under the original glove pose.
        blend = 0.0 if wrist is None else max(0.0, min(1.0, (y - wrist) / 0.035))
        power = 0.78 - blend * 0.54
        for i in range(count):
            angle = math.tau * i / count
            side, up = math.cos(angle), math.sin(angle)
            x = width * math.copysign(abs(side) ** power, side)
            z = (top + bottom) / 2 + (top - bottom) / 2 * math.copysign(abs(up) ** power, up)
            ring.append(bm.verts.new((x, y, z)))
        rings.append(ring)
    for k, (a, b) in enumerate(itertools.pairwise(rings)):
        finish = stations[k][-1]
        for i in range(count):
            face = bm.faces.new((a[i - 1], a[i], b[i], b[i - 1]))
            on_side = abs(math.sin(math.tau * (i - 0.5) / count)) < 0.61
            face.material_index = 1 if finish == "pad" else (2 if finish == "panel" and on_side else 0)
    bm.faces.new(rings[0]).material_index = 1
    bm.faces.new(rings[-1])
    obj = _object("Stock", bm, body, None)
    obj.data.materials.append(rubber)
    obj.data.materials.append(checkering)
    return obj


def lathe(
    name: str,
    profile: list,
    at: tuple,
    mat,
    segments: int = 24,
    parent=None,
    axis: str = "y",
    turn: float = 0.0,
    closed: bool = False,
):
    """Turns `profile` [(radius, along), ...] around `axis` through `at`. Ends are capped.
    `turn` rotates the ring start (radians), so an 8-sided part can sit flat side up.
    `closed` joins the last ring back to the first instead of capping, for open tubes and hoods."""
    bm = bmesh.new()
    rings = []
    for radius, along in profile:
        ring = []
        for i in range(segments):
            a = turn + 2 * math.pi * i / segments
            u, v = radius * math.cos(a), radius * math.sin(a)
            local = {"y": (u, along, v), "x": (along, u, v), "z": (u, v, along)}[axis]
            ring.append(bm.verts.new(tuple(p + q for p, q in zip(local, at, strict=True))))
        rings.append(ring)
    pairs = list(itertools.pairwise(rings)) + ([(rings[-1], rings[0])] if closed else [])
    for a, b in pairs:
        for i in range(segments):
            j = (i + 1) % segments
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if not closed:
        bm.faces.new(rings[0])
        bm.faces.new(rings[-1])
    return _object(name, bm, mat, parent)


def teeth(start: float, end: float, low: float, high: float, pitch: float = 0.01) -> list:
    """Side outline of a toothed accessory rail from `start` to `end` (Y), base `low`, tops `high`."""
    points = [(start, low)]
    y = start
    while y + pitch <= end + 1e-6:
        gap = pitch * 0.45
        points += [(y, high), (y + pitch - gap, high), (y + pitch - gap, low + (high - low) * 0.35)]
        points += [(y + pitch, low + (high - low) * 0.35)]
        y += pitch
    points.append((y, low))
    return points


def rounded(y0: float, z0: float, y1: float, z1: float, r: float, steps: int = 3) -> list:
    """Outline of a rectangle with rounded corners (slots, plates, buttons)."""
    corners = [(y1 - r, z0 + r, -90), (y1 - r, z1 - r, 0), (y0 + r, z1 - r, 90), (y0 + r, z0 + r, 180)]
    points = []
    for cy, cz, start in corners:
        for i in range(steps + 1):
            a = math.radians(start + 90 * i / steps)
            point = (cy + r * math.cos(a), cz + r * math.sin(a))
            if not points or math.dist(point, points[-1]) > 1e-6:
                points.append(point)
    if math.dist(points[0], points[-1]) <= 1e-6:
        points.pop()
    return points


def cut(obj, cutters: list):
    """Subtracts closed world-space cutters, consuming them while keeping the target's pivot and parent."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.context.view_layer.update()
    for cutter in cutters:
        modifier = obj.modifiers.new("Machined", "BOOLEAN")
        modifier.operation = "DIFFERENCE"
        modifier.solver = "EXACT"
        modifier.object = cutter
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        bpy.data.objects.remove(cutter, do_unlink=True)
    mesh = bmesh.new()
    mesh.from_mesh(obj.data)
    bmesh.ops.dissolve_degenerate(mesh, edges=mesh.edges[:], dist=1e-5)
    bmesh.ops.recalc_face_normals(mesh, faces=mesh.faces[:])
    bmesh.ops.triangulate(mesh, faces=mesh.faces[:])
    mesh.to_mesh(obj.data)
    mesh.free()
    return obj


def paint(obj, alpha: float):
    """Gives only `obj` a white `Color` attribute with this alpha (0 = rarity inlay, 1 = plain).
    `join_into` fills the parts it joins that have no colour with plain white, so build order does not matter."""
    colors = obj.data.color_attributes.get("Color") or obj.data.color_attributes.new("Color", "FLOAT_COLOR", "CORNER")
    for color in colors.data:
        color.color = (1.0, 1.0, 1.0, alpha)
    return obj


def add_inlays(m, target, outline: list, width: float, x: float, mat) -> None:
    """Builds the two rarity inlay strips (side outline `outline`, at `-x` and `+x`) and joins them into `target`."""
    strips = [paint(slab("Inlay", outline, width, mat, x=side * x), 0.0) for side in (-1, 1)]
    m.join_into(target, strips)


def marking(name: str, rect: tuple, x: float, side: int, region: str, mat, thick: float = 0.0004):
    """A thin printed plate on a gun side: `rect` (y0, z0, y1, z1), outer face at `x + side * thick`.
    Its `Markings` UV map shows atlas `region` on the outer face, read left to right from that side."""
    y0, z0, y1, z1 = rect
    xs = (x, x + side * thick)
    bm = bmesh.new()
    v = {(i, j, k): bm.verts.new((xs[i], (y0, y1)[j], (z0, z1)[k])) for i in (0, 1) for j in (0, 1) for k in (0, 1)}
    quads = [
        ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)),
        ((0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)),
        ((0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)),
        ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)),
        ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)),
        ((0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)),
    ]
    faces = [bm.faces.new([v[c] for c in quad]) for quad in quads]
    bm.loops.layers.uv.new("UVMap")
    uv = bm.loops.layers.uv.new(MARKINGS_UV)
    u0, v0, u1, v1 = gun_markings.uv_rect(region)
    bu, bv, _, _ = gun_markings.uv_rect("black")
    for face in faces:
        for loop in face.loops:
            loop[uv].uv = (bu + 0.01, bv + 0.01)
    for loop in faces[0].loops:
        t = (loop.vert.co.y - y0) / (y1 - y0)
        t = t if side > 0 else 1.0 - t
        loop[uv].uv = (u0 + (u1 - u0) * t, v0 + (v1 - v0) * (loop.vert.co.z - z0) / (z1 - z0))
    return _object(name, bm, mat, None)


def inspection_plate(m, model: str, at: tuple, width: float):
    """Flush inspection plate on the visible side of its authored, animating mesh."""
    x, y, z = at
    half_height = width * 0.075
    rect = (y - width / 2, z - half_height, y + width / 2, z + half_height)
    ink = bpy.data.materials.get("Markings") or m.material("FactoryPrint", m.MATTE_BLACK, roughness=0.65)
    return marking("InspectionPlate", rect, x, -1 if x < 0 else 1, model, ink, thick=0.00055)


def stamp(m, model: str, target: str, at: tuple, width: float) -> None:
    m.join_into(bpy.data.objects[target], [inspection_plate(m, model, at, width)])


def red_dot(m, y: float, rail_top: float, eye: float, black, glass, markings, receiver) -> list:
    """Small Oriel holographic sight on the rail at `y`, its window centred on the eye line `eye`.
    Returns the parts to join into `receiver`; `SightGlass` and the `ReticleMount` marker stay separate."""
    base_top = rail_top + 0.008
    hood = [(0.0152, y - 0.014), (0.0192, y - 0.014), (0.0192, y + 0.016), (0.0152, y + 0.016)]
    parts = [
        slab(
            "RedDotBase",
            [(y - 0.03, rail_top), (y + 0.03, rail_top), (y + 0.027, base_top), (y - 0.027, base_top)],
            0.026,
            black,
            bevel=0.0015,
        ),
        slab("RedDotRiser", rounded(y - 0.012, base_top - 0.001, y + 0.014, eye - 0.016, 0.002), 0.014, black),
        lathe("RedDotHood", hood, (0, 0, eye), black, 8, turn=math.pi / 8, closed=True),
        lathe(
            "RedDotKnob",
            [(0.004, 0.0), (0.004, 0.006), (0.003, 0.007)],
            (0.013, y + 0.018, base_top - 0.004),
            black,
            10,
            axis="x",
        ),
    ]
    for side in (-1, 1):
        parts.append(
            marking(
                f"RedDotMark{side}",
                (y - 0.024, rail_top + 0.0005, y + 0.012, base_top - 0.0015),
                side * 0.013,
                side,
                "logo",
                markings,
            )
        )
    lathe("SightGlass", [(0.0156, y + 0.0035), (0.0156, y + 0.0045)], (0, 0, eye), glass, 16, parent=receiver)
    m.marker("ReticleMount", (0, y + 0.0025, eye), parent=receiver)
    return parts
