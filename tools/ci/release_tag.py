"""Picks and checks the tag for a release cut from the Actions tab (docs/RELEASING.md).

pick --channel stable|test [--version X.Y.Z[-test.N]]: reads existing tags on stdin, prints the new
tag. With no version it takes the next patch after the newest stable tag (test: its next test number).
checks: reads a commit's check runs (one JSON object per line) on stdin, fails unless CI passed.
Only the newest run of each check counts, so a run cancelled by a later one is ignored.
"""

import argparse
import json
import re
import sys

TAG = re.compile(r"^v(\d+)\.(\d+)\.(\d+)(?:-test\.(\d+))?$")
FAILED = {"failure", "timed_out", "cancelled", "action_required", "startup_failure"}


def parse(tag: str) -> tuple[int, int, int, int | None] | None:
    match = TAG.match(tag)
    if match is None:
        return None
    test = match.group(4)
    return int(match.group(1)), int(match.group(2)), int(match.group(3)), int(test) if test else None


def pick_tag(channel: str, version: str, tags: list[str]) -> str:
    if channel not in ("stable", "test"):
        raise ValueError(f"channel must be stable or test, not {channel}")
    known = [v for v in (parse(t) for t in tags) if v is not None]
    latest = max((v[:3] for v in known if v[3] is None), default=(0, 0, 0))
    if not version:
        base = (latest[0], latest[1], latest[2] + 1)
        version = ".".join(str(n) for n in base)
        if channel == "test":
            done = [v[3] for v in known if v[3] is not None and v[:3] == base]
            version += f"-test.{max(done, default=0) + 1}"
    tag = "v" + version.strip().removeprefix("v")
    wanted = parse(tag)
    if wanted is None or (wanted[3] is None) != (channel == "stable"):
        shape = "X.Y.Z" if channel == "stable" else "X.Y.Z-test.N"
        raise ValueError(f"{channel} versions look like {shape}, not {version}")
    if tag in tags:
        raise ValueError(f"{tag} already exists: release a newer version instead")
    if wanted[:3] <= latest:
        raise ValueError(f"{tag} is not newer than the newest stable release v" + ".".join(str(n) for n in latest))
    newer_tests = [v for v in known if v[3] is not None and v[:3] == wanted[:3] and v[3] > (wanted[3] or 0)]
    if wanted[3] is not None and newer_tests:
        raise ValueError(f"{tag} is older than a test build that already exists")
    return tag


def ci_problem(runs: list[dict]) -> str:
    latest: dict[str, dict] = {}
    for run in sorted(runs, key=lambda r: r.get("id", 0)):
        latest[run["name"]] = run
    runs = list(latest.values())
    failed = sorted({r["name"] for r in runs if r.get("conclusion") in FAILED})
    if failed:
        return "CI failed on this commit: " + ", ".join(failed)
    if not any(r["name"] == "test" and r.get("conclusion") == "success" for r in runs):
        return "the CI 'test' check has not passed on this commit yet"
    return ""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    pick = commands.add_parser("pick")
    pick.add_argument("--channel", required=True)
    pick.add_argument("--version", default="")
    commands.add_parser("checks")
    args = parser.parse_args(argv)
    lines = [line.strip() for line in sys.stdin if line.strip()]
    try:
        if args.command == "pick":
            print(pick_tag(args.channel, args.version, lines))
            return 0
        problem = ci_problem([json.loads(line) for line in lines])
    except ValueError as error:
        print(f"::error::{error}")
        return 1
    if problem:
        print(f"::error::{problem}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
