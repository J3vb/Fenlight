"""Quality gate for pull requests. Run from the repo root:

    python tools/ci/check_pr.py <base-ref> [--no-tests-label] [--pr-body-file <path>]

Checks all tracked GDScript and Python outside vendored third-party folders. Only the tests-required
rule and the review-recorded rule use the files the PR changed. The review rule runs only when CI passes the
body of a ready (non-draft) PR.
"""

import re
import subprocess
import sys
from pathlib import Path

MAX_FUNCTION_LINES = 50
MAX_COMPLEXITY = 10
LINE_LENGTH = "120"
LOGIC_DIRS = ("core/", "systems/")
# Third-party code kept as published: Godot addons and the vendored agent skills.
VENDORED = ("addons/", ".agents/skills/", ".agents/plugins/", ".claude/skills/")
FUNC_RE = re.compile(r"^(\s*)(static\s+)?func\s+(\w+)")
COMPLEXITY_RE = re.compile(r"^\s*F\s+(\d+):\d+\s+(\S+)\s+-\s+[A-F]\s+\((\d+)\)\s*$")
# Files that need no independent review: prose, binary assets and launcher news data.
REVIEW_EXEMPT_DIRS = ("docs/", "assets/", "launcher/news/")
REVIEW_LINE_RE = re.compile(r"^Review:[ \t]*(\S.*)$", re.MULTILINE)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def changed_files(base: str, diff_filter: str = "ACMR") -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--name-only", f"--diff-filter={diff_filter}", f"{base}...HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [line for line in out.splitlines() if line]


def indent_of(line: str) -> int:
    return len(line) - len(line.lstrip("\t "))


def tracked_files(suffix: str) -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], check=True, capture_output=True, text=True).stdout
    return [path for path in out.split("\0") if path.endswith(suffix) and not path.startswith(VENDORED)]


def signature_end(lines: list[str], start: int) -> int:
    depth = 0
    for index in range(start, len(lines)):
        code = lines[index].split("#", 1)[0]
        depth += code.count("(") + code.count("[") - code.count(")") - code.count("]")
        if depth <= 0:
            return index
    return start


def function_lines(lines: list[str], start: int) -> int:
    depth = indent_of(lines[start])
    body = 0
    for later in lines[signature_end(lines, start) + 1 :]:
        stripped = later.strip()
        if not stripped:
            continue
        if indent_of(later) <= depth and not stripped.startswith("#"):
            break
        body += 1
    return body


def long_functions(path: str) -> list[str]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    problems = []
    for i, line in enumerate(lines):
        match = FUNC_RE.match(line)
        if not match:
            continue
        body = function_lines(lines, i)
        if body > MAX_FUNCTION_LINES:
            problems.append(f"{path}:{i + 1}: function '{match.group(3)}' has {body} lines (max {MAX_FUNCTION_LINES})")
    return problems


def run(cmd: list[str]) -> bool:
    print("$ " + " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=False).returncode == 0


def complex_functions(output: str) -> list[str]:
    problems = []
    path = ""
    for line in output.splitlines():
        match = COMPLEXITY_RE.match(line)
        if match:
            number, name, score = match.groups()
            if int(score) > MAX_COMPLEXITY:
                problems.append(f"{path}:{number}: function '{name}' has complexity {score} (max {MAX_COMPLEXITY})")
        elif line and not line[0].isspace():
            path = line
    return problems


def check_complexity(files: list[str]) -> bool:
    cmd = ["gdradon", "cc", *files]
    print("$ " + " ".join(cmd), flush=True)
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    problems = complex_functions(result.stdout)
    for problem in problems:
        print(problem)
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    # gdradon reports processing errors on stderr even when it exits zero.
    return result.returncode == 0 and not result.stderr and not problems


def check_gdscript(files: list[str]) -> bool:
    if not files:
        return True
    ok = run(["gdlint", *files])
    ok &= run(["gdformat", "--check", "--line-length", LINE_LENGTH, *files])
    long = [problem for path in files for problem in long_functions(path)]
    for problem in long:
        print(problem)
    ok &= not long
    ok &= check_complexity(files)
    return ok


def check_python(files: list[str]) -> bool:
    if not files:
        return True
    ok = run(["ruff", "check", *files])
    ok &= run(["ruff", "format", "--check", *files])
    return ok


def tests_required(files: list[str], skip_tests_rule: bool) -> bool:
    logic_changed = [f for f in files if f.endswith(".gd") and f.startswith(LOGIC_DIRS)]
    tests_changed = [f for f in files if f.startswith("tests/")]
    if not logic_changed or tests_changed:
        return True
    if skip_tests_rule:
        print("Code changed without tests; allowed by the 'no-tests-needed' label.")
        return True
    print("Code in core/ or systems/ changed but no file in tests/ changed:")
    for path in logic_changed:
        print("  " + path)
    print("Add or update a test, or add the 'no-tests-needed' label if this is visual-only.")
    return False


def needs_review(files: list[str]) -> list[str]:
    return [f for f in files if f.endswith(".gdshader") or not (f.endswith(".md") or f.startswith(REVIEW_EXEMPT_DIRS))]


def review_recorded(files: list[str], body: str | None) -> bool:
    """A ready PR that changes code must say how it was reviewed (pre-merge-review skill)."""
    code = needs_review(files)
    if body is None or not code:
        return True
    matches = REVIEW_LINE_RE.findall(HTML_COMMENT_RE.sub("", body))
    if matches and not matches[-1].strip().lower().startswith("skipped"):
        return True
    print("This PR changes code but its body has no filled 'Review:' line (or says skipped):")
    for path in code[:10]:
        print("  " + path)
    print("Run the pre-merge-review skill and fill the Review section of the PR.")
    print("Editing the body does not start CI: use 'Re-run jobs' on this run or push the next commit.")
    return False


def pr_body() -> str | None:
    flag = "--pr-body-file"
    if flag not in sys.argv:
        return None
    return Path(sys.argv[sys.argv.index(flag) + 1]).read_text(encoding="utf-8")


def main() -> int:
    files = changed_files(sys.argv[1])
    ok = check_gdscript(tracked_files(".gd"))
    ok &= check_python(tracked_files(".py"))
    ok &= tests_required(files, "--no-tests-label" in sys.argv)
    ok &= review_recorded(files + changed_files(sys.argv[1], "D"), pr_body())
    ok &= run([sys.executable, str(Path(__file__).with_name("check_rules.py"))])
    ok &= run([sys.executable, str(Path(__file__).with_name("check_plans.py"))])
    ok &= run([sys.executable, str(Path(__file__).with_name("check_saved_ids.py")), sys.argv[1]])

    print("Quality checks passed." if ok else "Quality checks failed. Fix the problems above.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
