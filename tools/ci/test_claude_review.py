import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent))

import claude_review as cr


def finding(file="core/a.gd", line=10, severity="high", title="Null access on spawn", lens="correctness"):
    return cr.Finding(file, line, severity, title, "problem", "fix", lens)


class FakeReviewer:
    def __init__(self, replies, usage=None, model="claude-opus-5-5", stop="end_turn"):
        self.replies = list(replies)
        self.usage = usage or {"input_tokens": 1000, "output_tokens": 1000}
        self.model = model
        self.stop = stop
        self.system = "system"
        self.max_tokens = 32_000
        self.calls = 0

    def review(self, content):
        self.calls += 1
        reply = self.replies.pop(0) if self.replies else '{"findings": []}'
        if isinstance(reply, Exception):
            raise reply
        return reply, self.model, self.usage, self.stop


class BudgetTests(unittest.TestCase):
    def test_usage_cost_counts_all_token_kinds(self):
        usage = {
            "input_tokens": 1_000_000,
            "output_tokens": 1_000_000,
            "cache_creation_input_tokens": 1_000_000,
            "cache_read_input_tokens": 1_000_000,
        }
        self.assertAlmostEqual(cr.usage_cost("claude-opus-5-5", usage), 4 + 20 + 5 + 0.2)

    def test_default_model_is_priced(self):
        self.assertIn(cr.parse_args([]).model, cr.PRICES)
        self.assertLessEqual(cr.PRICES["claude-fable-5-2"][1], cr.UNKNOWN_MODEL_PRICE[1])

    def test_unknown_model_uses_highest_price(self):
        usage = {"output_tokens": 1_000_000}
        self.assertGreaterEqual(cr.usage_cost("some-new-model", usage), cr.usage_cost("claude-opus-5-5", usage))

    def test_worst_case_covers_one_token_per_byte_at_any_price(self):
        size = 30_000
        for model in (*cr.PRICES, "unknown"):
            real = cr.usage_cost(model, {"cache_creation_input_tokens": size, "output_tokens": 32_000})
            self.assertGreaterEqual(cr.worst_case_cost(size, 32_000), real)

    def test_non_ascii_text_is_reserved_by_bytes(self):
        reviewer = FakeReviewer([])
        size = 40_000
        budget = cr.Budget(limit=cr.worst_case_cost(int(size * 1.5), reviewer.max_tokens))
        cr.run_review(reviewer, {"core/a.gd": "\u00e9" * size}, [["core/a.gd"]], ["correctness"], budget)
        self.assertEqual(reviewer.calls, 0)

    def test_run_stops_before_overspending(self):
        files = {f"core/f{i}.gd": "var x := 1\n" * 50 for i in range(5)}
        chunks = [[path] for path in files]
        budget = cr.Budget(limit=3.0)
        reviewer = FakeReviewer([], usage={"output_tokens": 32_000})
        cr.run_review(reviewer, files, chunks, ["correctness"], budget)
        self.assertLessEqual(budget.spent, budget.limit)
        self.assertLess(reviewer.calls, len(chunks))
        self.assertIn("budget left too small", budget.log[-1])

    def test_parallel_run_never_overspends(self):
        files = {f"core/f{i}.gd": "var x := 1\n" * 50 for i in range(30)}
        budget = cr.Budget(limit=10.0)
        reviewer = FakeReviewer([], usage={"output_tokens": 32_000}, model="unknown-model")
        cr.run_review(reviewer, files, [[p] for p in files], ["correctness", "performance"], budget, workers=8)
        self.assertLessEqual(budget.spent, budget.limit)
        self.assertEqual(budget.reserved, 0)
        self.assertGreater(budget.calls, 0)

    def test_rejected_request_stops_the_run(self):
        error = RuntimeError("bad key")
        error.status_code = 401
        reviewer = FakeReviewer([error])
        files = {f"core/f{i}.gd": "x" for i in range(5)}
        budget = cr.Budget(limit=50.0)
        cr.run_review(reviewer, files, [[p] for p in files], ["correctness"], budget)
        self.assertEqual(reviewer.calls, 1)
        self.assertEqual(budget.spent, 0)
        self.assertTrue(budget.stopped)

    def test_failed_call_is_charged_its_reservation(self):
        budget = cr.Budget(limit=10.0)
        cr.run_review(
            FakeReviewer([RuntimeError("cut off")]), {"core/a.gd": "x"}, [["core/a.gd"]], ["correctness"], budget
        )
        self.assertGreater(budget.spent, 0)
        self.assertEqual(budget.reserved, 0)

    def test_pending_reservations_do_not_skip_chunks(self):
        files = {f"core/f{i}.gd": "x" for i in range(10)}
        one_call = cr.worst_case_cost(10_000, 32_000)
        budget = cr.Budget(limit=one_call * 1.5)
        reviewer = FakeReviewer([], usage={"output_tokens": 100})
        cr.run_review(reviewer, files, [[p] for p in files], ["correctness"], budget, workers=3)
        self.assertEqual(reviewer.calls, 10)
        self.assertLessEqual(budget.spent, budget.limit)

    def test_rounding_residue_cannot_block_forever(self):
        budget = cr.Budget(limit=4.0)
        self.assertTrue(budget.reserve(1.6375))
        self.assertTrue(budget.reserve(1.63755))
        budget.settle(1.6375, 1.0)
        budget.settle(1.63755, 1.0)
        self.assertEqual(budget.reserved, 0)
        self.assertFalse(budget.reserve(2.5))

    def test_zero_budget_makes_no_calls(self):
        reviewer = FakeReviewer([])
        cr.run_review(reviewer, {"core/a.gd": "x"}, [["core/a.gd"]], ["correctness"], cr.Budget(limit=0.0))
        self.assertEqual(reviewer.calls, 0)

    def test_api_error_does_not_lose_earlier_findings(self):
        good = json.dumps({"findings": [vars(finding())]})
        reviewer = FakeReviewer([good, RuntimeError("overloaded")])
        files = {"core/a.gd": "x\n" * 20}
        found = cr.run_review(reviewer, files, [["core/a.gd"]], ["correctness", "performance"], cr.Budget(10))
        self.assertEqual(len(found), 1)


class ParseTests(unittest.TestCase):
    def test_drops_files_not_in_chunk_and_bad_severity(self):
        reply = json.dumps(
            {
                "findings": [
                    vars(finding(file="core/a.gd")) | {"lens": None},
                    vars(finding(file="core/other.gd")),
                    vars(finding(severity="urgent")),
                ]
            }
        )
        found = cr.parse_findings(reply, {"core/a.gd"}, "multiplayer")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].lens, "multiplayer")

    def test_refusal_or_truncated_reply_gives_no_findings(self):
        reviewer = FakeReviewer(["not json"], stop="max_tokens")
        budget = cr.Budget(10)
        self.assertEqual(cr.run_review(reviewer, {"core/a.gd": "x"}, [["core/a.gd"]], ["correctness"], budget), [])
        self.assertEqual(budget.calls, 1)


class DedupeTests(unittest.TestCase):
    def test_fingerprint_ignores_case_and_punctuation(self):
        self.assertEqual(cr.fingerprint("a.gd", "Null access!"), cr.fingerprint("a.gd", "null  ACCESS"))
        self.assertNotEqual(cr.fingerprint("a.gd", "Null access"), cr.fingerprint("b.gd", "Null access"))

    def test_marker_round_trip(self):
        f = finding()
        self.assertEqual(cr.parse_markers(cr.issue_body(f, "abc", "o/r")), [(f.fingerprint, f.file, f.line)])

    def test_existing_issue_blocks_same_finding(self):
        deduper = cr.Deduper()
        old = finding()
        deduper.add(old.fingerprint, old.file, old.line)
        self.assertFalse(deduper.keep(finding(title="Null access on spawn")))

    def test_nearby_line_in_same_file_counts_as_duplicate(self):
        deduper = cr.Deduper()
        self.assertTrue(deduper.keep(finding(line=10, title="A")))
        self.assertFalse(deduper.keep(finding(line=12, title="Something else")))
        self.assertTrue(deduper.keep(finding(line=40, title="Something else")))
        self.assertTrue(deduper.keep(finding(file="core/b.gd", line=10, title="A")))

    def test_select_filters_severity_sorts_and_caps(self):
        items = [
            finding(line=1, severity="low", title="l"),
            finding(line=20, severity="medium", title="m"),
            finding(line=40, severity="critical", title="c"),
            finding(line=60, severity="high", title="h"),
        ]
        chosen = cr.select_findings(items, cr.Deduper(), "medium", 2)
        self.assertEqual([f.severity for f in chosen], ["critical", "high"])


class ChunkTests(unittest.TestCase):
    def test_reviewable_paths(self):
        self.assertTrue(cr.is_reviewable("systems/net/peer.gd"))
        self.assertTrue(cr.is_reviewable(".github/workflows/ci.yml"))
        self.assertFalse(cr.is_reviewable("addons/gut/gut.gd"))
        self.assertFalse(cr.is_reviewable("content/guns/rifle.tres"))

    def test_launcher_rust_and_js_are_reviewed_with_game_code(self):
        self.assertTrue(cr.is_reviewable("launcher/core/src/install.rs"))
        self.assertTrue(cr.is_reviewable("launcher/ui/app.js"))
        self.assertLess(cr.priority_of("launcher/src-tauri/src/main.rs"), cr.priority_of("tests/unit/t.gd"))

    def test_chunks_respect_size_and_priority(self):
        files = {"tests/unit/t.gd": "x\n", "core/a.gd": "y\n" * 10, "core/b.gd": "z\n" * 10}
        size = len(cr.file_block("core/a.gd", files["core/a.gd"])) + 5
        chunks = cr.make_chunks(files, size)
        self.assertEqual(chunks[0], ["core/a.gd"])
        self.assertEqual(chunks[-1], ["tests/unit/t.gd"])
        self.assertTrue(all(len(c) == 1 for c in chunks))

    def test_small_areas_share_a_chunk_without_splitting(self):
        files = {"systems/a/x.gd": "a\n", "systems/b/y.gd": "b\n", "systems/c/z.gd": "c\n" * 40}
        small = sum(len(cr.file_block(p, files[p])) for p in ("systems/a/x.gd", "systems/b/y.gd"))
        chunks = cr.make_chunks(files, small + 10)
        self.assertEqual(chunks, [["systems/a/x.gd", "systems/b/y.gd"], ["systems/c/z.gd"]])

    def test_line_numbers_match_source(self):
        block = cr.number_lines("first\nsecond")
        self.assertIn("    2 second", block)


class CliTests(unittest.TestCase):
    def test_unknown_lens_is_rejected(self):
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                cr.parse_args(["--lenses", "correctness,vibes"])

    def test_dry_run_creates_no_issues(self):
        created = cr.create_issues(None, [finding()], "sha", cr.Budget(0))
        self.assertTrue(created[0].startswith("(dry run)"))

    def test_github_failure_keeps_other_issues_and_logs(self):
        class FlakyGitHub:
            def __init__(self):
                self.calls = 0

            def create_issue(self, item, sha):
                self.calls += 1
                if self.calls == 1:
                    raise cr.urllib.error.URLError("timed out")
                return f"https://example/issues/{self.calls}"

        budget = cr.Budget(0)
        original_sleep = cr.time.sleep
        cr.time.sleep = lambda _seconds: None
        try:
            created = cr.create_issues(FlakyGitHub(), [finding(line=1), finding(line=50)], "sha", budget)
        finally:
            cr.time.sleep = original_sleep
        self.assertEqual(created, ["https://example/issues/2"])
        self.assertIn("could not open issue", budget.log[0])

    def test_findings_file_is_written(self):
        with tempfile.TemporaryDirectory() as folder:
            cr.write_findings([finding()], Path(folder))
            data = json.loads((Path(folder) / "findings.json").read_text())
        self.assertEqual(data[0]["file"], "core/a.gd")


class ReviewerTests(unittest.TestCase):
    def test_review_reads_text_usage_and_model(self):
        message = SimpleNamespace(
            content=[SimpleNamespace(type="thinking"), SimpleNamespace(type="text", text='{"findings": []}')],
            usage=SimpleNamespace(input_tokens=5, output_tokens=7, cache_creation_input_tokens=None),
            model="claude-opus-5-5",
            stop_reason="end_turn",
        )

        class Stream:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def get_final_message(self):
                return message

        sent = {}

        def stream(**kwargs):
            sent.update(kwargs)
            return Stream()

        client = SimpleNamespace(beta=SimpleNamespace(messages=SimpleNamespace(stream=stream)))
        reviewer = cr.ClaudeReviewer(client, "claude-opus-5-5", "high", 1000, "sys")
        text, model, usage, stop = reviewer.review([{"type": "text", "text": "code"}])
        self.assertEqual(text, '{"findings": []}')
        self.assertEqual(usage["cache_creation_input_tokens"], 0)
        self.assertEqual(usage["cache_read_input_tokens"], 0)
        self.assertEqual(sent["output_config"]["effort"], "high")
        self.assertEqual(stop, "end_turn")
        self.assertEqual(model, "claude-opus-5-5")


if __name__ == "__main__":
    unittest.main()
