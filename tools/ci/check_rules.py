"""Check repository structure with plain text rules; run from any directory."""

import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

GAME_DIRS = ("core/", "systems/", "levels/")
ALLOWED_AUTOLOADS = ["Events", "Content", "Net", "Build", "Log", "Settings", "UI", "Audio", "Pool", "Game"]
LINT_LIMITS = {"max-line-length": 120, "max-file-lines": 350, "function-arguments-number": 6}
WARNING_LEVELS = {
    "untyped_declaration": 2,
    "inferred_declaration": 2,
    "unused_variable": 2,
    "unused_local_constant": 2,
    "unused_private_class_variable": 2,
    "unused_parameter": 2,
    "shadowed_variable": 2,
    "shadowed_variable_base_class": 1,
    "shadowed_global_identifier": 2,
    "unreachable_code": 2,
    "unreachable_pattern": 2,
    "standalone_expression": 2,
    "standalone_ternary": 2,
    "incompatible_ternary": 2,
    "narrowing_conversion": 2,
    "return_value_discarded": 0,
    "integer_division": 1,
}
INITIAL_UNTESTED_BASELINE = frozenset(
    {
        "systems/debug/debug_overlay.gd",
        "systems/economy/economy_rules.gd",
        "systems/effects/impact.gd",
        "systems/enemies/zombie_voice.gd",
        "systems/input/input_frame.gd",
        "systems/ui/hit_marker.gd",
        "systems/ui/version_label.gd",
        "systems/weapons/weapon_holder.gd",
    }
)
BASELINE = "tools/ci/untested_baseline.txt"
ID_FOLDERS = (
    "content/weapons/",
    "content/enemies/",
    "content/serums/",
    "content/power_ups/",
    "content/gear_visuals/",
    "content/loot/gear/",
    "content/grips/",
    "content/melee/",
    "content/skills/",
    "content/waves/",
)
ID_BASELINE = "tools/ci/content_id_baseline.txt"
INITIAL_CONTENT_ID_BASELINE = frozenset(
    {
        "systems/gear/gear_visual.gd: charm_dog_tags",
        "systems/gear/gear_visual.gd: implant_reflex",
        "systems/gear/gear_visual.gd: vest_medium",
        "systems/gear/look_builder.gd: charm_coin",
        "systems/gear/look_builder.gd: charm_dog_tags",
        "systems/gear/look_builder.gd: charm_dosimeter",
        "systems/gear/look_builder.gd: charm_keycard",
        "systems/gear/look_builder.gd: charm_vial",
        "systems/gear/look_builder.gd: implant_lung",
        "systems/gear/look_builder.gd: implant_ocular",
        "systems/gear/look_builder.gd: implant_reflex",
        "systems/gear/look_builder.gd: implant_relay",
        "systems/gear/look_builder.gd: implant_spine",
        "systems/gear/look_builder.gd: vest_heavy",
        "systems/gear/look_builder.gd: vest_light",
        "systems/gear/look_builder.gd: vest_medium",
        "systems/net/player_state_sync.gd: pistol_service",
        "systems/player/player.gd: second_wind",
        "systems/power_ups/power_up.gd: ammo_pack",
        "systems/power_ups/power_up.gd: resupply",
        "systems/power_ups/power_up_drops.gd: scavenger",
        "systems/serums/serum_data.gd: scavenger",
        "systems/serums/serum_data.gd: second_wind",
    }
)
LITERALS = re.compile(r""""((?:\\.|[^"\\])*)"|'((?:\\.|[^'\\])*)'|#.*""")
RPC_MODES = ("authority", "any_peer")
RPC_TRANSFERS = ("reliable", "unreliable", "unreliable_ordered")
LOG_WARN = re.compile(r"""Log\.warn\(\s*&?["'](\w+)["']\s*,\s*&?["'](\w+)["']""")
SCENE_NODE = re.compile(
    r'^\[node name="([^"]+)"(?:[^\]]*?parent="([^"]*)")?(?:[^\]]*?instance=ExtResource\("([^"]+)"\))?'
)
SCENE_EDITABLE = re.compile(r'^\[editable path="([^"]+)"\]')
STRINGS = re.compile(r""""(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|#.*""")


def scanned_paths(root: Path) -> list[str]:
    if (root / ".git").exists():
        output = subprocess.run(
            ["git", "ls-files", "-z", "--cached"],
            cwd=root,
            check=True,
            capture_output=True,
        ).stdout.decode("utf-8")
        paths = output.split("\0")
    else:  # Standalone sample directories used by the unit tests.
        paths = [path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()]
    return sorted(
        {p for p in paths if p and not p.startswith(("addons/", ".godot/", ".git/")) and (root / p).is_file()}
    )


def text_files(root: Path, prefixes: tuple = (), suffixes: tuple = ()):
    for path in scanned_paths(root):
        if prefixes and not path.startswith(prefixes):
            continue
        if suffixes and not path.endswith(suffixes):
            continue
        try:
            yield path, (root / path).read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue


def problem(path: str, line: int, rule: str, message: str) -> str:
    return f"{path}:{line}: {rule}: {message}"


def code(line: str) -> str:
    return STRINGS.sub(lambda match: " " * len(match[0]), line)


def comment(line: str) -> str:
    return next((m[0] for m in STRINGS.finditer(line) if m[0].startswith("#")), "").rstrip()


def calls(root: Path, rule: str, pattern: str, allowed: tuple = (), cosmetic: bool = False) -> list[str]:
    errors = []
    for path, lines in text_files(root, GAME_DIRS):
        if path in allowed:
            continue
        for number, line in enumerate(lines, 1):
            if re.search(pattern, code(line)) and not (cosmetic and comment(line) == "# cosmetic"):
                owner = "GameSession.rng or mark verified visuals # cosmetic" if cosmetic else "Log"
                errors.append(problem(path, number, rule, f"use {owner}; see docs/CODE_RULES.md"))
    return errors


def check_core_no_features(root: Path) -> list[str]:
    return [
        problem(path, number, "core-no-features", "move feature dependencies out of core/")
        for path, lines in text_files(root, ("core/",))
        for number, line in enumerate(lines, 1)
        if re.search(r"res://(?:systems|levels)/", line)
    ]


def check_content_is_data(root: Path) -> list[str]:
    return [
        problem(path, 1, "content-is-data", "content/ allows only .tres and their .uid/.import files")
        for path in scanned_paths(root)
        if path.startswith("content/") and not re.fullmatch(r".+\.tres(?:\.(?:uid|import))?", Path(path).name)
    ]


def check_file_names(root: Path) -> list[str]:
    return [
        problem(path, 1, "file-names", "rename the file to snake_case and update references")
        for path in scanned_paths(root)
        if Path(path).suffix.lower() in (".gd", ".tscn", ".tres", ".py", ".glb")
        and not re.fullmatch(r"[a-z0-9_]+\.[a-z]+", Path(path).name)
    ]


def check_class_name_matches_file(root: Path) -> list[str]:
    errors = []
    for path, lines in text_files(root, suffixes=(".gd",)):
        for number, line in enumerate(lines, 1):
            match = re.match(r"\s*class_name\s+(\w+)", line)
            if match:
                name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", match[1])
                name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name).lower() + ".gd"
                if Path(path).name != name:
                    errors.append(problem(path, number, "class-name-matches-file", f"rename file to {name}"))
    return errors


def check_input_only_in_input(root: Path) -> list[str]:
    errors = []
    pattern = r"\bInput\s*\.\s*(?:is_action_\w+|get_vector|get_axis|is_key_pressed|is_mouse_button_pressed)\s*\("
    allowed = ("systems/input/", "systems/ui/", "systems/debug/", "tools/")
    for path, lines in text_files(root, suffixes=(".gd",)):
        if not path.startswith(allowed):
            errors.extend(
                problem(path, i, "input-only-in-input", "read InputFrames in gameplay")
                for i, line in enumerate(lines, 1)
                if re.search(pattern, code(line))
            )
    return errors


def check_session_rng(root: Path) -> list[str]:
    pattern = (
        r"(?<![\w.])(?:randf|randi|randf_range|randi_range|randfn|randomize|seed)\s*\("
        r"|\.\s*(?:pick_random|shuffle)\s*\("
    )
    return calls(root, "session-rng", pattern, cosmetic=True)


def check_log_not_print(root: Path) -> list[str]:
    return calls(
        root,
        "log-not-print",
        r"(?<![\w.])(?:print|prints|printt|print_debug|printerr|push_warning)\s*\(",
        ("core/log.gd", "core/build.gd", "systems/net/dedicated_server.gd"),
    )


def check_ui_router_only(root: Path) -> list[str]:
    pattern = r"\bchange_scene_to_\w*|\bInput\s*\.\s*mouse_mode\s*=(?!=)"
    return [
        problem(path, number, "ui-router-only", "use UI.replace, UI.push or UI.hold_mouse; see docs/CODE_RULES.md")
        for path, lines in text_files(root, GAME_DIRS, (".gd",))
        if path != "core/ui.gd"
        for number, line in enumerate(lines, 1)
        if re.search(pattern, code(line))
    ]


def check_no_absolute_paths(root: Path) -> list[str]:
    errors = []
    for path, lines in text_files(root, GAME_DIRS, (".gd",)):
        for number, line in enumerate(lines, 1):
            references = re.finditer(r"\bget_node(?:_or_null)?\s*\(|\$", code(line))
            bad_path = any(re.match(r"""\s*\^?["'](?:/root/|[^"']*\.\./\.\.)""", line[m.end() :]) for m in references)
            bad_path = bad_path or re.search(r"\$\s*(?:/root/|\.\./\.\.)", code(line)) is not None
            parents = re.search(r"\bget_parent\s*\(\s*\)\s*\.\s*get_parent\s*\(", code(line))
            if bad_path or parents:
                errors.append(
                    problem(path, number, "no-absolute-paths", "use autoloads, signals or exported NodePaths")
                )
    return errors


def check_autoload_list(root: Path) -> list[str]:
    errors, section = [], ""
    project = root / "project.godot"
    if not project.is_file():
        return [problem("project.godot", 1, "autoload-list", "restore project.godot")]
    for number, line in enumerate(project.read_text().splitlines(), 1):
        if header := re.match(r"\s*(\[[^]]+\])", line):
            section = header[1]
        match = re.match(r"\s*([^;#=\s][^=]*)=", line)
        if section == "[autoload]" and match and match[1].strip(' \t"') not in ALLOWED_AUTOLOADS:
            errors.append(
                problem(
                    "project.godot",
                    number,
                    "autoload-list",
                    f"review new autoload {match[1].strip()} and allow explicitly",
                )
            )
    return errors


def configuration_lines(root: Path, path: str) -> list[str]:
    file = root / path
    text = file.read_text() if file.is_file() else ""
    if path == "project.godot":
        debug = re.search(r"(?ms)^\[debug\][^\n]*\n(.*?)(?=^\[|\Z)", text)
        return [""] * text[: debug.start(1)].count("\n") + debug[1].splitlines() if debug else []
    return text.splitlines()


def configuration_limits(root: Path, path: str, limits: dict) -> list[str]:
    errors = []
    lines = configuration_lines(root, path)
    prefix = "" if path == "gdlintrc" else "gdscript/warnings/"
    for name, limit in limits.items():
        matches = [
            (i, m[1])
            for i, line in enumerate(lines, 1)
            if (m := re.match(r"\s*" + prefix + name + r"\s*[:=]\s*(-?\d+)\s*(?:[#;].*)?$", line))
        ]
        for number, raw in matches or [(1, None)]:
            value = int(raw) if raw is not None else None
            if value is None or (value > limit if path == "gdlintrc" else value < limit):
                direction = "at most" if path == "gdlintrc" else "at least"
                errors.append(problem(path, number, "no-weakening", f"set {name} to {direction} {limit}"))
    return errors


def check_no_weakening(root: Path) -> list[str]:
    return configuration_limits(root, "gdlintrc", LINT_LIMITS) + configuration_limits(
        root, "project.godot", WARNING_LEVELS
    )


def check_no_todo(root: Path) -> list[str]:
    words = ("TO" + "DO", "FIX" + "ME", "HA" + "CK", "X" + "XX")
    pattern = r"\b(?:" + "|".join(words) + r")\b"
    return [
        problem(path, number, "no-todo", "finish the work or open an issue and remove the marker")
        for path, lines in text_files(root, suffixes=(".gd", ".py"))
        for number, line in enumerate(lines, 1)
        if re.search(pattern, line)
    ]


def check_warning_ignore_reason(root: Path) -> list[str]:
    errors = []
    for path, lines in text_files(root, suffixes=(".gd",)):
        for number, line in enumerate(lines, 1):
            if re.search(r"@warning_ignore(?:_start|_restore)?\s*\(", code(line)):
                if not re.search(r"[a-zA-Z]", comment(line)):
                    errors.append(
                        problem(path, number, "warning-ignore-reason", "add a same-line comment explaining why")
                    )
    return errors


def check_doc_comment(root: Path) -> list[str]:
    return [
        problem(path, 1, "doc-comment", "add a ## purpose comment within the first five lines")
        for path, lines in text_files(root, ("core/", "systems/"), (".gd",))
        if not any(line.lstrip().startswith("##") for line in lines[:5])
    ]


def check_no_triple_copy(root: Path) -> list[str]:
    blocks = defaultdict(list)
    for path, lines in text_files(root, (*GAME_DIRS, "tools/")):
        if path.endswith(".import"):  # Godot writes these sidecars; there is nothing to share.
            continue
        run = []
        for number, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", ";", "//")):
                continue
            run.append((number, stripped))
            if len(run) >= 8:
                blocks[tuple(text for _, text in run[-8:])].append((path, run[-8][0], number))
    places = sorted({place for copies in blocks.values() if len(copies) >= 3 for place in copies})
    errors, last_path, last_end = [], "", 0
    for path, start, end in places:
        if path != last_path or start > last_end:
            errors.append(
                problem(
                    path, start, "no-triple-copy", "8+ consecutive lines occur in 3+ places; extract the shared block"
                )
            )
        last_path, last_end = path, end
    return errors


def check_tested_scripts(root: Path) -> list[str]:
    scripts = dict(text_files(root, ("core/", "systems/"), (".gd",)))
    tests = "\n".join("\n".join(lines) for _, lines in text_files(root, ("tests/",)))
    covered = set()
    for path, lines in scripts.items():
        names = [Path(path).stem, *re.findall(r"^\s*class_name\s+(\w+)", "\n".join(lines), re.MULTILINE)]
        if any(re.search(r"\b" + re.escape(name) + r"\b", tests) for name in names):
            covered.add(path)
    baseline_path = root / BASELINE
    baseline = baseline_path.read_text().splitlines() if baseline_path.is_file() else []
    errors = []
    for number, path in enumerate(baseline, 1):
        if not path.strip() or path.lstrip().startswith("#"):
            continue
        if path not in INITIAL_UNTESTED_BASELINE or path not in scripts or path in covered:
            errors.append(problem(BASELINE, number, "tested-scripts", f"{path}: remove it from the baseline"))
    errors.extend(
        problem(path, 1, "tested-scripts", "add a test mentioning the file stem or class_name")
        for path in sorted(scripts.keys() - covered - set(baseline))
    )
    return errors


def rpc_body_start(lines: list[str], start: int) -> tuple[int, str]:
    """Return the line number and code of the first body line of the function after an annotation."""
    depth, in_signature = 0, False
    for number in range(start, len(lines) + 1):
        text = code(lines[number - 1])
        if not in_signature:
            match = re.search(r"\bfunc\b", text)
            if not match:
                continue
            in_signature, text = True, text[match.end() :]
        for index, char in enumerate(text):
            depth += (char == "(") - (char == ")")
            if char == ":" and depth == 0:
                rest = text[index + 1 :].strip()
                if rest:
                    return number, rest
                return next(
                    (
                        (n, code(lines[n - 1]).strip())
                        for n in range(number + 1, len(lines) + 1)
                        if code(lines[n - 1]).strip()
                    ),
                    (number, ""),
                )
    return start, ""


def check_rpc_rules(root: Path) -> list[str]:
    """Every @rpc names its mode and transfer mode; an any_peer RPC's first line is the server check."""
    errors = []
    for path, lines in text_files(root, GAME_DIRS, (".gd",)):
        for number, line in enumerate(lines, 1):
            match = re.match(r"\s*@rpc\b(\([^)]*\))?", line)
            if not match:
                continue
            words = re.findall(r"""["'](\w+)["']""", match[1] or "")
            if not any(word in RPC_MODES for word in words) or not any(word in RPC_TRANSFERS for word in words):
                errors.append(problem(path, number, "rpc-rules", "name the mode and the transfer mode in @rpc(...)"))
            if "any_peer" in words:
                body, text = rpc_body_start(lines, number + 1)
                if "multiplayer.is_server()" not in text:
                    errors.append(
                        problem(path, body, "rpc-rules", "start an any_peer RPC with a multiplayer.is_server() check")
                    )
    return errors


def check_log_catalogue(root: Path) -> list[str]:
    """Every Log.warn event named by a literal in core/ and systems/ has a row in docs/LOGGING.md."""
    doc = root / "docs/LOGGING.md"
    catalogue = doc.read_text(encoding="utf-8") if doc.is_file() else ""
    errors = []
    for path, lines in text_files(root, ("core/", "systems/"), (".gd",)):
        text = "\n".join(lines)
        for match in LOG_WARN.finditer(text):
            if not re.search(r"\b" + match[2] + r"\b", catalogue):
                number = text.count("\n", 0, match.start()) + 1
                errors.append(problem(path, number, "log-catalogue", f"add {match[1]}.{match[2]} to docs/LOGGING.md"))
    return errors


def content_id_literals(root: Path) -> set[tuple[str, str, int]]:
    ids = {Path(path).stem for path in scanned_paths(root) if path.startswith(ID_FOLDERS) and path.endswith(".tres")}
    found = set()
    for path, lines in text_files(root, ("core/", "systems/"), (".gd",)):
        for number, line in enumerate(lines, 1):
            for match in LITERALS.finditer(line):
                text = match[1] if match[1] is not None else match[2]
                if text in ids:
                    found.add((path, text, number))
    return found


def check_no_content_id_literals(root: Path) -> list[str]:
    """Code must not name content by id; the behaviour belongs in a field on the data type.

    Checked: weapons, enemies, serums, power-ups, gear visuals, loot gear bases, grips, skills, waves.
    Left out on purpose: affixes (their ids are also stat keys code must name), rarities and rarity
    looks (a fixed ordered rule), singletons loaded by one name (economy, progression, stat caps)
    and UI screens (screen flow is code). Known leftovers sit in the baseline, which may only shrink.
    """
    found = content_id_literals(root)
    pairs = {(path, text) for path, text, _ in found}
    baseline_path = root / ID_BASELINE
    baseline = baseline_path.read_text().splitlines() if baseline_path.is_file() else []
    allowed = set()
    errors = []
    for number, line in enumerate(baseline, 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        path, _, text = line.partition(": ")
        if line not in INITIAL_CONTENT_ID_BASELINE or (path, text) not in pairs:
            errors.append(
                problem(ID_BASELINE, number, "no-content-id-literals", f"{line}: remove it from the baseline")
            )
        allowed.add((path, text))
    errors.extend(
        problem(path, number, "no-content-id-literals", f"'{text}' is a content id; add a data field instead")
        for path, text, number in sorted(found)
        if (path, text) not in allowed
    )
    return errors


DECISIONS = "docs/DECISIONS.md"
DECISIONS_MAX = 300


def check_decisions_short(root: Path) -> list[str]:
    path = root / DECISIONS
    if not path.is_file():
        return []
    errors = []
    in_entry = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("- "):
            in_entry = True
            if len(line) > DECISIONS_MAX:
                errors.append(problem(DECISIONS, number, "decisions-short", f"entry over {DECISIONS_MAX} characters"))
        elif not line.strip() or line.startswith("#"):
            in_entry = False
        elif in_entry:
            errors.append(problem(DECISIONS, number, "decisions-short", "entry wraps; keep it on one line"))
    return errors


def scene_nodes(lines: list[str]) -> tuple[list[tuple[int, str, str, bool]], set, set]:
    """Nodes as (line, path, parent, declared), the instanced node paths and the editable paths."""
    nodes, instances, editable = [], set(), set()
    for number, line in enumerate(lines, 1):
        if match := SCENE_EDITABLE.match(line):
            editable.add(match[1])
        if not (match := SCENE_NODE.match(line)) or match[2] is None:
            continue
        path = match[1] if match[2] == "." else f"{match[2]}/{match[1]}"
        if match[3]:
            instances.add(path)
        nodes.append((number, path, match[2], bool(match[3]) or " type=" in line))
    return nodes, instances, editable


def check_instance_children_editable(root: Path) -> list[str]:
    errors = []
    for path, lines in text_files(root, suffixes=(".tscn",)):
        nodes, instances, editable = scene_nodes(lines)
        declared = {node_path for _, node_path, _, own in nodes if own}
        flagged = set()
        for number, _, parent, own in nodes:
            owner = parent
            while owner not in declared | {"."} and "/" in owner:
                owner = owner.rsplit("/", 1)[0]
            inside = owner in instances and (owner != parent or not own)
            if inside and owner not in editable | flagged:
                flagged.add(owner)
                message = f'node inside instance "{owner}" needs [editable path="{owner}"] or export drops it'
                errors.append(problem(path, number, "instance-children-editable", message))
    return errors


RULES = [
    check_core_no_features,
    check_content_is_data,
    check_file_names,
    check_class_name_matches_file,
    check_input_only_in_input,
    check_session_rng,
    check_log_not_print,
    check_no_absolute_paths,
    check_ui_router_only,
    check_autoload_list,
    check_no_weakening,
    check_no_todo,
    check_warning_ignore_reason,
    check_doc_comment,
    check_no_triple_copy,
    check_tested_scripts,
    check_no_content_id_literals,
    check_rpc_rules,
    check_log_catalogue,
    check_decisions_short,
    check_instance_children_editable,
]


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    errors = [error for rule in RULES for error in rule(root)]
    for error in errors:
        print(error)
    print(f"Structure rules: {len(errors)} finding(s).")
    return int(bool(errors))


if __name__ == "__main__":
    sys.exit(main())
