---
id: f172-01-marked-cards-pass-the-reserve
milestone: f172-i-d-like-to-be-able
agent: lead
difficulty: 5
depends_on: []
files:
  - runner/milestone.py
  - runner/loop.py
tests:
  - tests/runner/test_milestone.py
  - tests/runner/test_loop.py
---

### Goal
Past Claude's week mark or the owner's 25% of the 5-hour window, with the switches off, the lead tickets of a card whose header says `**Reserve:** yes`, and the ready tickets they wait for, run instead of parking; every other lead ticket parks as today.

### Context
Read ADR 34 in `.softfield/adr/34-a-card-may-use-the-reserve.md` (it must be Accepted) and D1, D3 and D5 in `.softfield/cards/f172-i-d-like-to-be-able.md`. Then `card` and `Card` in `runner/milestone.py`, and in `runner/loop.py`: `at_reserve`, `_at_the_reserve`, `at_five_hour`, `_at_five_hour`, `_waits_for_the_owner`, `_next_task` and `_cards`; and `signoff` in `runner/owner.py` for D5.
- `Card.reserve` is True only for a header with `**Reserve:** yes`; anything else, or no field, is False.
- `reserve_cards(repo, ready)` (D3) is a plain function: time and git stay out of it. Dependencies are followed through the ready tickets only; a dependency already done adds nothing.
- `_waits_for_the_owner` today answers for Claude as a whole; it needs the ticket it is asked about, so that `_next_task` prefers developer tickets, then marked ones, before a lead ticket that would park.
- Both reserves count (ADR 34 item 5): a ticket in the set passes `at_reserve` and `at_five_hour` alike. A real limit (a window used up, a job parked for a reset, a refusal resting a window) still holds it.
- `signoff` drops a `**Reserve:**` field from the header it rewrites (D5).

### Done when
- `milestone.card` reads `**Reserve:** yes` as `reserve=True`, and a header without it as False
- with the week past its mark and the switch off, a lead ticket of a marked card doesn't park, and a lead ticket of an unmarked card does, as today
- a lead ticket of an unmarked card that a marked card's ticket waits for (directly or through another) doesn't park either
- at the reserve, `_next_task` takes a developer ticket first, then a marked card's lead ticket, before an unmarked lead ticket
- with the 5-hour window past the owner's 25% and its switch off, a marked card's lead ticket runs, and an unmarked one parks as today
- with Claude limited (a job parked for a reset ahead), a marked card's lead ticket waits like any other
- a card signed off has no `**Reserve:**` in its header
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
