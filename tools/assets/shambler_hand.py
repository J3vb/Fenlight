"""Reach pose for the lab technician's curled striking hand, in its fitted wrist frame."""

import math

from mathutils import Vector


def _ease(low, high, value):
    t = min(1.0, max(0.0, (value - low) / (high - low)))
    return t * t * (3.0 - 2.0 * t)


def _release(length, width, depth):
    """Wrist-local metres. The knuckle row slopes from the little finger toward the index finger."""
    knuckle = 0.133 + 0.65 * width
    lever = length - knuckle
    lift = depth - 0.033
    # Curled fingertips lie in front of the palm. Blend the proximal row into the stationary palm.
    distal = _ease(-0.014, 0.025, max(lever, lift * 0.85))
    fingers = 1.0 - _ease(0.023, 0.053, width)
    angle = math.radians(44.0) * distal * fingers
    c, s = math.cos(angle), math.sin(angle)
    opened = lever * c + lift * s
    uncurl = lift * c - lever * s
    spread = (width + 0.014) * 0.19 * distal * fingers
    # Abduct the thumb slightly as the four fingers open.
    thumb = _ease(0.045, 0.074, width) * _ease(0.09, 0.15, length)
    return Vector((opened - lever, spread + 0.008 * thumb, uncurl - lift))


def add_reach(body, arm):
    """Add the right-hand shape to the fitted lab tech before its final glTF export."""
    hand = arm.data.bones["hand_R"]
    wrist = arm.matrix_world @ hand.head_local
    along = (arm.matrix_world.to_3x3() @ (hand.tail_local - hand.head_local)).normalized()
    forward = Vector((0.0, -1.0, 0.0))
    palm = (forward - along * forward.dot(along)).normalized()
    across = along.cross(palm)
    group = body.vertex_groups["hand_R"].index
    to_mesh = body.matrix_world.to_3x3().inverted()
    body.shape_key_add(name="Basis", from_mix=False)
    key = body.shape_key_add(name="ReachFingers", from_mix=False)
    for vertex in body.data.vertices:
        weight = next((g.weight for g in vertex.groups if g.group == group), 0.0)
        if weight:
            p = (body.matrix_world @ vertex.co) - wrist
            d = _release(p.dot(along), p.dot(across), p.dot(palm))
            key.data[vertex.index].co += to_mesh @ (along * d.x + across * d.y + palm * d.z) * weight
