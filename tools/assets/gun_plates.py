"""Original receiver stamps for the Cold Containment markings sheet, on a 256-unit layout."""

import itertools

# Fixed atlas slots. Service issue uses an Oriel hex, sporting stocks a leaf,
# and lab equipment a split diamond. Keep the layouts clear at small mip levels.
STAMPS = {
    "rifle_ar": ("AR-17", "issue"),
    "shotgun_brenner": ("BR-12", "issue"),
    "kestrel_smg": ("VX-9", "issue"),
    "talon_dmr": ("MR-28", "issue"),
    "warden_p9": ("M-9", "issue"),
    "wren_mp": ("WREN MP", "issue"),
    "hollis_44": ("HOLLIS .44", "sport"),
    "coachman_2b": ("COACHMAN", "sport"),
    "grubber_sawnoff": ("GRUBBER", "sport"),
    "fieldhand_lever": ("FIELDHAND", "sport"),
    "halberd_lmg": ("HALBERD", "issue"),
    "bastion_lmg": ("BASTION", "issue"),
    "mako_pdw": ("MAKO PDW", "issue"),
    "rampart_br": ("RAMPART", "issue"),
    "atlas_auto": ("ATLAS AUTO", "issue"),
    "sentry_br3": ("SENTRY", "issue"),
    "corvid_338": ("CORVID .338", "issue"),
    "ironwood_50": ("IRONWOOD .50", "issue"),
    "nightjar_sd": ("NIGHTJAR SD", "issue"),
    "siphon": ("SIPHON", "lab"),
    "cryo_lance": ("CRYO LANCE", "lab"),
    "synapse": ("SYNAPSE", "lab"),
}

# Five-row punched lettering, drawn in the same units as the inspection marks.
GLYPHS = {
    "A": "6/9/F/9/9",
    "B": "E/9/E/9/E",
    "C": "7/8/8/8/7",
    "D": "E/9/9/9/E",
    "E": "F/8/E/8/F",
    "F": "F/8/E/8/8",
    "G": "7/8/B/9/7",
    "H": "9/9/F/9/9",
    "I": "7/2/2/2/7",
    "J": "3/1/1/9/6",
    "K": "9/A/C/A/9",
    "L": "8/8/8/8/F",
    "M": "9/F/F/9/9",
    "N": "9/D/B/9/9",
    "O": "6/9/9/9/6",
    "P": "E/9/E/8/8",
    "R": "E/9/E/A/9",
    "S": "7/8/6/1/E",
    "T": "F/2/2/2/2",
    "U": "9/9/9/9/6",
    "V": "9/9/9/6/6",
    "W": "9/9/F/F/9",
    "X": "9/9/6/9/9",
    "Y": "9/9/6/2/2",
    "0": "6/B/9/D/6",
    "1": "2/6/2/2/7",
    "2": "E/1/6/8/F",
    "3": "E/1/6/1/E",
    "4": "A/A/F/2/2",
    "5": "F/8/E/1/E",
    "6": "7/8/E/9/6",
    "7": "F/1/2/4/4",
    "8": "6/9/6/9/6",
    "9": "6/9/7/1/E",
    "-": "0/0/7/0/0",
    ".": "0/0/0/0/2",
    " ": "0/0/0/0/0",
}


def rect(index):
    x = 2 + index % 3 * 84
    y = 66 + index // 3 * 15
    return x, y, x + 80, y + 12


def text(img, x, y, string, scale, ink):
    for char in string:
        for r, row in enumerate(GLYPHS[char].split("/")):
            for c in range(4):
                if int(row, 16) & (8 >> c):
                    for dy in range(scale):
                        img[y + r * scale + dy][x + c * scale : x + (c + 1) * scale] = [ink] * scale
        x += scale * 5


def draw(img, line):
    for index, (name, family) in enumerate(STAMPS.values()):
        x0, y0, _, _ = rect(index)
        x, y = x0 * 4, y0 * 4
        light = (185, 184, 171)
        accent = {"issue": (169, 161, 134), "sport": (181, 148, 92), "lab": (196, 164, 77)}[family]
        for row in range(48):
            for col in range(320):
                # Rolled steel, an impressed rim and a few rubbed longitudinal streaks.
                value = 36 + ((row * 79 + col // 27 + index * 5) % 9)
                if row in (1, 46) or col in (1, 318):
                    value = 68
                img[y + row][x + col] = (value, value + 1, value)
        if family == "sport":
            points = [(6, 24), (18, 12), (32, 9), (25, 24), (12, 31), (6, 24), (28, 14)]
        elif family == "lab":
            points = [(7, 24), (20, 8), (33, 24), (20, 39), (7, 24), (26, 24)]
        else:
            points = [(8, 16), (20, 9), (32, 16), (32, 30), (20, 37), (8, 30), (8, 16)]
        for a, b in itertools.pairwise(points):
            line(img, (x + a[0], y + a[1]), (x + b[0], y + b[1]), 1.8, accent)
        text(img, x + 44, y + 8, name, 4, light)
        text(img, x + 45, y + 34, ("ORIEL" if family != "sport" else "NO.") + f"  {index + 1:03}", 1, accent)
        for col in range(274, 305, 4):
            height = 4 + ((col * 13 + index) % 5) * 3
            for row in range(36 - height, 37):
                img[y + row][x + col : x + col + 2] = [accent] * 2
