---
id: f285-02-pre-review-when-idle
milestone: f285-i-think-i-said-at-some
depends_on: [f285-01-pre-review-job]
agent: lead
difficulty: 3
area: factory
files:
  - runner/loop.py
  - runner/dispatch.py
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_dispatch.py
---

### Goal
When Claude is at its real limit and nothing else can start, the runner pre-reviews the first eligible milestone instead of standing idle: at most three times per milestone, and only after a new merge since its last pre-review (ADR 51 items 2 and 4).

### Context
Read ADR 51 (`.softfield/adr/51-copilot-pre-reviews-while-claude-is-out.md`) and D2 and D3 in `.softfield/cards/f285-i-think-i-said-at-some.md`. f285-01 added `pre_review(s, milestone)` in `runner/loop.py`. Then in `runner/loop.py`: `work_queue` (where it writes `_idle_line` and calls `_idle_holds`), `choose_ticket`, `_held_at_the_limit`, `_queue_due_review`; in `runner/milestone.py`: `due_reviews`; in `runner/dispatch.py`: `dry_run_plan` and how it names the next job. Tests to follow: `test_a_reviews_lead_fix_is_held_by_the_weeks_pace_line_as_any` in `tests/runner/test_loop.py`, and the dry run's next-line tests in `tests/runner/test_dispatch.py`.
- Count a milestone's pre-reviews from the metrics database's `jobs` (role `pre-review`, outcome `passed`, its `milestone_id`); with no database, none run.
- "A new merge" means a done ticket of the milestone merged after the last passed pre-review's start.
- The owner's pause holds it, as every job.
- The runner and the dry run decide through the same function, as ADR 44 item 9 asks of the pick.

### Done when
- Claude at 100%, a milestone's review waiting for Claude, no free developer ticket: the turn runs `pre_review` on that milestone instead of the idle hold, and the dry run names "Copilot's pre-review of F…" as next
- with a free developer ticket, or Claude under its limit, no pre-review runs
- a milestone with three passed pre-reviews, or with no merge since its last one, gets none; the next eligible milestone in `due_reviews` order does
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
