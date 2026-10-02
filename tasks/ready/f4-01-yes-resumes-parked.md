---
id: f4-01-yes-resumes-parked
milestone: f4-always-on
depends_on: []
agent: lead
difficulty: 4
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
After the owner answers yes to the 5-hour question, the escalations and checkpoints that were parked for it run before the lead ticket that asked.

### Context
Read `runner/loop.py`: `at_five_hour`, `_ask_five_hour`, `_five_hour_granted`, `run_task` (the `at_reserve(s, task) or at_five_hour(s, task)` branch), `_resume_support` and `work_queue`. Test-first.
- **What happened in F2 (2026-10-02, 12:01):** f2-06's escalation was parked at 78% of the window. The question came on lead ticket f2-03, and the owner said y. `_five_hour_granted` set `RETRY` on the parked escalation, but `at_five_hour` returned False and `run_task` ran f2-03 first (10 min). The escalation only ran at 12:17, on the next pass of `work_queue`.
- **The wanted order** after a yes: parked support work whose `RETRY` is set (`_resume_support`), then the ticket that asked, on the next pick. Don't park that ticket or count it as an attempt: it simply goes back to `ready/` for the next pass. When nothing was parked, the ticket goes on at once, as today (`test_a_yes_to_the_5_hour_question_lets_the_lead_ticket_go_at_once` stays green).

### Done when
- a yes with a parked escalation runs the escalation's job before the asking ticket's job
- a yes with nothing parked runs the asking ticket at once
- the asking ticket gets no extra attempt, park or Needs-you item from waiting its turn
- `uv run runner check-all --task f4-01-yes-resumes-parked` passes
