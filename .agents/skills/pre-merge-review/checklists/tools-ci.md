# Tools, CI and workflows

1. **The check can fail.** No `|| true`, `continue-on-error`, swallowed exit
   code, condition that is always true, or "no files matched" counted as a pass.
2. **Nothing weakened.** No lower threshold or warning level, no skipped or
   deleted test, no baseline file that grew (`untested_baseline.txt`,
   `content_id_baseline.txt`).
3. **Triggers and path filters.** Does the workflow run for the files that
   matter? Does a path filter leave a check that never reports? Does
   `concurrency` cancel a run that was needed?
4. **Injection and secrets.** PR title, body or branch name never placed in
   a `run:` line with `${{ }}`; pass them through `env`. No
   `pull_request_target` with a checkout of PR code. Least `permissions`.
5. **Spend.** Anything that calls a paid API runs only by hand with a budget
   cap. A new automatic trigger for it needs the owner's yes in the PR.
6. **Pinned versions agree** across `ci.yml`, `.claude/hooks/session-start.sh`
   and `AGENTS.md` (Godot, gdtoolkit, ruff, Rust toolchain, actions).
7. **Python.** `subprocess` with a list and no `shell=True`, exit codes
   checked, UTF-8 set, paths from the repo root, `base...HEAD` diffs that
   handle renamed and deleted files, enough `fetch-depth`.
8. **Shell.** `set -euo pipefail`, quoted variables, no pipe that hides a failure.
9. **The check has a test** in `tools/ci/test_*.py`, with a case that fails.
10. **Generators are repeatable.** Asset, sound and map scripts give the same
    output each run (no clock, unseeded random, dictionary order or absolute
    path), and the regenerated output is committed with the script.
11. **Release tools.** Frozen names and channel rules from
    `docs/RELEASING.md` (test and stable never mixed); nothing publishes from a PR.
12. **Agent files.** Skills edited in `.agents/skills` and mirrored;
    third-party skill folders untouched; `AGENTS.md` stays within its word
    budget; no person's name in any file.
13. **Session hook.** Safe to run twice, quick, and a failed download does
    not block the session.
