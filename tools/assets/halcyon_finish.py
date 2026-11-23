"""Place material grain and legible graphics on named parts before their static meshes are joined."""

import fnmatch

import bpy
from halcyon_atlas import DEST, GRID, SLOTS

BASE = {
    "Steel": "steel",
    "Dark": "rubber",
    "Paint": "enamel",
    "Laminate": "laminate",
    "Olive": "olive",
    "Wood": "wood",
    "Paper": "paper",
    "SodiumPaint": "orange",
    "Alarm": "alarm",
    "Concrete": "concrete",
    "Vine": "vine",
}
# Face keys use Blender's local axes. A double-sided panel can be read from either approach.
# The patterns identify existing pieces of geometry. Other opaque metalwork shares the base grain.
FAMILIES = {
    "SupplyTruck": [
        ("Body", "+x", "cargo"),
        ("Body", "-x", "cargo_left"),
        ("Doors", "y", "tailgate"),
        ("Cab", "x", "cab"),
        ("Hood", "-y", "grille"),
        ("Windscreen", "y", "windshield"),
        ("SideGlass*", "x", "tinted"),
        ("Lamp*", "y", "headlight"),
        ("Wheel*Hub", "x", "hub"),
        ("Step*", "z", "deck"),
    ],
    "CrateStack CrateLarge CrateLong": [("*Stencil", "y", "freight")],
    "Bulkhead BulkheadWide": [("Plate*", "y", "access")],
    "DebrisPile": [("Cabinet", "y", "service")],
    "RollShutter": [("Housing", "y", "rail")],
    "VentGrate VentGrateWide": [("Louvre*", "z", "brushed"), ("Bolt*", "y", "hub")],
    "FreezerDoor": [("Leaf", "y", "cold"), ("Kick*", "y", "brushed")],
    "BodyBag": [("Bag", "*", "vinyl"), ("Shoulders", "*", "vinyl"), ("Tag", "z", "tag"), ("Zip", "z", "zipper")],
    "CatwalkOffice": [("Deck", "z", "deck"), ("Tread*", "z", "deck"), ("Window", "y", "tinted")],
    "Ceiling": [("Duct", "*", "foil"), ("Seam*", "*", "brushed"), ("Bundle*", "*", "braid"), ("Sag*", "*", "braid")],
    "FenlightSpill VineCeiling VinePillar VineWall VineWallSmall ResearchRoom": [
        ("Leaf*", "*", "leaf"),
        ("Mat", "z", "leaf"),
    ],
    "FloorCables": [("Cable*", "*", "braid")],
    "HangingStrip": [("Housing", "*", "brushed"), ("Tube", "*", "ceramic"), ("*Wire*", "*", "braid")],
    "HazardSign": [("Band", "-y", "sign")],
    "LabFloorWreck LabPapers": [("Sheet*", "z", "document"), ("Clipboard", "z", "log")],
    "MessSpill MessTable": [("Tray*", "z", "tray"), ("Cup*", "*", "cup")],
    "PipeRun3 PipeRun6": [("Water*", "*", "conduit"), ("Steam", "*", "foil"), ("Cable0", "*", "braid")],
    "ScreenPair": [("DeadFace", "y", "tinted"), ("Cable", "*", "braid")],
    "SpecimenVault": [("Hatch", "z", "hatch"), ("Vent*", "x", "vent"), ("Plate*", "y", "archive")],
    "WeaponRack WeaponRackCold": [("Backplate*", "y", "pinboard"), ("Stencil", "y", "labels")],
    "Barricade": [("Sandbag", "*", "vinyl")],
    "BigTankCracked BigTankShattered": [("Base", "xy", "tank"), ("Cap", "*", "brushed")],
    "CoveredGurney": [("DrapedSheet", "*", "linen")],
    "FallenBarrels": [("Standing", "xy", "drum"), ("Lying*", "xy", "tank")],
    "FilingCabinets": [("Front*", "-y", "drawer"), ("OpenDrawer", "-y", "drawer"), ("Folder*", "y", "file")],
    "Forklift": [("Hub*", "y", "hub"), ("Step*", "z", "deck"), ("Seat*", "*", "vinyl")],
    "FuelDrum": [("Drum", "xy", "drum"), ("Lid", "z", "brushed")],
    "GuardDesk LabBench": [
        ("Keyboard", "z", "keyboard"),
        ("Switcher", "z", "console"),
        ("Phone", "z", "cassette"),
        ("Logbook", "z", "log"),
        ("Binder", "z", "file"),
        ("Drawer*", "y", "drawer"),
    ],
    "HoldingCell": [("Lock", "y", "console"), ("Floor", "z", "deck")],
    "JarShelf": [("Lid*", "z", "labels"), ("Shelf*", "z", "brushed")],
    "KitchenLine": [("Burner*", "z", "burner"), ("Hood", "-z", "grille"), ("Splash", "y", "brushed")],
    "LockerRow": [("Door*", "-y", "locker")],
    "MilitaryCases": [("Long", "z", "case"), ("Case?", "z", "case"), ("Latch*", "y", "brushed")],
    "OverturnedTable": [("Top", "y", "laminate"), ("Foot*", "*", "brushed")],
    "ServingCounter": [("Pan*", "z", "meal"), ("Worktop", "z", "brushed")],
    "ToppledConsole": [("Desk", "z", "console"), ("Body", "x", "vent")],
    "VendingMachine": [("Body", "x", "menu"), ("Slot", "y", "console"), ("Can*", "xy", "cup")],
}
MODELS = {model: details for family, details in FAMILIES.items() for model in family.split()}


def _atlas_material():
    from build_models import material

    mat = material("FacilityFinish", (1, 1, 1, 1))
    tree = mat.node_tree
    node = tree.nodes.new("ShaderNodeTexImage")
    node.image = bpy.data.images.load(str(DEST / "facility_preview.jpg"))
    node.image.pack()
    tree.links.new(node.outputs["Color"], tree.nodes["Principled BSDF"].inputs["Base Color"])
    return mat


def _tile(part_rules, axis, normal, base):
    direction = "xyz"[axis]
    oriented = ("+" if normal > 0 else "-") + direction
    for faces, name in part_rules:
        if faces == "*" or (
            abs(normal) > 0.70 and (faces == oriented or (faces[0] not in "-+" and direction in faces))
        ):
            return SLOTS[name]
    return SLOTS[base]


def _project(part, rules, base):
    mesh = part.data
    layer = mesh.uv_layers.active or mesh.uv_layers.new(name="UVMap")
    coords = [vertex.co for vertex in mesh.vertices]
    low = [min(v[k] for v in coords) for k in range(3)]
    span = [max(1e-7, max(v[k] for v in coords) - low[k]) for k in range(3)]
    for face in mesh.polygons:
        axis = max(range(3), key=lambda k: abs(face.normal[k]))
        normal = face.normal[axis]
        slot = _tile(rules, axis, normal, base)
        h, v = ((1, 2), (0, 2), (0, 1))[axis]
        for loop in face.loop_indices:
            co = coords[mesh.loops[loop].vertex_index]
            u, t = (co[h] - low[h]) / span[h], (co[v] - low[v]) / span[v]
            if (axis == 0 and normal < 0) or (axis == 1 and normal > 0):
                u = 1 - u
            # Filter guard around each tile to avoid bleed through the first three mip levels.
            layer.data[loop].uv = ((slot % GRID + 0.03 + 0.94 * u) / GRID, 1 - (slot // GRID + 0.97 - 0.94 * t) / GRID)


def apply(model, parts):
    if model not in MODELS:
        return False
    atlas = _atlas_material()
    for part in parts:
        original = part.data.materials[0].name
        if original in BASE:
            rules = [(face, tile) for pattern, face, tile in MODELS[model] if fnmatch.fnmatchcase(part.name, pattern)]
            _project(part, rules, BASE[original])
            part.data.materials[0] = atlas
    return True
