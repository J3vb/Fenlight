"""Support glove cupping a small prop, in the hand's own flexion plane."""

import math

from mathutils import Vector
from player_grip_frames import rest_frame


def finger_path(root, index):
    """Bend the three phalanges toward the palm; keep their lengths through the curl."""
    _across, forward, inward = rest_frame(1)
    length = (0.077, 0.083, 0.076, 0.063)[index]
    angles = ((12, 55, 88), (18, 63, 94), (26, 71, 102), (32, 76, 108))[index]
    points = [root]
    for fraction, degrees in zip((0.45, 0.32, 0.23), angles, strict=True):
        angle = math.radians(degrees)
        step = (forward * math.cos(angle) + inward * math.sin(angle)) * (length * fraction / 3)
        for _ in range(3):
            points.append(points[-1] + step)
    return points


def thumb_path():
    across, forward, inward = rest_frame(1)
    palm = Vector((0.649, 0, 1.011))
    sections = (
        (-0.026, 0.005, 0.010),
        (-0.036, 0.016, 0.019),
        (-0.041, 0.030, 0.034),
        (-0.039, 0.044, 0.049),
        (-0.033, 0.059, 0.057),
        (-0.027, 0.071, 0.060),
    )
    return [palm + across * x + forward * y + inward * z for x, y, z in sections]
