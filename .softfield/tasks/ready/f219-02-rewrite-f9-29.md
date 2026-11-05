---
id: f219-02-rewrite-f9-29
milestone: f219-lead-tickets-don-t-wait-on
agent: lead
difficulty: 2
depends_on: [f219-01-one-lead-rule]
files:
  - .softfield/tasks/ready/f9-29-week-pace.md
  - .softfield/adr/25-pace-with-a-margin.md
tests:
  - tests/runner/test_tasks.py
---

### Goal
f9-29 draws what the runner now does, from `.softfield/cards/f219-mockup/lead-stop.html`, using the runner's own rule.

### Context
Read D7 in `.softfield/cards/f219-lead-tickets-don-t-wait-on.md` and `.softfield/adr/44-lead-tickets-stop-at-the-reserve.md`.
- In `.softfield/tasks/ready/f9-29-week-pace.md`, under the same id: the picture becomes the f219 mock-up, Proposed; whether a lead ticket is held comes from `lead_hold` in `runner/allowance.py`, not a second check; "no pace line in the sweep" becomes the mock-up's last-hours plate; the mark's words and the legend's line about the mark change as drawn. Add `f219-01-one-lead-rule` to its `depends_on`. It keeps the until-about function and its fast lane and lever exceptions.
- If f9-29 has already run, leave `.softfield/tasks/done/` alone and write a new ready ticket, f219-03-week-pace-matches-the-rule, for what it drew differently from the mock-up.
- In `.softfield/adr/25-pace-with-a-margin.md`, one line under its header: "See ADR 44: the runner applied this to lead tickets only from then, and its evidence came from a dry run that disagreed with the runner." Nothing else in it changes.

### Done when
- f9-29 as rewritten passes pre-flight (`softfield check-tickets` on it)
- the listed `tests:` pass
- all gates pass (see `docs/workflow.md`)
