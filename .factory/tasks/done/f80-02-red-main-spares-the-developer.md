---
id: f80-02-red-main-spares-the-developer
milestone: f80-developer-rating-could-be-more-tailored
difficulty: 5
agent: lead
depends_on: []
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
finding: f80-developer-rating-could-be-more-tailored-F1
---

### Goal
A developer attempt that fails only `all-tests`, on tests main fails too, costs no attempt and no rating game: the ticket waits for main as a lead ticket does (F106 D5).

### Context
Read `_main_is_red`, `_look_at_main` and `waits_for_main` in `runner/loop.py` (main-red for lead tickets), and the developer attempt loop in `run_task` (where `failed` is the first failing gate, and two of them escalate). Follow `_red_main` and the tests after it in `tests/runner/test_loop.py`.
- f80-01 (2026-10-27): Qwen's attempt 1 built the bay and passed every gate but `all-tests`, which failed on `bug-03`'s test on main itself. 72 minutes, a second attempt that blocked `needs-file`, an escalation to Opus ($1.56), and two "not merged" coding games against Qwen's rating for work that was right.
- Only `all-tests` qualifies: every other gate is about the developer's own diff.
- `waits_for_main` today holds lead tickets only (`router.lead_only`); a developer ticket waiting on its branch needs to be held the same way, and to run its gates again (not a new attempt) once `_look_at_main` sees main pass.

### Done when
- a developer attempt whose only failing gate is `all-tests`, with main failing the same check, ends with the ticket waiting on its branch, the main-red owner item set, no escalation, and the attempt not counted in `rec.attempts`
- the same attempt with main passing `all-tests` counts as a failed attempt, as today
- an attempt failing another gate besides `all-tests` counts as a failed attempt, as today, without running checks on main
- once main passes again, the waiting developer ticket's gates run on its branch and it merges if they pass
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
