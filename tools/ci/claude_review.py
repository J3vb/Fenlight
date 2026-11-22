"""Claude code review: reads the repo in chunks, asks Claude for problems, opens GitHub issues.

Spend is capped: before every API call the worst-case cost of that call is checked against
what is left of --budget, so a run can never go over it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path

LABEL = "claude-review"
SEVERITIES = ("critical", "high", "medium", "low")
CODE_SUFFIXES = (".gd", ".py", ".gdshader", ".sh", ".rs", ".js")
EXCLUDED_PREFIXES = ("addons/", ".agents/", ".claude/", ".godot/")
# Lower number = reviewed first, so the budget goes to game code before tests and tools.
AREA_PRIORITY = (
    ("core/", 0),
    ("systems/net/", 1),
    ("systems/", 2),
    ("launcher/", 2),
    ("levels/", 3),
    ("deploy/", 4),
    (".github/", 4),
    ("tools/ci/", 5),
    ("tools/", 6),
    ("tests/", 8),
)
# USD per million tokens: input, output, cache write (5 min), cache read.
PRICES = {
    "claude-fable-5-2": (8.0, 40.0, 10.0, 0.20),
    "claude-opus-5-5": (4.0, 20.0, 5.0, 0.20),
    "claude-opus-5": (5.0, 25.0, 6.25, 0.50),
    "claude-opus-4-8": (5.0, 25.0, 6.25, 0.50),
    "claude-sonnet-5-5": (2.0, 10.0, 2.5, 0.10),
}
UNKNOWN_MODEL_PRICE = (10.0, 50.0, 12.5, 1.0)
# The tokenizer is byte-level, so a token covers at least one UTF-8 byte: bytes are a true upper bound.
REQUEST_OVERHEAD_TOKENS = 2_000
FATAL_STATUS = (400, 401, 403, 404)
LENSES = {
    "correctness": "Logic bugs, wrong maths, null/freed-instance access, off-by-one, broken state machines, "
    "signals connected twice or never, await/coroutine mistakes, unhandled errors.",
    "multiplayer": "Code that breaks in co-op or on a dedicated headless server: state only changed on one peer, "
    "missing authority checks, RPCs that trust bad input, client-only nodes used on the server, desyncs.",
    "performance": "Frame hitches and waste: allocations or node lookups in _process/_physics_process, "
    "first-use shader or resource loads during play, O(n^2) loops over enemies, leaks of nodes or signals.",
    "maintainability": "Breaks of the repo rules in AGENTS.md, dead code, copy-pasted logic, hard-coded numbers "
    "that belong in content data, missing tests for risky code, misleading names.",
}
FINDINGS_SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file": {"type": "string"},
                    "line": {"type": "integer"},
                    "severity": {"type": "string", "enum": list(SEVERITIES)},
                    "title": {"type": "string"},
                    "problem": {"type": "string"},
                    "fix": {"type": "string"},
                },
                "required": ["file", "line", "severity", "title", "problem", "fix"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["findings"],
    "additionalProperties": False,
}
SYSTEM_PROMPT = """You review the code of Fenlight, a wave-based zombie FPS in Godot 4.7.2 (typed \
GDScript) with Python Blender/CI tools. It has co-op with a dedicated headless server.

Report only real problems you can point at in the files you were given: a concrete file and line, what goes \
wrong, when it goes wrong, and a short fix. Skip style nits, formatting, and guesses about code you cannot see. \
If a chunk has no real problems, return an empty list. Quality beats quantity: five solid findings are worth \
more than twenty weak ones.

Severity: critical = crash, data loss or save corruption; high = gameplay or multiplayer broken in normal play; \
medium = bug in an edge case, a clear hitch, or a rule break that will cause bugs; low = minor.

Write titles under 80 characters. Write problem and fix in plain, short sentences.

Repo rules (AGENTS.md):
{rules}

All files in the repo (for context; you only see some of them):
{file_map}
"""


@dataclass
class Finding:
    file: str
    line: int
    severity: str
    title: str
    problem: str
    fix: str
    lens: str = ""

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.file, self.title)


@dataclass
class Budget:
    """Thread-safe spend cap. A call first reserves its worst-case cost; afterwards the reservation is
    swapped for the real cost. Reserved + spent never goes over the limit."""

    limit: float
    spent: float = 0.0
    reserved: float = 0.0
    pending: int = 0
    calls: int = 0
    stopped: bool = False
    log: list[str] = field(default_factory=list)
    lock: threading.Condition = field(default_factory=threading.Condition, repr=False)

    def reserve(self, worst_case: float) -> bool:
        """Waits while other calls hold reservations that might settle lower; gives up only when the
        settled spend alone leaves too little."""
        with self.lock:
            while self.spent + self.reserved + worst_case > self.limit and self.pending > 0 and not self.stopped:
                self.lock.wait()
            if self.stopped or self.spent + self.reserved + worst_case > self.limit:
                return False
            self.reserved += worst_case
            self.pending += 1
            return True

    def settle(self, reserved: float, cost: float) -> None:
        with self.lock:
            self.pending -= 1
            # Reset when idle so float rounding can't leave a phantom reservation behind.
            self.reserved = self.reserved - reserved if self.pending else 0.0
            self.spent += cost
            self.calls += 1
            self.lock.notify_all()

    def note(self, line: str) -> None:
        with self.lock:
            self.log.append(line)


def fingerprint(file: str, title: str) -> str:
    words = re.sub(r"[^a-z0-9]+", " ", title.lower()).split()
    return hashlib.sha1(f"{file}|{' '.join(words)}".encode()).hexdigest()[:12]


def price_for(model: str) -> tuple[float, float, float, float]:
    return PRICES.get(model, UNKNOWN_MODEL_PRICE)


def usage_cost(model: str, usage: dict) -> float:
    price_in, price_out, price_write, price_read = price_for(model)
    total = (
        usage.get("input_tokens", 0) * price_in
        + usage.get("output_tokens", 0) * price_out
        + usage.get("cache_creation_input_tokens", 0) * price_write
        + usage.get("cache_read_input_tokens", 0) * price_read
    )
    return total / 1_000_000


def worst_case_cost(prompt_bytes: int, max_tokens: int) -> float:
    """Upper bound for one call: one input token per UTF-8 byte, all priced as cache writes, and every
    output token at the dearest price a fallback model could charge, so a refusal fallback can't break the cap."""
    _, price_out, price_write, _ = UNKNOWN_MODEL_PRICE
    input_tokens = prompt_bytes + REQUEST_OVERHEAD_TOKENS
    return (input_tokens * price_write + max_tokens * price_out) / 1_000_000


def area_of(path: str) -> str:
    parts = path.split("/")
    return "/".join(parts[:2]) if len(parts) > 2 else parts[0]


def priority_of(path: str) -> int:
    return next((rank for prefix, rank in AREA_PRIORITY if path.startswith(prefix)), 7)


def is_reviewable(path: str) -> bool:
    if path.startswith(EXCLUDED_PREFIXES):
        return False
    if path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml")):
        return True
    return path.endswith(CODE_SUFFIXES)


def number_lines(text: str) -> str:
    return "\n".join(f"{n:>5} {line}" for n, line in enumerate(text.splitlines(), 1))


def file_block(path: str, text: str) -> str:
    return f'<file path="{path}">\n{number_lines(text)}\n</file>\n'


def make_chunks(files: dict[str, str], max_chars: int) -> list[list[str]]:
    """Packs whole areas (e.g. systems/loot) into chunks up to max_chars; only areas too big for one chunk are split."""
    by_area: dict[str, list[str]] = {}
    for path in sorted(files, key=lambda p: (priority_of(p), p)):
        by_area.setdefault(area_of(path), []).append(path)
    chunks: list[list[str]] = [[]]
    size = 0
    for paths in by_area.values():
        sizes = [len(file_block(p, files[p])) for p in paths]
        if chunks[-1] and size + sum(sizes) > max_chars:
            chunks.append([])
            size = 0
        for path, block in zip(paths, sizes, strict=True):
            if chunks[-1] and size + block > max_chars:
                chunks.append([])
                size = 0
            chunks[-1].append(path)
            size += block
    return [chunk for chunk in chunks if chunk]


def marker(finding: Finding) -> str:
    return f"<!-- {LABEL} fp={finding.fingerprint} loc={finding.file}:{finding.line} -->"


def parse_markers(body: str) -> list[tuple[str, str, int]]:
    pattern = rf"<!-- {LABEL} fp=([0-9a-f]+) loc=(\S+):(\d+) -->"
    return [(fp, file, int(line)) for fp, file, line in re.findall(pattern, body or "")]


class Deduper:
    """Drops a finding when its fingerprint was seen, or when the same file has a finding within a few lines."""

    def __init__(self, line_window: int = 3) -> None:
        self.fingerprints: set[str] = set()
        self.locations: dict[str, list[int]] = {}
        self.line_window = line_window

    def add(self, fp: str, file: str, line: int) -> None:
        self.fingerprints.add(fp)
        self.locations.setdefault(file, []).append(line)

    def seen(self, finding: Finding) -> bool:
        if finding.fingerprint in self.fingerprints:
            return True
        return any(abs(line - finding.line) <= self.line_window for line in self.locations.get(finding.file, []))

    def keep(self, finding: Finding) -> bool:
        if self.seen(finding):
            return False
        self.add(finding.fingerprint, finding.file, finding.line)
        return True


def select_findings(findings: list[Finding], deduper: Deduper, min_severity: str, max_issues: int) -> list[Finding]:
    cutoff = SEVERITIES.index(min_severity)
    ranked = sorted(findings, key=lambda f: SEVERITIES.index(f.severity))
    chosen = []
    for finding in ranked:
        if SEVERITIES.index(finding.severity) > cutoff or len(chosen) >= max_issues:
            continue
        if deduper.keep(finding):
            chosen.append(finding)
    return chosen


def issue_body(finding: Finding, sha: str, repo: str) -> str:
    link = f"https://github.com/{repo}/blob/{sha}/{finding.file}#L{finding.line}" if repo and sha else finding.file
    return (
        f"**Severity:** {finding.severity}  \n**Where:** [`{finding.file}:{finding.line}`]({link})  \n"
        f"**Review lens:** {finding.lens}\n\n### Problem\n{finding.problem}\n\n### Suggested fix\n{finding.fix}\n\n"
        "_Found by the automated Claude code review. Check it before acting; close it as not planned if wrong._\n\n"
        f"{marker(finding)}\n"
    )


def build_user_content(paths: list[str], files: dict[str, str], lens: str) -> list[dict]:
    code = "".join(file_block(p, files[p]) for p in paths)
    return [
        {"type": "text", "text": code, "cache_control": {"type": "ephemeral"}},
        {"type": "text", "text": f"Review the files above with this focus only: {lens}: {LENSES[lens]}"},
    ]


def parse_findings(text: str, allowed_files: set[str], lens: str) -> list[Finding]:
    data = json.loads(text)
    out = []
    for item in data.get("findings", []):
        if item.get("file") in allowed_files and item.get("severity") in SEVERITIES:
            out.append(Finding(**{k: item[k] for k in FINDINGS_SCHEMA["properties"]["findings"]["items"]["required"]}))
            out[-1].lens = lens
    return out


class ClaudeReviewer:
    def __init__(self, client, model: str, effort: str, max_tokens: int, system: str) -> None:
        self.client = client
        self.model = model
        self.effort = effort
        self.max_tokens = max_tokens
        self.system = system

    def review(self, content: list[dict]) -> tuple[str, str, dict, str]:
        """Returns (response text, model that answered, usage dict, stop reason)."""
        with self.client.beta.messages.stream(
            model=self.model,
            max_tokens=self.max_tokens,
            system=[{"type": "text", "text": self.system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": content}],
            output_config={"effort": self.effort, "format": {"type": "json_schema", "schema": FINDINGS_SCHEMA}},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        ) as stream:
            message = stream.get_final_message()
        text = next((b.text for b in message.content if b.type == "text"), '{"findings": []}')
        usage = {
            key: getattr(message.usage, key, 0) or 0
            for key in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
        }
        return text, message.model, usage, message.stop_reason


def run_review(reviewer, files, chunks: list[list[str]], lenses: list[str], budget: Budget, workers: int = 1):
    """Reviews chunks in parallel (lenses of one chunk run in order so they reuse its prompt cache)."""
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        jobs = [
            pool.submit(review_chunk, reviewer, files, paths, lenses, budget, i) for i, paths in enumerate(chunks, 1)
        ]
        return [finding for job in jobs for finding in job.result()]


def review_chunk(reviewer, files, paths: list[str], lenses: list[str], budget: Budget, index: int) -> list[Finding]:
    findings: list[Finding] = []
    for lens in lenses:
        content = build_user_content(paths, files, lens)
        size = len(reviewer.system.encode()) + sum(len(c["text"].encode()) for c in content)
        reserved = worst_case_cost(size, reviewer.max_tokens)
        if budget.stopped:
            return findings
        if not budget.reserve(reserved):
            budget.note(f"chunk {index} ({lens}) skipped: budget left too small")
            return findings
        findings.extend(review_one(reviewer, content, set(paths), lens, budget, index, reserved))
    return findings


def review_one(reviewer, content, allowed: set[str], lens: str, budget: Budget, index: int, reserved: float):
    try:
        text, model, usage, stop = reviewer.review(content)
    except Exception as error:  # one bad call must not lose the findings so far
        rejected = getattr(error, "status_code", None) in FATAL_STATUS
        if rejected:
            budget.stopped = True
            budget.note("stopping: the API rejected the request (check the key, model name or parameters)")
        # A rejected request is not billed; any other failure may have been, so it keeps its reservation.
        budget.settle(reserved, 0.0 if rejected else reserved)
        budget.note(f"chunk {index} ({lens}): API error {type(error).__name__}: {error}")
        return []
    cost = usage_cost(model, usage)
    budget.settle(reserved, cost)
    budget.note(f"chunk {index} ({lens}): {model} ${cost:.3f}, total ${budget.spent:.2f}, stop={stop}")
    if stop in ("refusal", "max_tokens"):
        return []
    try:
        return parse_findings(text, allowed, lens)
    except (json.JSONDecodeError, TypeError, KeyError):
        budget.note(f"chunk {index} ({lens}): could not read the JSON reply")
        return []


class GitHub:
    def __init__(self, repo: str, token: str) -> None:
        self.repo = repo
        self.token = token

    def call(self, method: str, path: str, payload: dict | None = None):
        request = urllib.request.Request(
            f"https://api.github.com/repos/{self.repo}{path}",
            data=json.dumps(payload).encode() if payload is not None else None,
            method=method,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read() or b"null")

    def ensure_labels(self) -> None:
        colours = {LABEL: "5319e7", "severity:critical": "b60205", "severity:high": "d93f0b"}
        colours |= {"severity:medium": "fbca04", "severity:low": "c2e0c6"}
        for name, colour in colours.items():
            try:
                self.call("POST", "/labels", {"name": name, "color": colour})
            except urllib.error.HTTPError as error:
                if error.code != 422:  # 422 = label already exists
                    raise

    def existing_markers(self) -> list[tuple[str, str, int]]:
        """Markers from every claude-review issue, open or closed, so closed ones are not reopened."""
        found = []
        for page in range(1, 50):
            issues = self.call("GET", f"/issues?labels={LABEL}&state=all&per_page=100&page={page}")
            for issue in issues:
                found.extend(parse_markers(issue.get("body") or ""))
            if len(issues) < 100:
                break
        return found

    def create_issue(self, finding: Finding, sha: str) -> str:
        payload = {
            "title": f"[{finding.severity}] {finding.title}"[:250],
            "body": issue_body(finding, sha, self.repo),
            "labels": [LABEL, f"severity:{finding.severity}"],
        }
        return self.call("POST", "/issues", payload)["html_url"]


def git_files(root: Path, since: str | None) -> list[str]:
    if since:
        args = ["git", "diff", "--name-only", "--diff-filter=AMR", f"{since}...HEAD"]
    else:
        args = ["git", "ls-files"]
    out = subprocess.run(args, cwd=root, check=True, capture_output=True, text=True).stdout
    return [p for p in out.splitlines() if is_reviewable(p)]


def load_files(root: Path, paths: list[str], max_file_chars: int) -> dict[str, str]:
    files = {}
    for path in paths:
        text = (root / path).read_text(encoding="utf-8", errors="replace")
        if 0 < len(text) <= max_file_chars:
            files[path] = text
    return files


def build_system(root: Path) -> str:
    rules_path = root / "AGENTS.md"
    rules = rules_path.read_text(encoding="utf-8") if rules_path.exists() else "(none)"
    all_files = subprocess.run(["git", "ls-files"], cwd=root, check=True, capture_output=True, text=True).stdout
    file_map = "\n".join(p for p in all_files.splitlines() if is_reviewable(p))
    return SYSTEM_PROMPT.format(rules=rules, file_map=file_map)


def write_findings(findings: list[Finding], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "findings.json").write_text(json.dumps([asdict(f) for f in findings], indent=2))


def write_summary(args, budget: Budget, findings: list[Finding], created: list[str], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "## Claude code review",
        f"- Mode: {'changed since ' + args.since if args.since else 'full repo'}, model {args.model}, "
        f"effort {args.effort}",
        f"- Spent: **${budget.spent:.2f}** of ${budget.limit:.2f} in {budget.calls} calls",
        f"- Findings: {len(findings)} raw, {len(created)} new issues"
        + (" (dry run, no issues created)" if args.dry_run else ""),
        "",
        *(f"- {url}" for url in created),
        "",
        "<details><summary>Call log</summary>\n",
        *(f"    {entry}" for entry in budget.log),
        "</details>",
    ]
    text = "\n".join(lines) + "\n"
    (out_dir / "summary.md").write_text(text)
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as handle:
            handle.write(text)
    sys.stdout.write(text)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget", type=float, default=5.0, help="hard USD cap for the whole run")
    parser.add_argument("--model", default="claude-fable-5-2")
    parser.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])
    parser.add_argument("--lenses", default=",".join(LENSES), help="comma list of: " + ", ".join(LENSES))
    parser.add_argument("--since", default="", help="only review files changed since this git ref")
    parser.add_argument("--chunk-chars", type=int, default=180_000, help="max code characters per API call")
    parser.add_argument("--max-file-chars", type=int, default=150_000, help="skip files bigger than this")
    parser.add_argument("--max-tokens", type=int, default=32_000)
    parser.add_argument("--min-severity", default="medium", choices=list(SEVERITIES))
    parser.add_argument("--max-issues", type=int, default=60)
    parser.add_argument("--workers", type=int, default=3, help="parallel API calls")
    parser.add_argument("--dry-run", action="store_true", help="review but do not create issues")
    parser.add_argument("--out", default="claude-review-out")
    args = parser.parse_args(argv)
    args.lenses = [lens.strip() for lens in args.lenses.split(",") if lens.strip()]
    unknown = set(args.lenses) - set(LENSES)
    if unknown:
        parser.error(f"unknown lens: {', '.join(sorted(unknown))}")
    return args


def create_issues(github: GitHub | None, chosen: list[Finding], sha: str, budget: Budget) -> list[str]:
    created = []
    for finding in chosen:
        if github is None:
            created.append(f"(dry run) [{finding.severity}] {finding.file}:{finding.line} {finding.title}")
            continue
        try:
            created.append(github.create_issue(finding, sha))
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            budget.note(f"could not open issue for {finding.file}:{finding.line}: {error}")
        time.sleep(2)  # stay under GitHub's content-creation rate limit
    return created


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    files = load_files(root, git_files(root, args.since), args.max_file_chars)
    chunks = make_chunks(files, args.chunk_chars)
    budget = Budget(limit=args.budget)
    budget.log.append(f"{len(files)} files in {len(chunks)} chunks x {len(args.lenses)} lenses")

    github = None if args.dry_run else GitHub(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])
    deduper = Deduper()
    if github:
        github.ensure_labels()
        for fp, file, line in github.existing_markers():
            deduper.add(fp, file, line)

    import anthropic  # imported here so the unit tests run without the SDK installed

    system = build_system(root)
    reviewer = ClaudeReviewer(anthropic.Anthropic(max_retries=8), args.model, args.effort, args.max_tokens, system)
    findings = run_review(reviewer, files, chunks, args.lenses, budget, args.workers)
    write_findings(findings, root / args.out)  # saved first so paid results survive a GitHub failure
    chosen = select_findings(findings, deduper, args.min_severity, args.max_issues)
    created = create_issues(github, chosen, os.environ.get("GITHUB_SHA", ""), budget)
    write_summary(args, budget, findings, created, root / args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
