# Milestone F135: Reviews stop at once: they look for end-to-end tests the split removed

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-15.

## Notes
Why is there a couple of 'end-to-end tests fail on staging
softfield milestone f28-the-first-time-i-clicked-on' review stop on the overview

## What we know (2026-10-15)
- Both stops, F28's (2026-10-15 07:35) and F19's (00:23), are the same failure. Their `e2e.txt` in `.factory/var/runs/20261015-073531/` and `20261015-002300/` read: `ERROR: file or directory not found: tests/e2e`. No test failed: none ran.
- The milestone review (`review_milestone`, `runner/milestone.py`) runs `run_e2e` (`runner/loop.py`) before each round: `pytest -m e2e … tests/e2e`. Those were Coucou's browser tests. Since the split (ADR 30, 2026-10-14) Softfield has no `tests/e2e`, so every Softfield review now stops before Claude reads a line. F28 and F19 are the first two reviews since the split; F26's (2026-10-10) was the last clean one, run while Coucou's tests were still in the repo.
- ADR 30 item 3 moved the checks to each project's `[checks]` in `.factory/project.toml`; the end-to-end run was left behind, hard-coded.
- The stop is recorded in `state.json`'s `review_stop`, so `due_reviews` counts F28 and F19 as reviewed: nothing reruns them, and their "Needs you" items wait for a terminal command.
- F101 (`uv runner run` command stopped when…) was the third, at 08:40; the owner signed it off at 09:08 without a review round. F28 and F19 still wait.

## Outcome
A Softfield milestone review goes straight to Claude's rounds; F28 and F19 get their review without the owner doing anything, and their two stops leave Needs you.

## Done when
- a review of a project with no end-to-end tests runs its rounds, and says in its log that there were none to run
- F28's and F19's reviews run again on the runner's own, and their review-stop items go once their verdict is written

## Decisions
- **D1. No end-to-end folder, no end-to-end run.** `run_e2e` runs only when the project has `tests/e2e/`; with none, the review logs "no end-to-end tests" and goes on. Coucou keeps its run unchanged. No new `[checks]` key: nothing needs one yet.
- **D2. The stale stops are due again.** A review whose recorded stop is "end-to-end tests fail on staging" while the project has no `tests/e2e/` is due (`due_reviews`): that stop can only have come from the missing folder. Its earlier rounds in `review_counts` are kept (there were none).
- **D3. Lead ticket.** `runner/**` is protected.

## Tickets
- f135-01-no-e2e-no-stop (lead)
