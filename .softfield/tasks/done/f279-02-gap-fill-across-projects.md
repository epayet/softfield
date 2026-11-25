---
id: f279-02-gap-fill-across-projects
milestone: f279-i-would-like-to-be-able
agent: lead
difficulty: 4
depends_on: [f279-01-the-runners-plan]
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
Over Claude's pace or past a mark, a lead ticket fills the gap only when no project has anything else that can start, as ADR 50 item 2 says, and the stored plan shows that order.

### Context
Read `.softfield/cards/f279-i-would-like-to-be-able.md` ("What happens today", last bullet, and D5) and `.softfield/adr/50-the-line-never-idles-for-the-pace.md` item 2.
- Today `def project_round` in `runner/loop.py` asks each project in turn for one ticket, and `def choose_ticket` lets the first lead ticket fill the gap when that project alone has nothing else (`first(free)` after `first(developers)`). So travel-companion's lead ticket goes before softfield's developer ticket.
- Make the gap the factory's: a first pass over every project that takes only what `choose_ticket` would take without the gap-filling lead ticket, then, when none ran, a second pass that lets the first project's lead ticket fill it. Under the pace, nothing changes.
- `factory_plan` (f279-01) lists the lines in the same order, so the page and the dry run agree with the run.
- `runner/**` is protected: tests first.

### Done when
- over pace, project A (first in the order) with only a lead ticket that can go and project B with a developer ticket that can go: B's developer ticket runs first, then A's lead ticket
- over pace, with no developer ticket that can go anywhere: the first project's first lead ticket runs, as today
- under the pace, project A's lead ticket goes first, as today
- the stored plan lists the tickets in the order they run in each case
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
