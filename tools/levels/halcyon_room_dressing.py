"""Build the room-by-room Halcyon Labs dressing from its fixture placements.

Run python tools/levels/halcyon_room_dressing.py to regenerate the packed scene.
"""

from pathlib import Path

from halcyon_dressing_scene import DressingScene, resource

warm = (1, 0.68, 0.38)
cold = (0.62, 0.86, 1)
white = (0.84, 0.95, 0.90)


def loading_dock(scene):
    scene.room("LoadingDock")
    # A split pallet has skids under its boards and a loose strap laid over one corner.
    for i, x in enumerate((29.0, 29.57, 30.14)):
        scene.box(f"PalletRunner{i + 1}", (x, 0.072, 57.89), (0.11, 0.144, 1.01), "wood")
    for i in range(5):
        x = 29.58 if i < 4 else 29.39
        scene.box(
            f"DeckBoard{i + 1}",
            (x, 0.166, 57.45 + i * 0.225),
            (1.4 if i < 4 else 0.98, 0.045, 0.17),
            "wood",
            (0, (-1, 1, 0, -2, 4)[i], 0),
        )
    scene.box("SnappedBoard", (30.21, 0.109, 58.36), (0.42, 0.048, 0.16), "wood", (0, 12, -16))
    for i, (x, z, length, yaw, y) in enumerate(
        ((29.64, 57.91, 0.84, 21, 0.198), (29.85, 58.33, 0.33, 55, 0.185), (30.12, 58.50, 0.35, 72, 0.048))
    ):
        scene.box(f"FreightWebbing{i + 1}", (x, y, z), (0.072, 0.012, length), "ochre", (0, yaw, -4))
    scene.box("StrapBuckle", (29.66, 0.208, 57.99), (0.105, 0.029, 0.085), "brass", (0, 21, 0))
    scene.floor("ForkliftTurn", (32.06, 0.014, 55.53), (3.35, 6.1), "treads", -34)
    scene.floor("DockSlip", (29.15, 0.194, 57.78), (0.30, 0.22), "freight", 17)
    scene.card("ReceivingMark", (25.45, 2.38, 46.215), (3.9, 2.12), "freight")
    scene.box("DockCanopy", (25.6, 3.59, 46.39), (4.25, 0.16, 0.42), "green_metal")
    scene.strip("ReceivingLight", (26.75, 3.5, 46.49), 1.19, True)
    scene.light("ReceivingPool", (26.8, 3.06, 47.28), warm, 3.7, 7.8)
    # Amber work lamp on a side pillar washes the cargo flank, behind the existing truck.
    scene.box("ServiceBacking", (22.22, 2.33, 57.24), (0.10, 0.65, 0.45), "steel")
    scene.box("ServiceGlass", (22.29, 2.35, 57.24), (0.08, 0.34, 0.16), "sodium_lamp", pwr=True)
    scene.light("CabRim", (22.65, 2.45, 57.08), warm, 2.5, 7)


def guard_post(scene):
    scene.room("GuardPost")
    for i, x in enumerate((16.71, 17.86)):
        scene.box(f"BoardBracket{i}", (x, 1.21, 39.55), (0.043, 0.91, 0.07), "steel")
    scene.box("KeyCabinet", (17.29, 1.91, 39.58), (1.64, 1.03, 0.125), "green_metal")
    scene.card("KeyRegister", (17.29, 1.91, 39.649), (1.6, 1.0), "keys")
    scene.rod("LampFoot", (17.92, 0.80, 40.27), (0.19, 0.075, 0.19), "rubber")
    scene.bar("LampLowerArm", (17.92, 0.82, 40.27), (18.08, 1.25, 40.16), 0.032, "brass")
    scene.bar("LampUpperArm", (18.08, 1.25, 40.16), (17.75, 1.46, 40.13), 0.035, "steel")
    scene.shape("LampReflector", "cone", (17.72, 1.42, 40.14), (0.26, 0.14, 0.24), "green_metal", (12, 0, -18))
    scene.rod("TaskBulb", (17.70, 1.35, 40.15), (0.15, 0.035, 0.14), "sodium_lamp", (12, 0, -18), pwr=True)
    scene.light("DeskPool", (17.46, 1.42, 40.56), warm, 0.85, 4.3)
    scene.floor("ClippedRoster", (16.23, 0.772, 40.30), (0.31, 0.21), "log", 8)
    scene.box("CaughtSleeve", (21.03, 1.29, 38.29), (0.07, 0.39, 0.17), "navy", (-18, 0, 10))
    scene.box("SleeveCuff", (20.99, 1.11, 38.35), (0.077, 0.055, 0.17), "teal", (-18, 0, 10))


def mess_hall(scene):
    scene.room("MessHall")
    # Table service under a short suspended twin-bulb warm rail.
    for i, x in enumerate((44.39, 45.65)):
        scene.bar(f"HeatRailDrop{i}", (x, 5.82, 40.57), (x, 2.60, 40.57), 0.025, "pipe")
    scene.box("HeatRail", (45.02, 2.57, 40.57), (1.38, 0.061, 0.11), "steel")
    for i, x in enumerate((44.57, 45.48)):
        scene.shape(f"HeatShade{i}", "cone", (x, 2.46, 40.57), (0.28, 0.17, 0.28), "green_metal")
        scene.rod(f"HeatLamp{i}", (x, 2.37, 40.57), (0.21, 0.022, 0.21), "sodium_lamp", pwr=True)

    scene.box("MenuFrame", (49.0, 3.12, 30.25), (3.08, 1.12, 0.12), "green_metal")
    scene.card("NightMenu", (49, 3.12, 30.32), (3.02, 1.08), "menu")
    scene.strip("PassLamp", (49, 2.67, 31.41), 1.65, True)

    scene.floor("SpilledCoffee", (44.55, 0.783, 40.54), (0.91, 0.72), "spill", 29)
    scene.rod("CupOnSide", (44.7, 0.849, 40.50), (0.13, 0.17, 0.13), "ceramic", (75, -28, 0))
    scene.rod("CupInterior", (44.66, 0.872, 40.575), (0.112, 0.006, 0.112), "rubber", (75, -28, 0))
    scene.ring("CupHandle", (44.64, 0.858, 40.43), (0.095, 0.075, 0.096), "ceramic", (90, 0, -30))
    scene.rod("Saucer", (45.0, 0.79, 40.26), (0.21, 0.02, 0.21), "ceramic")
    scene.floor("MealTicket", (44.36, 0.788, 40.70), (0.16, 0.11), "log", 11)
    for i, (x, z, turn) in enumerate(((44.18, 40.31, -9), (45.43, 40.68, 12))):
        scene.box(f"EnamelTray{i}", (x, 0.798, z), (0.40, 0.027, 0.29), "green_metal", (0, turn, 0))
        scene.rod(f"DinnerPlate{i}", (x - 0.04, 0.825, z), (0.226, 0.026, 0.226), "ceramic")
        scene.ring(f"PlateLip{i}", (x - 0.04, 0.839, z), (0.208, 0.037, 0.208), "ceramic")
        scene.box(f"FoldedNapkin{i}", (x + 0.115, 0.825, z), (0.078, 0.016, 0.17), "ceramic", (0, turn + 5, 0))


def main_corridor(scene):
    scene.room("MainCorridor")
    for i, (a, b) in enumerate(((21.18, 42.82), (45.18, 47.78))):
        for name, y, h, m in (("DepartmentBand", 1.62, 0.43, "teal"), ("LowerRule", 1.345, 0.048, "ceramic")):
            scene.box(f"{name}{i}", ((a + b) / 2, y, 29.784), (b - a, h, 0.026), m)
    scene.card("LabsArrow", (24.79, 1.64, 29.762), (2.5, 0.55), "wayfinding", (0, 180, 0))
    for i, x in enumerate((28.9, 31.0)):
        scene.card(f"ReplacementSheet{i}", (x, 0.81, 29.758), (1.28, 0.84), "patch", (0, 180, i * 2))
    scene.box("JunctionBox", (21.87, 1.07, 26.30), (0.53, 0.52, 0.15), "green_metal")
    scene.card("JunctionCover", (21.87, 1.07, 26.385), (0.47, 0.46), "service")
    for i, x in enumerate((21.79, 21.94)):
        scene.rod(f"JunctionDrop{i}", (x, 2.04, 26.32), (0.038, 1.4, 0.038), "pipe")
    scene.box("JunctionLightBack", (21.87, 2.5, 26.35), (0.40, 0.18, 0.23), "steel")
    scene.box("JunctionLens", (21.87, 2.48, 26.48), (0.30, 0.09, 0.05), "sodium_lamp", pwr=True)
    scene.light("JunctionPool", (21.84, 2.19, 26.81), warm, 0.70, 3.9)
    scene.card("CartRub", (26.81, 1.49, 29.749), (2.38, 0.29), "scrapes", (0, 180, 2))
    scene.card("ChippedBand", (32.10, 1.72, 29.757), (1.77, 0.48), "scrapes", (0, 180, -2))


def generator_hall(scene):
    scene.room("GeneratorHall")
    # Service raceway and a low wall bumper make the right perimeter read across the aisle.
    for i, y in enumerate((0.69, 0.92)):
        scene.bar(f"PlantBumper{i}", (27.55, y, 14.6), (27.55, y, 23.15), 0.08, "pipe")
    scene.box("PlantPullBox", (27.63, 1.67, 20.32), (0.24, 1.09, 0.86), "green_metal")
    scene.card("PullBoxCover", (27.49, 1.67, 20.32), (0.80, 1.03), "service", (0, -90, 0))

    scene.card("PlantStencil", (27.778, 2.96, 16.48), (3.8, 1.65), "generator", (0, -90, 0))
    for i, y in enumerate((3.97, 4.18)):
        scene.bar(f"BusConduit{i}", (11.0, y, 6.37), (21.3, y, 6.37), 0.088, "pipe")
    for i, x in enumerate((11.1, 13.3, 15.5, 17.7, 19.9, 21.2)):
        scene.box(f"ConduitCleat{i}", (x, 4.08, 6.38), (0.085, 0.42, 0.19), "green_metal")
    scene.box("PlantLampHousing", (27.65, 4.13, 16.48), (0.22, 0.13, 1.2), "steel")
    scene.box("PlantLampLens", (27.60, 4.055, 16.48), (0.16, 0.035, 1.04), "fluorescent", pwr=True)
    scene.light("StencilWash", (26.98, 3.75, 16.48), white, 2.4, 7.5)
    scene.box("RemovedCover", (14.42, 0.62, 14.46), (1.18, 1.15, 0.068), "steel", (-14, 0, -3))
    scene.card("CoverLouvers", (14.42, 0.628, 14.501), (1.13, 1.07), "service", (-14, 0, -3))
    scene.box("DripTray", (13.72, 0.073, 14.62), (0.67, 0.081, 0.40), "steel")
    scene.floor("TrayOil", (13.72, 0.119, 14.62), (0.66, 0.37), "spill")
    scene.box("FoldedShopRag", (14.85, 0.057, 14.86), (0.42, 0.09, 0.22), "navy", (0, 16, -6))
    scene.floor("ServiceGrate", (15.02, 0.014, 15.19), (2.52, 0.265), "drain")
    scene.bar("WorkStandA", (13.04, 0.04, 14.66), (13.22, 0.61, 14.76), 0.046, "ochre")
    scene.bar("WorkStandB", (13.44, 0.04, 14.72), (13.22, 0.61, 14.76), 0.046, "ochre")
    scene.box("PortableHousing", (13.23, 0.59, 14.77), (0.43, 0.33, 0.16), "ochre", (-10, -16, 0))
    scene.box("WorkReflector", (13.21, 0.59, 14.856), (0.37, 0.26, 0.035), "rubber", (-10, -16, 0))
    scene.box("WorkLens", (13.20, 0.59, 14.882), (0.318, 0.20, 0.025), "sodium_lamp", (-10, -16, 0), pwr=True)
    for i, y in enumerate((0.52, 0.59, 0.66)):
        scene.box(f"WorkGuard{i}", (13.20, y, 14.91), (0.34, 0.012, 0.012), "pipe", (-10, -16, 0))
    scene.light("ServicePool", (13.08, 0.79, 15.22), warm, 1.65, 6.5)


def labs(scene):
    scene.room("Labs")
    scene.floor("TransferBay", (40.32, 0.018, 21.14), (2.72, 1.46), "transfer", -90)
    scene.floor("DepartingCasters", (43.19, 0.017, 21.06), (1.25, 5.35), "caster", 83)
    scene.card("TransferCard", (40.54, 0.66, 20.01), (0.23, 0.31), "log", (0, 0, -6))
    scene.box("SampleTray", (40.52, 0.952, 19.40), (0.64, 0.044, 0.35), "steel")
    for i, (dx, dz, h) in enumerate(((-0.18, -0.05, 0.16), (0.03, -0.05, 0.22), (0.17, 0.025, 0.16))):
        x, z = 40.51 + dx, 19.4 + dz
        scene.rod(f"SealedSample{i}", (x, 0.976 + h / 2, z), (0.10, h, 0.10), "green_metal")
        scene.rod(f"SampleCollar{i}", (x, 0.976 + h * 0.58, z), (0.104, 0.053, 0.104), "ceramic")
        scene.rod(f"SampleCap{i}", (x, 0.985 + h, z), (0.084, 0.03, 0.084), "ochre")
    scene.strip("BenchLight", (40.72, 0.875, 19.94), 0.43)
    scene.light("BayPool", (40.62, 0.62, 20.45), white, 0.30, 3)


def coolant_tunnel(scene):
    scene.room("CoolantTunnel")
    scene.bar("InsulatedMain", (28.6, 2.48, 11.44), (35.5, 2.48, 11.44), 0.245, "frozen")
    for i, x in enumerate((28.77, 29.56, 30.38, 31.20, 31.84, 32.22, 32.95, 33.75, 34.55, 35.35)):
        scene.rod(f"LaggingBand{i}", (x, 2.48, 11.44), (0.274, 0.07, 0.274), "steel", (0, 0, 90))
    scene.box("ManifoldPlate", (32, 2.66, 11.28), (0.67, 0.38, 0.10), "green_metal")
    scene.rod("ValveFlange", (32, 2.48, 11.61), (0.44, 0.22, 0.44), "steel", (90, 0, 0))
    scene.rod("ValveStem", (32, 2.48, 11.85), (0.14, 0.34, 0.14), "brass", (90, 0, 0))
    scene.ring("ShutdownWheel", (32, 2.48, 12.03), (0.49, 0.24, 0.49), "green_metal", (90, 0, 0))
    for i, deg in enumerate((0, 60, 120)):
        scene.box(f"WheelSpoke{i}", (32, 2.48, 12.027), (0.036, 0.43, 0.04), "steel", (0, 0, deg))
    scene.bar("ReliefBranch", (32, 2.58, 11.67), (32, 2.77, 12.43), 0.095, "frozen")
    scene.card("RimeHalo", (32, 2.66, 11.344), (1.36, 0.42), "frost")
    scene.floor("MeltWater", (32.1, 0.017, 11.81), (1.40, 0.83), "spill", -17)
    scene.strip("PipeInspection", (30.53, 2.72, 11.41), 0.55)
    scene.light("RimeGlint", (31.6, 2.23, 12.14), cold, 0.60, 4.25, fog=0.035)


def containment_wing(scene):
    scene.room("ContainmentWing")
    scene.bar("CurtainTrack", (62.29, -0.42, 27.3), (64.55, -0.42, 27.3), 0.046, "pipe")
    for i, x in enumerate((62.41, 62.60, 62.79, 62.98, 63.14)):
        scene.ring(f"CurtainRing{i}", (x, -0.47, 27.3), (0.086, 0.05, 0.12), "steel", (90, 0, 0))
    scene.card("SnaggedPrivacyCurtain", (62.73, -1.08, 27.33), (0.84, 1.19), "curtain", (0, 0, -6))
    scene.floor("CasterSkid", (66.67, -2.981, 14.09), (1.70, 4.35), "caster", -17)
    for i, (x, z, h, yaw) in enumerate(
        (
            (67.15, 11.65, 0.22, 31),
            (68.58, 11.81, 0.15, -13),
            (68.95, 11.48, 0.27, 72),
            (67.41, 11.73, 0.10, 19),
            (68.27, 11.90, 0.12, 56),
        )
    ):
        scene.shape(f"VesselFragment{i}", "shard", (x, -2.99 + h / 2, z), (0.18, h, 0.045), "frozen", (0, yaw, 18))
    scene.box("CageLampBack", (62.36, -0.58, 27.28), (0.17, 0.30, 0.12), "rubber")
    scene.box("CageLampLens", (62.36, -0.58, 27.37), (0.106, 0.22, 0.055), "sodium_lamp", pwr=True)
    scene.light("CageInspection", (62.04, -0.87, 27.70), warm, 0.52, 4.6)


def containment_ramp(scene):
    scene.room("ContainmentRamp")
    top = (52.63, 0.90, 19.63)
    bottom = (59.47, -1.665, 19.63)
    scene.bar("GalvanizedRail", top, bottom, 0.075, "steel")
    for i, x in enumerate((52.85, 54.95, 57.05, 59.18)):
        y = 1.136 - (x - 52) * 0.375
        scene.bar(f"WallStay{i}", (x, y - 0.12, 19.79), (x, y, 19.63), 0.047, "pipe")
    scene.card("LowerLevelArrow", (56.91, 0.37, 19.775), (1.38, 0.79), "descent", (0, 180, 0))
    scene.box("EmergencyBacking", (56.86, -0.99, 19.71), (0.52, 0.25, 0.16), "green_metal")
    scene.box("EmergencyLens", (56.86, -0.99, 19.61), (0.41, 0.16, 0.06), "sodium_lamp")
    for i, x in enumerate((56.72, 56.85, 56.98)):
        scene.box(f"EmergencyCage{i}", (x, -0.99, 19.56), (0.018, 0.19, 0.02), "steel")
    scene.light("EmergencyPool", (56.70, -0.70, 19.25), warm, 2.4, 5.25, False)
    scene.card("ThresholdPlate", (53.38, 0.94, 16.223), (0.93, 0.65), "patch", (0, 0, -3))
    # A high crosswise work strip lights the landing and the opposite wall.
    scene.strip("LandingStrip", (55.25, 3.21, 18.12), 1.17)
    scene.light("RampFill", (55.07, 2.53, 17.85), white, 2.68, 7.7)
    for i, x in enumerate((53.75, 55.35, 57.15, 58.75)):
        y = -(x - 52) * 0.375
        scene.box(f"KerbMarker{i}", (x, y + 0.041, 19.50), (0.49, 0.023, 0.077), "ochre", (0, 0, -20.556))
    scene.node(
        "WheelRub",
        "MeshInstance3D",
        scene.current,
        transform="Transform3D(0, 2.87, 0.35112, 0, -1.076, 0.93633, 0.73, 0, 0, 56.33, -1.61075, 19.01)",
        cast_shadow=0,
        gi_mode=0,
        visibility_range_end=20,
        material_override=resource("scrapes"),
        mesh=resource("card"),
    )


def vent_route(scene):
    scene.room("VentRoute")
    scene.node(
        "ContactWear",
        "MeshInstance3D",
        scene.current,
        transform="Transform3D(-1.07, 0, 0, 0, 1.528, 0.92848, 0, 3.82, -0.37139, 62.47, -0.426, 39.40)",
        cast_shadow=0,
        gi_mode=0,
        visibility_range_end=20,
        material_override=resource("scrapes"),
        mesh=resource("card"),
    )
    scene.strip("ReturnStrip", (62.5, 3.19, 34.8), 0.82)
    scene.light("ReturnPool", (62.5, 2.23, 35.33), white, 2.36, 7.35)
    for i, z in enumerate((36.88, 41.88)):
        y = -3 + (z - 33) * 0.4
        for side, x in enumerate((61.23, 63.77)):
            scene.box(f"WallFlange{i}Side{side}", (x, (3.3 + y) * 0.5, z), (0.055, 3.3 - y, 0.095), "steel")
        scene.box(f"RoofFlange{i}", (62.5, 3.28, z), (2.55, 0.075, 0.095), "steel")

    scene.card("ServicePatch", (63.77, 1.43, 40.12), (1.52, 0.79), "patch", (0, -90, 0))
    for i, (y, z) in enumerate(((1.1, 39.48), (1.1, 40.77), (1.75, 39.48), (1.75, 40.77))):
        scene.rod(f"Bolt{i}", (63.75, y, z), (0.075, 0.035, 0.075), "steel", (0, 0, 90))
    scene.box("InspectionSlit", (61.235, 0.98, 38.31), (0.055, 0.105, 1.31), "steel")
    scene.box("ColdSeam", (61.27, 1.0, 38.31), (0.022, 0.039, 1.20), "fluorescent", pwr=True)
    scene.light("SeamPool", (61.51, 1.03, 38.41), cold, 1.65, 5.8)
    scene.box("ReturnSeam", (63.743, -0.35, 34.15), (0.022, 0.065, 0.72), "teal")


def cold_room(scene):
    scene.room("ColdRoom")
    # A sealed amber indicator over the records provides a second, quiet pool of light.
    scene.box("LogIndicatorBase", (55.21, 2.41, 50.73), (0.27, 0.20, 0.12), "steel")
    scene.box("LogIndicatorLens", (55.21, 2.39, 50.655), (0.14, 0.11, 0.046), "sodium_lamp", pwr=True)
    scene.light("LogPool", (55.21, 2.24, 50.38), warm, 0.48, 2.75)

    scene.box("ColdShelf", (56.57, 1.81, 48.98), (0.43, 0.066, 2.25), "steel")
    for i, z in enumerate((48.13, 49.80)):
        scene.bar(f"ShelfBracket{i}", (56.76, 1.48, z), (56.39, 1.78, z), 0.042, "pipe")
    for i, (z, h) in enumerate(((48.25, 0.27), (48.91, 0.35), (49.41, 0.25))):
        scene.rod(f"ReserveTin{i}", (56.52, 1.849 + h / 2, z), (0.32, h, 0.32), "green_metal")
        scene.rod(f"Seal{i}", (56.52, 1.85 + h, z), (0.326, 0.034, 0.326), "ceramic")
        scene.card(f"BatchTag{i}", (56.355, 1.85 + h / 2, z), (0.125, 0.12), "log", (0, -90, 0))
    scene.card("ShelfRime", (56.34, 1.81, 48.99), (2.18, 0.24), "frost", (0, -90, 0))
    scene.card("TemperatureLog", (55.2, 1.77, 50.777), (0.45, 0.61), "log", (0, 180, 0))
    scene.box("SleeveClip", (55.2, 2.13, 50.76), (0.27, 0.045, 0.038), "brass")
    scene.box("ShelfLightBack", (56.42, 1.72, 49.16), (0.15, 0.09, 0.66), "steel")
    scene.box("ShelfLens", (56.40, 1.67, 49.16), (0.103, 0.035, 0.62), "fluorescent", pwr=True)
    scene.light("ColdShelfPool", (56.01, 1.50, 49.04), cold, 0.76, 4.5)


def build():
    scene = DressingScene()
    loading_dock(scene)
    guard_post(scene)
    mess_hall(scene)
    main_corridor(scene)
    generator_hall(scene)
    labs(scene)
    coolant_tunnel(scene)
    containment_wing(scene)
    containment_ramp(scene)
    vent_route(scene)
    cold_room(scene)
    return scene.render()


if __name__ == "__main__":
    output = Path(__file__).resolve().parents[2] / "levels/halcyon_labs/room_dressing.tscn"
    output.write_text(build(), encoding="utf-8")
