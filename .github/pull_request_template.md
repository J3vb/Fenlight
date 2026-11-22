## What changed

<!-- One or two sentences. -->

## Why

<!-- The issue, design doc section or bug this is for. -->

Plan: <!-- docs/plans/<file>.md, step N, or "none: <why no plan is needed>" -->

## How it was tested

<!-- Which tests you added or changed. For feel/visual changes, what you checked in-game. -->

### Review
<!-- Run the pre-merge-review skill before marking this PR ready. CI checks the "Review:" line on a ready PR. -->
Review: <!-- fresh subagent at <sha>; checklists: game, coop   OR   skipped, docs only -->
<!-- Counts, then one line per finding: `path:line` problem - fixed in <sha> / declined: reason / not a bug: why -->

### Ready to build
<!-- Link the plan that has the filled-in checklist from docs/FOUNDATIONS.md#ready-to-build,
or paste it here for a small change. Write n.a. only for docs, art or test-only PRs. -->

### Simplicity check
- Only builds what this phase needs: yes / no (why)
- New autoloads, managers or base classes: none / list + which rule allows it
- New abstraction used in fewer than 3 places: none / list
- Anything a Godot built-in already does: none / list
- Dead code removed: yes / n.a.

## Checklist

- [ ] CI is green (`quality`, `test` and `soak`)
- [ ] Behaviour change has a test (or the `no-tests-needed` label and a reason above)
- [ ] Bug fix has a test that failed before the fix
- [ ] Follows the Keep it simple rules in AGENTS.md
- [ ] Built only the plan step named above (or no plan needed, see docs/plans/README.md)
- [ ] Ready-to-build checklist filled in, no shaky foundation left unhandled (or n.a.)
- [ ] Followed docs/HOW_TO_ADD.md for new content/systems (or n.a.)
- [ ] Structure rules pass (tools/ci/check_rules.py)
- [ ] Only touched files this task needed
- [ ] One label: `new`, `fix`, `balance` or `tech`
- [ ] Review section filled: every Blocking finding fixed, every declined Suggestion has a reason
