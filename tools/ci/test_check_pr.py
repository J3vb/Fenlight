"""Regression tests for the repository quality gate; stdlib only."""

import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import call, patch

from tools.ci import check_pr


class LongFunctionTests(unittest.TestCase):
    def check_source(self, source: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.gd"
            path.write_text(source, encoding="utf-8")
            return check_pr.long_functions(str(path))

    def test_fifty_body_lines_pass(self):
        self.assertEqual(self.check_source("func at_limit():\n" + "\tpass\n" * 50), [])

    def test_long_function_reports_name_line_and_size(self):
        problems = self.check_source("# Script\nstatic func too_long():\n" + "\tpass\n" * 51)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].endswith(":2: function 'too_long' has 51 lines (max 50)"))

    def test_wrapped_signature_body_is_counted(self):
        source = "func wrapped(\n\ta: int,\n\tb: int\n) -> void:\n" + "\tpass\n" * 51 + "func next():\n\tpass\n"
        problems = self.check_source(source)
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].endswith(":1: function 'wrapped' has 51 lines (max 50)"))

    def test_wrapped_signature_at_limit_passes(self):
        source = "func wrapped(\n\ta: int,\n\tb: Array[int] = []\n) -> void:\n" + "\tpass\n" * 50
        self.assertEqual(self.check_source(source), [])

    def test_blank_lines_and_next_function_do_not_count(self):
        source = "func first():\n" + "\tpass\n\n" * 50 + "func second():\n\tpass\n"
        self.assertEqual(self.check_source(source), [])

    def test_nested_function_indentation_and_comments_count(self):
        source = "class Nested:\n\tfunc too_long():\n" + "\t\t# Body\n" * 51 + "\tvar value: int\n"
        self.assertEqual(len(self.check_source(source)), 1)


class ComplexityTests(unittest.TestCase):
    def test_only_functions_over_ten_are_reported(self):
        output = """systems/debug/debug_console.gd
    F 12:0 small - A (1)
    F 90:0 at_limit - B (10)
    F 122:0 _change_game - C (15)
tools/soak/soak.gd
    F 55:4 check_log - C (11)
    F 90:0 huge - F (50)
    C 1:0 SomeClass - C (12)
"""
        self.assertEqual(
            check_pr.complex_functions(output),
            [
                "systems/debug/debug_console.gd:122: function '_change_game' has complexity 15 (max 10)",
                "tools/soak/soak.gd:55: function 'check_log' has complexity 11 (max 10)",
                "tools/soak/soak.gd:90: function 'huge' has complexity 50 (max 10)",
            ],
        )

    def test_empty_output_passes(self):
        self.assertEqual(check_pr.complex_functions(""), [])

    @patch("tools.ci.check_pr.subprocess.run")
    def test_gdradon_processing_errors_fail_even_with_zero_exit(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, stdout="", stderr="Cannot process file 'broken.gd'\n")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertFalse(check_pr.check_complexity(["broken.gd"]))


class TestsRequiredTests(unittest.TestCase):
    def test_core_change_without_tests_fails(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(check_pr.tests_required(["core/net.gd"], False))

    def test_no_tests_needed_label_passes(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(check_pr.tests_required(["core/net.gd"], True))

    def test_logic_change_with_tests_passes(self):
        self.assertTrue(
            check_pr.tests_required(["systems/debug/debug_console.gd", "tests/unit/test_debug_console.gd"], False)
        )

    def test_unrelated_files_do_not_require_tests(self):
        self.assertTrue(check_pr.tests_required(["addons/example.gd", "tools/screenshot.gd", "core/data.tres"], False))


class ReviewRecordedTests(unittest.TestCase):
    TEMPLATE = (
        "### Review\n<!-- Run the pre-merge-review skill. -->\n"
        "Review: <!-- fresh subagent at <sha>; checklists: game   OR   skipped, docs only -->\n"
    )

    def check(self, files: list[str], body: str | None) -> bool:
        with contextlib.redirect_stdout(io.StringIO()):
            return check_pr.review_recorded(files, body)

    def test_no_body_passes_for_drafts_and_local_runs(self):
        self.assertTrue(self.check(["systems/x/y.gd"], None))

    def test_docs_and_assets_only_need_no_review_line(self):
        self.assertTrue(self.check(["docs/plans/x.md", "assets/a.glb", "launcher/news/n.json", "README.md"], ""))

    def test_untouched_template_fails_for_code(self):
        self.assertFalse(self.check(["launcher/core/src/install.rs"], self.TEMPLATE))

    def test_skipped_fails_for_code(self):
        self.assertFalse(self.check(["tools/ci/check_pr.py"], "Review: skipped, docs only\n"))

    def test_filled_review_line_passes(self):
        body = self.TEMPLATE.replace("Review: <!--", "Review: fresh subagent at abc123; checklists: game <!--")
        self.assertTrue(self.check(["systems/x/y.gd", "docs/a.md"], body))

    def test_heading_alone_does_not_count(self):
        self.assertFalse(self.check(["core/net.gd"], "### Review\nLooks fine.\n"))


class RepositoryScopeTests(unittest.TestCase):
    @patch("tools.ci.check_pr.subprocess.run")
    def test_tracked_files_exclude_addons_and_other_extensions(self, run):
        run.return_value = subprocess.CompletedProcess(
            [], 0, stdout="addons/vendor.gd\0core/net.gd\0tools/has space.gd\0README.md\0tools/ci/check_pr.py\0"
        )
        self.assertEqual(check_pr.tracked_files(".gd"), ["core/net.gd", "tools/has space.gd"])
        self.assertEqual(check_pr.tracked_files(".py"), ["tools/ci/check_pr.py"])
        self.assertEqual(run.call_args.args[0], ["git", "ls-files", "-z"])

    @patch("tools.ci.check_pr.subprocess.run")
    def test_tracked_files_exclude_vendored_agent_skills(self, run):
        run.return_value = subprocess.CompletedProcess(
            [], 0, stdout=".agents/skills/a/x.gd\0.claude/skills/a/x.py\0tools/ci/check_skills_mirror.py\0"
        )
        self.assertEqual(check_pr.tracked_files(".gd"), [])
        self.assertEqual(check_pr.tracked_files(".py"), ["tools/ci/check_skills_mirror.py"])

    def test_main_checks_tracked_files_but_applies_tests_rule_to_changed_files(self):
        with (
            patch.object(check_pr.sys, "argv", ["check_pr.py", "origin/main"]),
            patch.object(check_pr, "changed_files", return_value=["README.md"]),
            patch.object(check_pr, "tracked_files", side_effect=[["core/net.gd"], ["tools/ci/check_pr.py"]]),
            patch.object(check_pr, "check_gdscript", return_value=True) as gdscript,
            patch.object(check_pr, "check_python", return_value=True) as python,
            patch.object(check_pr, "run", return_value=True) as structure,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(check_pr.main(), 0)
        gdscript.assert_called_once_with(["core/net.gd"])
        python.assert_called_once_with(["tools/ci/check_pr.py"])
        here = Path(check_pr.__file__)
        self.assertEqual(
            structure.call_args_list,
            [
                call([check_pr.sys.executable, str(here.with_name("check_rules.py"))]),
                call([check_pr.sys.executable, str(here.with_name("check_plans.py"))]),
                call([check_pr.sys.executable, str(here.with_name("check_saved_ids.py")), "origin/main"]),
            ],
        )

    def test_structure_failure_fails_local_quality_check(self):
        with (
            patch.object(check_pr.sys, "argv", ["check_pr.py", "origin/main"]),
            patch.object(check_pr, "changed_files", return_value=[]),
            patch.object(check_pr, "tracked_files", return_value=[]),
            patch.object(check_pr, "run", return_value=False),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(check_pr.main(), 1)


if __name__ == "__main__":
    unittest.main()
