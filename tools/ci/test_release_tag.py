"""Tests for tools/ci/release_tag.py; stdlib only."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import release_tag

TAGS = ["v0.1.0-test.1", "v0.1.0", "v0.1.1-test.1", "v0.1.1-test.2", "not-a-version"]


class PickTagTests(unittest.TestCase):
    def test_empty_version_takes_the_next_patch_for_stable(self):
        self.assertEqual(release_tag.pick_tag("stable", "", TAGS), "v0.1.1")

    def test_empty_version_takes_the_next_test_number(self):
        self.assertEqual(release_tag.pick_tag("test", "", TAGS), "v0.1.1-test.3")
        self.assertEqual(release_tag.pick_tag("test", "", ["v0.1.0"]), "v0.1.1-test.1")

    def test_first_release_ever(self):
        self.assertEqual(release_tag.pick_tag("stable", "", []), "v0.0.1")

    def test_a_typed_version_is_kept_with_or_without_v(self):
        self.assertEqual(release_tag.pick_tag("stable", "0.2.0", TAGS), "v0.2.0")
        self.assertEqual(release_tag.pick_tag("test", "v0.2.0-test.1", TAGS), "v0.2.0-test.1")

    def test_version_must_match_the_channel(self):
        with self.assertRaisesRegex(ValueError, "X.Y.Z-test.N"):
            release_tag.pick_tag("test", "0.2.0", TAGS)
        with self.assertRaisesRegex(ValueError, "X.Y.Z"):
            release_tag.pick_tag("stable", "0.2.0-test.1", TAGS)
        with self.assertRaisesRegex(ValueError, "look like"):
            release_tag.pick_tag("stable", "0.2", TAGS)

    def test_unknown_channel_is_refused(self):
        with self.assertRaisesRegex(ValueError, "channel"):
            release_tag.pick_tag("beta", "", TAGS)

    def test_existing_or_older_tags_are_refused(self):
        with self.assertRaisesRegex(ValueError, "already exists"):
            release_tag.pick_tag("test", "0.1.1-test.2", TAGS)
        with self.assertRaisesRegex(ValueError, "not newer"):
            release_tag.pick_tag("stable", "0.0.9", TAGS)
        with self.assertRaisesRegex(ValueError, "not newer"):
            release_tag.pick_tag("test", "0.1.0-test.5", TAGS)
        with self.assertRaisesRegex(ValueError, "older than a test build"):
            release_tag.pick_tag("test", "0.1.1-test.1", ["v0.1.0", "v0.1.1-test.3"])


class CiProblemTests(unittest.TestCase):
    def test_passes_when_test_succeeded_and_nothing_failed(self):
        runs = [{"name": "test", "conclusion": "success"}, {"name": "cut", "conclusion": None}]
        self.assertEqual(release_tag.ci_problem(runs), "")

    def test_names_failed_checks(self):
        runs = [{"name": "test", "conclusion": "success"}, {"name": "export / export", "conclusion": "failure"}]
        self.assertIn("export / export", release_tag.ci_problem(runs))

    def test_needs_a_passed_test_check(self):
        self.assertIn("has not passed", release_tag.ci_problem([{"name": "test", "conclusion": None}]))
        self.assertIn("has not passed", release_tag.ci_problem([]))


class MainTests(unittest.TestCase):
    def test_bad_input_returns_an_error_code(self):
        import io

        old = sys.stdin, sys.stdout
        sys.stdin, sys.stdout = io.StringIO("v0.1.0\n"), io.StringIO()
        try:
            self.assertEqual(release_tag.main(["pick", "--channel", "stable", "--version", "0.1.0"]), 1)
            self.assertIn("::error::", sys.stdout.getvalue())
        finally:
            sys.stdin, sys.stdout = old


if __name__ == "__main__":
    unittest.main()
