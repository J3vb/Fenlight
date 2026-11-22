---
name: pre-merge-review
description: Get an independent review of your own diff from a fresh subagent before the PR is marked ready. Use at the end of every task that changes code (game, co-op, launcher, tools or CI), after local checks pass and before merge.
---

# Pre-merge review

CI checks format, size and tests. It does not find a frozen window, a
double launch or a delete of the wrong folder. A reviewer who did not write
the code does. You run that reviewer; you do not review your own work.

## When

1. Local checks pass and the draft PR is pushed.
2. Run this skill. Fix what it finds. Run the local checks again.
3. Fill the PR's **Review** section, then mark the PR ready. CI checks the
   `Review:` line on a ready PR.
4. Later pushes: review again only when the new commits change more than
   50 lines of non-test code or a code file the reviewer did not see. Then
   review only `git diff <reviewed-sha>..HEAD`.

**Skip** when every changed file is a `.md` file or is under `docs/`,
`assets/` or `launcher/news/`. Write `Review: skipped, docs only` (or
`assets only`). There is no "too small" skip for code: the worst launcher
bugs were small diffs.

## Pick the checklists

Run `git diff --name-only origin/main...HEAD` and take every row that matches:

| Changed | Checklist |
|---|---|
| `core/`, `systems/`, `levels/`, `content/`, `tests/` | `checklists/game.md` |
| The diff has `@rpc`, `.rpc(`, `rpc_id`, `multiplayer.`, `Net.`, a MultiplayerSpawner or Synchronizer, or touches `systems/net/` | also `checklists/coop.md` |
| `launcher/core/`, `launcher/src-tauri/` | `checklists/launcher-rust.md` |
| `launcher/ui/` | `checklists/launcher-ui.md` (and `launcher-rust.md` if a command or event changed) |
| `tools/`, `.github/`, `.claude/hooks/`, `deploy/` | `checklists/tools-ci.md` |

## Brief the reviewer

Start one fresh subagent (Claude Code: the Agent tool, general-purpose). For
a diff over about 800 changed lines, or one that spans game and launcher,
start one per area at the same time. If you have no subagent tool, run the
brief in a new session; if that is not possible either, write
`Review: self-review only, no subagent available` so it is visible.

Give it only the brief below. Do **not** give it the PR description, your
plan reasoning, what you tested or what you think is fine: that anchors it.
One neutral sentence of intended behaviour is allowed.

> Review a change in this repository. Do not edit any file.
> Change: `git diff <base-sha>...HEAD` (files: <list>).
> Intended behaviour: <one sentence, no claims about correctness>.
> Read `AGENTS.md` code rules and these checklists: <paths under
> `.agents/skills/pre-merge-review/checklists/`>.
> Read each changed file in full and the callers of what changed, not only
> the diff. Go through every checklist line and look for real bugs: for each
> one give `path:line`, the concrete scenario (what the player or system
> does, what goes wrong), **Blocking** or **Suggestion**, and the smallest
> fix. Blocking = wrong behaviour, data loss, a freeze or crash, a co-op
> desync, or a broken repo rule. Do not report style, formatting or size
> (CI does), and do not ask for new abstractions (Keep it simple). End with
> the checklist lines you could not check and why. If you find nothing, say so.

## Handle the findings

1. **Verify each one.** Open the line and follow the scenario. Best proof is
   a test that fails. A finding is not true just because it was reported, and
   not false just because your tests pass.
2. **Blocking and true:** fix it in this PR, with a test that fails without
   the fix where a test is possible.
3. **Suggestion:** fix it, or decline it with a one-line reason.
4. **Not a bug:** say why in one line (the line that makes it safe).
5. Out of your task's files and not Blocking: open a Task issue and link it.

## Record it in the PR

    ### Review
    Review: fresh subagent at <sha>; checklists: game, coop
    Blocking 2 (fixed 2). Suggestions 3 (fixed 1, declined 2). Not a bug 1.
    - `systems/x/y.gd:41` double purchase on two quick presses - fixed in <sha>
    - `launcher/core/src/install.rs:148` suggestion to keep old folder - declined: <reason>

## Output

The filled Review section, and a PR with no open Blocking finding.
