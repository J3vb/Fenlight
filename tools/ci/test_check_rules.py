"""Temporary-repository examples for the structure checks."""

import subprocess
import tempfile
import unittest
from pathlib import Path

import check_rules as rules


class CheckRulesTests(unittest.TestCase):
    def write_files(self, root, files):
        for name, content in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    def check(self, name, files, expected=0):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_files(root, files)
            problems = getattr(rules, "check_" + name.replace("-", "_"))(root)
        self.assertEqual(len(problems), expected, problems)
        for problem in problems:
            self.assertRegex(problem, rf"^[^:]+:[1-9][0-9]*: {name}: .+")
        return problems

    def config_files(self):
        return {
            "gdlintrc": "".join(f"{key}: {value}\n" for key, value in rules.LINT_LIMITS.items()),
            "project.godot": "[debug]\n"
            + "".join(f"gdscript/warnings/{key}={value}\n" for key, value in rules.WARNING_LEVELS.items()),
        }

    def test_core_no_features(self):
        self.check("core-no-features", {"core/content.gd": 'load("res://content/weapon.tres")\n'})
        problems = self.check(
            "core-no-features",
            {
                "core/content.gd": '# Header\nload("res://systems/foo.gd")\nload("res://levels/map.tscn")\n',
            },
            2,
        )
        self.assertTrue(problems[0].startswith("core/content.gd:2:"))
        self.check("core-no-features", {"systems/game.gd": 'load("res://levels/map.tscn")\n'})

    def test_content_is_data(self):
        self.check(
            "content-is-data",
            {
                "content/guns/weapon.tres": "[gd_resource]\n",
                "content/guns/weapon.tres.uid": "uid://abc\n",
                "content/guns/weapon.tres.import": "[remap]\n",
            },
        )
        self.check("content-is-data", {"content/guns/weapon.gd": "extends Resource\n"}, 1)

    def test_file_names(self):
        for extension in ("gd", "tscn", "tres", "py", "glb"):
            with self.subTest(extension=extension):
                self.check("file-names", {f"assets/good_name2.{extension}": ""})
                self.check("file-names", {f"assets/BadName.{extension}": ""}, 1)
                self.check("file-names", {f"assets/bad-name.{extension}": ""}, 1)
        self.check("file-names", {"tools/__init__.py": "", "docs/README.md": ""})

    def test_class_name_matches_file(self):
        self.check("class-name-matches-file", {"systems/foo_bar.gd": "class_name FooBar\nextends Node\n"})
        self.check("class-name-matches-file", {"systems/wrong.gd": "class_name FooBar\nextends Node\n"}, 1)
        self.check("class-name-matches-file", {"core/events.gd": "extends Node\n"})

    def test_input_only_in_input(self):
        calls = (
            'Input.is_action_pressed("fire")',
            'Input.is_action_just_pressed("fire")',
            'Input.is_action_just_released("fire")',
            'Input.get_vector("l", "r", "u", "d")',
            'Input.get_axis("left", "right")',
            "Input.is_key_pressed(KEY_F3)",
            "Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT)",
        )
        for call in calls:
            with self.subTest(call=call):
                self.check("input-only-in-input", {"systems/player/player.gd": call + "\n"}, 1)
                for allowed in ("systems/input", "systems/ui", "systems/debug", "tools"):
                    self.check("input-only-in-input", {f"{allowed}/reader.gd": call + "\n"})
        self.check(
            "input-only-in-input",
            {
                "systems/player/player.gd": '# Input.is_action_pressed("fire")\nvar note = "Input.get_axis()"\n',
            },
        )

    def test_session_rng(self):
        calls = (
            "randf()",
            "randi()",
            "randf_range(0, 1)",
            "randi_range(0, 1)",
            "randfn()",
            "randomize()",
            "seed(1)",
            "items.pick_random()",
            "items.shuffle()",
        )
        for call in calls:
            with self.subTest(call=call):
                self.check("session-rng", {"systems/effects/spark.gd": call + " # cosmetic\n"})
                self.check("session-rng", {"systems/effects/spark.gd": call + "\n"}, 1)
                self.check("session-rng", {"systems/effects/spark.gd": call + " # cosmetic extra\n"}, 1)
        self.check(
            "session-rng",
            {
                "systems/game.gd": "rng.randf()\nsession.rng.randi_range(0, 1)\nrng.seed(1)\n",
                "tools/generate.py": "randomize()\n",
                "tests/random.gd": "randf()\n",
            },
        )
        self.check("session-rng", {"levels/light.gd": "# randf()\nvar label = 'randi()'\n"})

    def test_cosmetic_marker_must_be_an_actual_trailing_comment(self):
        for line in ('randf(); var label = "# cosmetic"', 'var label = "# cosmetic"; randf()'):
            with self.subTest(line=line):
                self.check("session-rng", {"systems/effects/spark.gd": line + "\n"}, 1)

    def test_log_not_print(self):
        for function in ("print", "prints", "printt", "print_debug", "printerr", "push_warning"):
            with self.subTest(function=function):
                call = f'{function}("message")\n'
                self.check("log-not-print", {"systems/game.gd": call}, 1)
                for allowed in ("core/log.gd", "core/build.gd", "systems/net/dedicated_server.gd"):
                    self.check("log-not-print", {allowed: call})
        self.check(
            "log-not-print",
            {
                "systems/game.gd": 'Log.warn("message")\n# print("example")\nvar label = "print()"\n',
                "tools/report.py": 'print("message")\n',
            },
        )

    def test_ui_router_only(self):
        lines = ('get_tree().change_scene_to_file("res://menu.tscn")', "Input.mouse_mode = Input.MOUSE_MODE_VISIBLE")
        for line in lines:
            with self.subTest(line=line):
                self.check("ui-router-only", {"systems/ui/menu.gd": line + "\n"}, 1)
                self.check("ui-router-only", {"levels/hub.gd": line + "\n"}, 1)
                self.check("ui-router-only", {"core/ui.gd": line + "\n"})
                self.check("ui-router-only", {"tests/unit/test_menu.gd": line + "\n", "tools/shot.gd": line + "\n"})
        self.check(
            "ui-router-only",
            {
                "systems/game.gd": "var free: bool = Input.mouse_mode == Input.MOUSE_MODE_VISIBLE\n"
                "# change_scene_to_file example\nvar label = 'change_scene_to_packed'\n",
            },
        )

    def test_no_absolute_paths(self):
        self.check(
            "no-absolute-paths",
            {
                "systems/game.gd": 'Events.player_spawned.emit(player)\nget_node("Camera")\nget_parent()\n',
            },
        )
        self.check("no-absolute-paths", {"systems/game.gd": 'get_node(^"Camera")\n'})
        for call in (
            'get_node("/root/Game")',
            'get_node(^"/root/Game")',
            'get_node(^"../../Thing")',
            'get_node_or_null("../../Thing")',
            '$"/root/Game"',
            'get_node("../..")',
            '$"../../Camera"',
            "$/root/Game",
            "$../../Camera",
            "var cam = $ ../../Camera",
            "get_parent().get_parent()",
        ):
            with self.subTest(call=call):
                self.check("no-absolute-paths", {"systems/game.gd": call + "\n"}, 1)
        self.check("no-absolute-paths", {"tools/example.gd": 'get_node("/root/Game")\n'})
        self.check("no-absolute-paths", {"systems/game.gd": "$Camera\n$Arm/Hand\n$../Sibling\n"})

    def test_path_examples_in_strings_and_comments_are_not_calls(self):
        self.check(
            "no-absolute-paths",
            {
                "systems/game.gd": (
                    '# get_node("/root/Game")\n'
                    '# $"../../Camera"\n'
                    "var note = 'get_node(\"/root/Game\")'\n"
                    "var note2 = '$\"../../Camera\"'\n"
                    'var note3 = "get_parent().get_parent()"\n'
                ),
            },
        )

    def test_autoload_list(self):
        content = "[autoload]\n" + "".join(f'{name}="*res://core/test.gd"\n' for name in rules.ALLOWED_AUTOLOADS)
        self.check("autoload-list", {"project.godot": content + "[other]\nUnknown=1\n"})
        self.check("autoload-list", {"project.godot": content + 'Unknown="*res://core/test.gd"\n'}, 1)

    def test_no_weakening(self):
        self.check("no-weakening", self.config_files())
        files = self.config_files()
        files["project.godot"] = files["project.godot"].replace("[debug]", "[rendering]")
        self.check("no-weakening", files, len(rules.WARNING_LEVELS))
        for key, value in rules.LINT_LIMITS.items():
            with self.subTest(lint=key):
                files = self.config_files()
                files["gdlintrc"] = files["gdlintrc"].replace(f"{key}: {value}", f"{key}: {value + 1}")
                self.check("no-weakening", files, 1)
        for key, value in rules.WARNING_LEVELS.items():
            with self.subTest(warning=key):
                files = self.config_files()
                setting = f"gdscript/warnings/{key}="
                files["project.godot"] = files["project.godot"].replace(f"{setting}{value}", f"{setting}{value - 1}")
                self.check("no-weakening", files, 1)
        files = self.config_files()
        files["gdlintrc"] = files["gdlintrc"].replace("max-line-length: 120\n", "")
        self.check("no-weakening", files, 1)
        files = self.config_files()
        key = next(iter(rules.WARNING_LEVELS))
        files["project.godot"] = "\n".join(line for line in files["project.godot"].splitlines() if key not in line)
        self.check("no-weakening", files, 1)

    def test_no_weakening_checks_every_warning_assignment(self):
        files = self.config_files()
        key = "untyped_declaration"
        files["project.godot"] = files["project.godot"].replace(
            f"gdscript/warnings/{key}=2",
            f"gdscript/warnings/{key}=1\ngdscript/warnings/{key}=2",
        )
        self.check("no-weakening", files, 1)

    def test_unfinished_markers(self):
        self.check("no-todo", {"systems/game.gd": "# Completed work; follow-up is issue 123.\n"})
        for marker in ("TO" + "DO", "FIX" + "ME", "HA" + "CK", "X" * 3):
            for extension in ("gd", "py"):
                with self.subTest(marker=marker, extension=extension):
                    self.check("no-todo", {f"tools/sample.{extension}": f"# {marker}: unfinished\n"}, 1)

    def test_warning_ignore_reason(self):
        self.check(
            "warning-ignore-reason",
            {
                "systems/game.gd": '@warning_ignore("unused_parameter") # Signal signature requires the argument.\n',
            },
        )
        for suffix in ("", " #", ' + "# not a comment"'):
            with self.subTest(suffix=suffix):
                self.check(
                    "warning-ignore-reason",
                    {
                        "systems/game.gd": '@warning_ignore("unused_parameter")' + suffix + "\n",
                    },
                    1,
                )
        self.check("warning-ignore-reason", {"systems/game.gd": '# @warning_ignore("example")\n'})

    def test_doc_comment(self):
        for directory in ("core", "systems/player"):
            with self.subTest(directory=directory):
                path = f"{directory}/sample.gd"
                self.check("doc-comment", {path: "\n" * 4 + "## Explains the script.\nextends Node\n"})
                self.check("doc-comment", {path: "\n" * 5 + "## Too late.\nextends Node\n"}, 1)
                self.check("doc-comment", {path: "# A regular comment.\nextends Node\n"}, 1)
        self.check("doc-comment", {"levels/sample.gd": "extends Node\n", "tools/sample.gd": "extends Node\n"})

    def test_no_triple_copy(self):
        block = "".join(f"step_{number}()\n" for number in range(8))
        files = {"systems/first.gd": block, "systems/second.gd": block}
        self.check("no-triple-copy", files)
        files["tools/third.py"] = "\n".join("  " + line for line in block.splitlines()) + "\n"
        problems = self.check("no-triple-copy", files, 3)
        self.assertEqual({problem.split(":", 1)[0] for problem in problems}, set(files))
        self.check("no-triple-copy", {"systems/first.gd": block * 3}, 3)
        short = "".join(f"step_{number}()\n" for number in range(7))
        self.check("no-triple-copy", {f"systems/{name}.gd": short for name in ("a", "b", "c")})
        self.check("no-triple-copy", {"systems/a.gd": block, "systems/b.gd": block, "tests/c.gd": block})

    def test_copy_detection_ignores_blank_and_comment_lines(self):
        for separator in ("\n", "# A separate task.\n"):
            with self.subTest(separator=separator):
                lines = [f"step_{number}()\n" for number in range(8)]
                block = "".join(lines[:4]) + separator + "".join(lines[4:])
                self.check("no-triple-copy", {f"systems/{name}.gd": block for name in ("a", "b", "c")}, 3)

    def test_copy_detection_includes_scenes_and_resources(self):
        block = "".join(f"property_{number} = {number}\n" for number in range(8))
        files = {"levels/a.tscn": block, "systems/b.tres": block}
        self.check("no-triple-copy", files)
        files["levels/c.tscn"] = block
        self.check("no-triple-copy", files, 3)

    def test_copy_detection_skips_godot_import_files(self):
        block = "".join(f"compress/setting_{number}=0\n" for number in range(8))
        names = ("levels/a/map.exr.import", "levels/b/map.exr.import", "levels/c/prop.glb.import")
        self.check("no-triple-copy", {name: block for name in names})
        self.check("no-triple-copy", {"levels/a.tres": block, "levels/b.tres": block, "levels/c.tres": block}, 3)

    def test_long_copy_reports_each_place_once(self):
        block = "".join(f"step_{number}()\n" for number in range(12))
        files = {f"systems/{name}.gd": "# Purpose.\n" + block for name in ("a", "b", "c")}
        problems = self.check("no-triple-copy", files, 3)
        self.assertTrue(all(":2: no-triple-copy:" in problem for problem in problems))

    def test_tested_scripts(self):
        for mention in ("foo_bar", "FooBar"):
            with self.subTest(mention=mention):
                self.check(
                    "tested-scripts",
                    {
                        "systems/foo_bar.gd": "class_name FooBar\n",
                        "tests/unit/test_example.gd": f"# Covers {mention}.\n",
                    },
                )
        self.check("tested-scripts", {"systems/foo_bar.gd": "class_name FooBar\n"}, 1)
        self.check("tested-scripts", {"levels/map.gd": "extends Node\n"})

    def test_tested_scripts_baseline_ratchet(self):
        baseline_path = "tools/ci/untested_baseline.txt"
        original = next(iter(rules.INITIAL_UNTESTED_BASELINE))
        self.check("tested-scripts", {original: "extends Node\n", baseline_path: original + "\n"})
        problems = self.check("tested-scripts", {baseline_path: original + "\n"}, 1)
        self.assertIn("remove", problems[0].lower())
        problems = self.check(
            "tested-scripts",
            {
                original: "extends Node\n",
                baseline_path: original + "\n",
                "tests/test_example.gd": Path(original).stem + "\n",
            },
            1,
        )
        self.assertIn("remove", problems[0].lower())
        self.check(
            "tested-scripts",
            {
                "systems/new.gd": "extends Node\n",
                baseline_path: "systems/new.gd\n",
            },
            1,
        )

    def test_no_content_id_literals(self):
        gun = {"content/weapons/test_gun.tres": "[resource]\n", "content/loot/affixes/head_damage.tres": "[resource]\n"}
        problems = self.check("no-content-id-literals", {**gun, "systems/a.gd": 'if id == &"test_gun":\n'}, 1)
        self.assertIn("test_gun", problems[0])
        self.check("no-content-id-literals", {**gun, "core/b.gd": "var x: String = 'test_gun'\n"}, 1)
        self.check("no-content-id-literals", {**gun, "systems/a.gd": "pass  # test_gun is special\n"})
        self.check("no-content-id-literals", {**gun, "systems/a.gd": '## "test_gun" in a doc comment\n'})
        self.check("no-content-id-literals", {**gun, "systems/a.gd": 'var stat: StringName = &"head_damage"\n'})
        self.check("no-content-id-literals", {**gun, "levels/map.gd": 'var id: StringName = &"test_gun"\n'})
        self.check("no-content-id-literals", {**gun, "systems/a.gd": 'var id: StringName = &"test_gun_2"\n'})

    def test_content_id_baseline_only_shrinks(self):
        baseline_path = "tools/ci/content_id_baseline.txt"
        files = {"content/serums/second_wind.tres": "[resource]\n", "content/weapons/test_gun.tres": "[resource]\n"}
        original = "systems/player/player.gd: second_wind"
        if original in rules.INITIAL_CONTENT_ID_BASELINE:
            literal = {"systems/player/player.gd": 'if has_serum(&"second_wind"):\n'}
            self.check("no-content-id-literals", {**files, **literal, baseline_path: original + "\n"})
            problems = self.check("no-content-id-literals", {**files, baseline_path: original + "\n"}, 1)
            self.assertIn("remove", problems[0].lower())
        problems = self.check(
            "no-content-id-literals",
            {
                **files,
                "systems/new.gd": 'var id: StringName = &"test_gun"\n',
                baseline_path: "systems/new.gd: test_gun\n",
            },
            1,
        )
        self.assertIn("remove", problems[0].lower())

    def test_melee_ids_are_content_ids(self):
        knife = {"content/melee/test_knife.tres": "[resource]\n"}
        self.check("no-content-id-literals", {**knife, "systems/a.gd": 'if id == &"test_knife":\n'}, 1)

    def test_rpc_names_mode_and_transfer(self):
        body = "func f() -> void:\n\tpass\n"
        self.check("rpc-rules", {"systems/a.gd": '@rpc("authority", "call_remote", "reliable")\n' + body})
        self.check("rpc-rules", {"core/a.gd": '@rpc("authority", "unreliable_ordered")\n' + body})
        self.check("rpc-rules", {"systems/a.gd": '@rpc("authority", "call_local")\n' + body}, 1)
        self.check("rpc-rules", {"systems/a.gd": '@rpc("reliable")\n' + body}, 1)
        self.check("rpc-rules", {"levels/a.gd": "@rpc\n" + body}, 1)

    def test_any_peer_rpc_starts_with_server_check(self):
        rpc = '@rpc("any_peer", "call_remote", "reliable")\n'
        good = "func f(x: int) -> void:\n\tif not multiplayer.is_server():\n\t\treturn\n"
        self.check("rpc-rules", {"systems/a.gd": rpc + good})
        multi_line = (
            "# gdlint:ignore = function-arguments-number\n"
            "func f(\n\ta: int,\n\tb: Vector3 = Vector3(0, 0, 0)\n) -> void:\n"
            "\n\t# Only the server takes requests.\n"
            "\tif multiplayer.is_server():\n\t\tpass\n"
        )
        self.check("rpc-rules", {"systems/a.gd": rpc + multi_line})
        bad = "func f() -> void:\n\tvar sender: int = multiplayer.get_remote_sender_id()\n"
        bad += "\tif not multiplayer.is_server():\n\t\treturn\n"
        problems = self.check("rpc-rules", {"systems/a.gd": rpc + bad}, 1)
        self.assertTrue(problems[0].startswith("systems/a.gd:3:"))
        authority = '@rpc("authority", "call_remote", "reliable")\n'
        self.check("rpc-rules", {"systems/a.gd": authority + "func f() -> void:\n\tpass\n"})
        self.check("rpc-rules", {"systems/a.gd": rpc + "func f() -> void:\n\t# multiplayer.is_server()\n\tpass\n"}, 1)

    def test_log_catalogue(self):
        doc = {"docs/LOGGING.md": "| `net.join_failed` | warn | Client could not join |\n"}
        warn = 'Log.warn(&"net", &"join_failed", {})\n'
        self.check("log-catalogue", {**doc, "systems/a.gd": warn})
        self.check("log-catalogue", {**doc, "core/a.gd": 'Log.warn(\n\t&"net",\n\t&"join_failed", {}\n)\n'})
        problems = self.check("log-catalogue", {**doc, "systems/a.gd": 'pass\nLog.warn(&"net", &"port_lost", {})\n'}, 1)
        self.assertTrue(problems[0].startswith("systems/a.gd:2:"))
        self.assertIn("net.port_lost", problems[0])
        self.check("log-catalogue", {**doc, "systems/a.gd": 'Log.warn(&"net", &"join_failed_twice", {})\n'}, 1)
        self.check("log-catalogue", {**doc, "systems/a.gd": 'Log.warn(&"net", event, {})\n'})
        self.check("log-catalogue", {**doc, "tools/a.gd": 'Log.warn(&"net", &"port_lost", {})\n'})

    def test_decisions_short(self):
        name = "docs/DECISIONS.md"
        short = "# Decisions\n\nIntro text\nover two lines.\n\n## List\n\n- **A:** one line.\n- **B:** another.\n"
        self.check("decisions-short", {name: short})
        self.check("decisions-short", {name: "- " + "x" * 298 + "\n"})
        problems = self.check("decisions-short", {name: "## List\n- " + "x" * 299 + "\n"}, 1)
        self.assertIn(":2:", problems[0])
        problems = self.check("decisions-short", {name: "- **A:** starts here\n  and wraps.\n- **B:** fine.\n"}, 1)
        self.assertIn(":2:", problems[0])
        self.check("decisions-short", {name: "- **A:** item\n  - nested item\n"}, 1)
        self.check("decisions-short", {})

    def test_instance_children_editable(self):
        rule = "instance-children-editable"
        name = "systems/weapons/viewmodels/rifle_viewmodel.tscn"
        head = (
            '[gd_scene format=3]\n\n[ext_resource type="PackedScene" path="res://assets/rifle.glb" id="1"]\n'
            '[ext_resource type="PackedScene" path="res://door.tscn" id="2"]\n\n'
            '[node name="Viewmodel" type="Node3D"]\n'
        )
        model = '[node name="Rifle" parent="." instance=ExtResource("1")]\n'
        inside = '[node name="Flash" type="Node3D" parent="Rifle/Receiver/Muzzle"]\n'
        problems = self.check(rule, {name: head + model + inside}, 1)
        self.assertIn(":8:", problems[0])
        self.assertIn('[editable path="Rifle"]', problems[0])
        self.check(rule, {name: head + model + inside + '\n[editable path="Rifle"]\n'})
        self.check(rule, {name: head + model + inside + inside.replace("Flash", "Light")}, 1)
        self.check(rule, {name: head + model + '[node name="A" type="Node3D" parent="Rifle"]\n'})
        self.check(rule, {name: head + model + '[node name="Receiver" parent="Rifle" index="0"]\nvisible = false\n'}, 1)
        nested = '[node name="Gun" type="Node3D" parent="."]\n'
        nested += '[node name="Rifle" parent="Gun" instance=ExtResource("1")]\n'
        self.check(rule, {name: head + nested + inside.replace('"Rifle/', '"Gun/Rifle/')}, 1)
        door = '[node name="Door" parent="." instance=ExtResource("2")]\n'
        self.check(rule, {name: head + door + '[node name="Lamp" type="OmniLight3D" parent="Door/Blocker"]\n'}, 1)
        own = '[node name="Door" type="Node3D" parent="."]\n[node name="Blocker" type="StaticBody3D" parent="Door"]\n'
        own += '[node name="Model" parent="Door/Blocker" instance=ExtResource("2")]\n'
        own += '[node name="Shape" type="CollisionShape3D" parent="Door/Blocker"]\n'
        self.check(rule, {name: head + own})

    def test_scope_uses_tracked_files_and_excludes_vendor_and_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_files(
                root,
                {
                    "core/allowed.gd": "extends Node\n",
                    "addons/BadName.gd": 'load("res://systems/feature.gd")\n',
                    ".godot/BadName.py": 'load("res://levels/map.tscn")\n',
                },
            )
            subprocess.run(["git", "init", "--quiet", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            self.write_files(root, {"core/Untracked.gd": 'load("res://systems/feature.gd")\n'})
            self.assertEqual(rules.check_core_no_features(root), [])
            self.assertEqual(rules.check_file_names(root), [])
            self.write_files(root, {"core/allowed.gd": 'load("res://systems/feature.gd")\n'})
            self.assertEqual(len(rules.check_core_no_features(root)), 1)
            (root / "core/allowed.gd").unlink()
            self.assertEqual(rules.check_core_no_features(root), [])


if __name__ == "__main__":
    unittest.main()
