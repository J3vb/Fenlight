"""Serialize the room fixtures as editable Godot scene resources."""

from math import atan2, degrees, hypot, radians

from halcyon_dressing_batches import batch_hardware

SHARED = ("wood", "steel", "pipe", "rubber")


def resource(name):
    kind = "ExtResource" if name in SHARED else "SubResource"
    return f'{kind}("{name}")'


def num(x):
    return f"{x:.6f}".rstrip("0").rstrip(".") if x else "0"


def vector(x):
    return "Vector3(" + ", ".join(num(v) for v in x) + ")"


def color(x):
    return "Color(" + ", ".join(num(v) for v in x) + ", 1)"


def _external_resources():
    resources = ["[gd_scene format=3]"]

    def ext(t, path, id):
        resources.append(f'[ext_resource type="{t}" path="res://{path}" id="{id}"]')

    for m in SHARED:
        ext("Material", "levels/materials/" + m + ".tres", m)
    ext("Texture2D", "assets/textures/story/dressing_prints.png", "atlas")
    ext("Texture2D", "assets/textures/halcyon/decal_scuffs.png", "scuffed")
    for m in ("painted_metal", "smudge", "brushed_steel", "rubber"):
        for channel in ("albedo", "normal"):
            ext("Texture2D", f"assets/textures/halcyon/{m}_{channel}.png", f"{m}_{channel}")

    return resources


def _resources():
    resources = _external_resources()

    def sub(t, id, **props):
        resources.extend(["", f'[sub_resource type="{t}" id="{id}"]'] + [f"{k} = {v}" for k, v in props.items()])

    def tex(id):
        return f'ExtResource("{id}")'

    for name, texture, tint, rough, metal in (
        ("teal", "painted_metal", (0.33, 0.64, 0.60), 0.48, 0.12),
        ("ochre", "rubber", (0.95, 0.61, 0.26), 0.68, 0.05),
        ("ceramic", "smudge", (0.85, 0.86, 0.73), 0.32, 0.04),
        ("frozen", "smudge", (0.68, 0.88, 0.91), 0.3, 0.15),
        ("brass", "brushed_steel", (0.95, 0.73, 0.38), 0.43, 0.55),
        ("navy", "rubber", (0.25, 0.36, 0.39), 0.95, 0),
        ("green_metal", "painted_metal", (0.56, 0.64, 0.51), 0.5, 0.34),
    ):
        sub(
            "StandardMaterial3D",
            name,
            albedo_texture=tex(texture + "_albedo"),
            albedo_color=color(tint),
            normal_enabled="true",
            normal_texture=tex(texture + "_normal"),
            normal_scale=0.45,
            roughness=rough,
            metallic=metal,
            uv1_triplanar="true",
            uv1_world_triplanar="true",
        )
    for name, tint in (("sodium_lamp", (1, 0.65, 0.34)), ("fluorescent", (0.77, 0.92, 0.88))):
        sub(
            "StandardMaterial3D",
            name,
            albedo_color=color(tint),
            albedo_texture=tex("smudge_albedo"),
            emission_enabled="true",
            emission=color(tint),
            emission_energy_multiplier=1.45,
            roughness=0.49,
        )
    sub("StandardMaterial3D", "scrapes", albedo_texture=tex("scuffed"), transparency=1, cull_mode=2, roughness=0.42)
    tiles = (
        "freight keys menu wayfinding generator service frost transfer "
        "treads caster spill log descent patch curtain drain"
    ).split()
    for i, m in enumerate(tiles):
        sub(
            "StandardMaterial3D",
            m,
            albedo_texture=tex("atlas"),
            uv1_scale=vector((0.247, 0.247, 1)),
            uv1_offset=vector(((i % 4) / 4 + 0.0015, (i // 4) / 4 + 0.0015, 0)),
            transparency=1,
            cull_mode=2,
            roughness=0.24 if m == "spill" else 0.68,
        )
    for kind, t, params in (
        ("block", "BoxMesh", {}),
        ("card", "QuadMesh", {}),
        ("rod", "CylinderMesh", dict(top_radius=0.5, bottom_radius=0.5, height=1, radial_segments=16, rings=0)),
        ("rim", "TorusMesh", dict(inner_radius=0.39, outer_radius=0.5, rings=20, ring_segments=8)),
        ("cone", "CylinderMesh", dict(top_radius=0.32, bottom_radius=0.5, height=1, radial_segments=16, rings=0)),
        ("shard", "PrismMesh", dict(size=vector((1, 1, 1)), left_to_right=0.12)),
    ):
        sub(t, kind, **params)
    return resources


class DressingScene:
    def __init__(self):
        self.lines = []
        self.colliders = []
        self.current = "."
        self.node("RoomDressing", "Node3D")

    def render(self):
        text = "\n".join(_resources() + self.lines) + "\n"
        return batch_hardware(text)

    def collision_box(self, name, position, size, rotation=(0, 0, 0)):
        self.colliders.append((name, position, size, rotation))

    def render_collision(self):
        resources = ["[gd_scene format=3]"]
        nodes = ['[node name="RoomFixtureCollision" type="Node3D"]']
        for name, position, size, rotation in self.colliders:
            resources.extend(("", f'[sub_resource type="BoxShape3D" id="{name}"]', f"size = {vector(size)}"))
            nodes.extend(
                (
                    "",
                    f'[node name="{name}" type="StaticBody3D" parent="."]',
                    f"position = {vector(position)}",
                    "collision_mask = 0",
                )
            )
            if any(rotation):
                nodes.append(f"rotation = {vector(tuple(radians(v) for v in rotation))}")
            nodes.extend(
                ("", f'[node name="Shape" type="CollisionShape3D" parent="{name}"]', f'shape = SubResource("{name}")')
            )
        return "\n".join([*resources, "", *nodes]) + "\n"

    def node(self, n, t, p=None, group=None, **props):
        tail = (f' parent="{p}"' if p else "") + (f' groups=["{group}"]' if group else "")
        self.lines.extend(["", f'[node name="{n}" type="{t}"{tail}]'] + [f"{k} = {v}" for k, v in props.items()])

    def room(self, n):
        self.current = n
        self.node(n, "Node3D", ".")

    def shape(self, n, kind, p, size, m, rot=(0, 0, 0), pwr=False, reach=25, walk_through=None, solid=False):
        if solid:
            self.collision_box(n, p, size, rot)
        props = {"position": vector(p)}
        if any(rot):
            props["rotation"] = vector(tuple(radians(v) for v in rot))
        props.update(
            scale=vector(size),
            cast_shadow=0,
            gi_mode=0,
            visibility_range_end=reach,
            material_override=resource(m),
            mesh=resource(kind),
        )
        if walk_through:
            props["metadata/walk_through"] = f'"{walk_through}"'
        self.node(
            n,
            "MeshInstance3D",
            self.current,
            "mains_light" if pwr else ("emergency_light" if n in ("EmergencyLens", "EmergencyPool") else None),
            **props,
        )

    def box(self, n, p, size, m, rot=(0, 0, 0), **kw):
        self.shape(n, "block", p, size, m, rot, **kw)

    def rod(self, n, p, size, m, rot=(0, 0, 0), **kw):
        self.shape(n, "rod", p, size, m, rot, **kw)

    def ring(self, n, p, size, m, rot=(0, 0, 0)):
        self.shape(n, "rim", p, size, m, rot)

    def card(self, n, p, size, m, rot=(0, 0, 0), **kw):
        self.shape(n, "card", p, (*size, 1), m, rot, **kw)

    def floor(self, n, p, size, m, yaw=0):
        self.card(n, p, size, m, (-90, yaw, 0))

    def bar(self, n, a, b, d, m):
        delta = [b[i] - a[i] for i in range(3)]
        length = hypot(*delta)
        rot = (degrees(atan2(hypot(delta[0], delta[2]), delta[1])), degrees(atan2(delta[0], delta[2])), 0)
        self.rod(n, tuple((a[i] + b[i]) / 2 for i in range(3)), (d, length, d), m, rot)

    def light(self, n, p, tint, energy, r, pwr=True, fog=0.14):
        self.node(
            n,
            "OmniLight3D",
            self.current,
            "mains_light" if pwr else ("emergency_light" if n in ("EmergencyLens", "EmergencyPool") else None),
            position=vector(p),
            light_color=color(tint),
            light_energy=energy,
            light_specular=0.65,
            light_volumetric_fog_energy=fog,
            light_bake_mode=0,
            distance_fade_enabled="true",
            distance_fade_begin=15,
            distance_fade_length=8,
            omni_range=r,
            omni_attenuation=1.2,
        )

    def strip(self, n, p, width, warm=False):
        x, y, z = p
        self.box(n + "Housing", (x, y + 0.045, z), (width + 0.16, 0.12, 0.20), "steel")
        self.box(
            n + "Lens",
            (x, y - 0.025, z + 0.023),
            (width, 0.045, 0.16),
            "sodium_lamp" if warm else "fluorescent",
            pwr=True,
        )
