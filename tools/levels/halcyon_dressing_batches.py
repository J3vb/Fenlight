"""Merge repeated static hardware by room, material and mesh for Godot MultiMesh."""

import math
import re

import numpy as np

BATCHES = (
    ("PalletRunner", "PalletSkids"),
    ("DeckBoard", "DeckBoards"),
    ("FreightWebbing", "LooseWebbing"),
    ("ConduitCleat", "ConduitCleats"),
    ("WorkGuard", "ReflectorGrille"),
    ("SealedSample", "Samples"),
    ("SampleCollar", "SampleLabels"),
    ("SampleCap", "SampleCaps"),
    ("LaggingBand", "InsulationBands"),
    ("WheelSpoke", "ValveSpokes"),
    ("CurtainRing", "CurtainRings"),
    ("VesselFragment", "BrokenGlass"),
    ("WallStay", "RailBrackets"),
    ("EmergencyCage", "LensCage"),
    ("KerbMarker", "KerbMarkers"),
    ("Bolt", "PatchBolts"),
    ("ReserveTin", "ReserveTins"),
    ("Seal", "ColdShelfSeals"),
    ("BatchTag", "BatchTags"),
)


def _vector(node, field, default):
    value = re.search(rf"^{field} = Vector3\(([^)]+)\)", node, re.M)
    return np.fromstring(value[1], sep=",") if value else np.array(default)


def _numbers(values):
    return ", ".join(f"{v:.6f}".rstrip("0").rstrip(".") if abs(v) > 0.000001 else "0" for v in values)


def _transform_values(node, offset):
    angles = _vector(node, "rotation", (0, 0, 0))
    cx, cy, cz = map(math.cos, angles)
    sx, sy, sz = map(math.sin, angles)
    rotation = (
        np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
        @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
        @ np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    )
    basis = rotation @ np.diag(_vector(node, "scale", (1, 1, 1)))
    return np.column_stack((basis, offset)).ravel()


def _batch(parts, name, room, mesh, material):
    positions = [_vector(node, "position", (0, 0, 0)) for node in parts]
    center = np.mean(positions, axis=0)
    transforms = [_transform_values(node, pos - center) for node, pos in zip(parts, positions, strict=True)]
    key = room + name
    resource = (
        f'[sub_resource type="MultiMesh" id="{key}"]\ntransform_format = 1\n'
        f"instance_count = {len(parts)}\nmesh = {mesh}\n"
        f"buffer = PackedFloat32Array({_numbers(np.concatenate(transforms))})\n\n"
    )
    instance = (
        f'[node name="{name}" type="MultiMeshInstance3D" parent="{room}"]\nposition = Vector3({_numbers(center)})\n'
        f"cast_shadow = 0\ngi_mode = 0\nvisibility_range_end = 25\nmaterial_override = {material}\n"
        f'multimesh = SubResource("{key}")\n\n'
    )
    return resource, instance


def batch_hardware(text):
    resources, raw_nodes = text.split("[node ", 1)
    nodes = ["[node " + section for section in raw_nodes.split("[node ")]
    for prefix, name in BATCHES:
        pattern = re.compile(rf'^\[node name="{prefix}\d+" type="MeshInstance3D" parent="([^"]+)"\]')
        by_room = {}
        for node in nodes:
            match = pattern.match(node)
            if match:
                by_room.setdefault(match[1], []).append(node)
        for room, parts in by_room.items():
            meshes = {re.search(r"^mesh = (.+)$", node, re.M)[1] for node in parts}
            materials = {re.search(r"^material_override = (.+)$", node, re.M)[1] for node in parts}
            (mesh,) = meshes
            (material,) = materials
            resource, instance = _batch(parts, name, room, mesh, material)
            resources += resource
            nodes[nodes.index(parts[0])] = instance
            nodes = [node for node in nodes if node not in parts]
    return resources + "".join(nodes)
