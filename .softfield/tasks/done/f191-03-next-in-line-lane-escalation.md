---
id: f191-03-next-in-line-lane-escalation
milestone: f191-why-is-the-lead-reviewing-something
difficulty: 3
depends_on: [f191-02-escalated-ticket-keeps-the-lane]
files:
  - factory_dashboard/overview.py
  - tests/factory_dashboard/test_overview.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview's Next in line shows a queued escalation or direction of a fast-lane card's ticket in the Fast lane bay, even when its ticket has left `.softfield/tasks/ready/`.

### Context
Read D3 in `.softfield/cards/f191-why-is-the-lead-reviewing-something.md`. The bay's picture is `.softfield/cards/f172-mockup/goes-first.html`; nothing new is drawn.
In `factory_dashboard/overview.py`: `_live_context` builds `lane_ids` from the lane's ticket rows only, then passes them to `queued_jobs` as `first`; `fast_lane` splits the ticket rows. An escalated ticket has no ticket row, so its escalation misses the bay.
A ticket id starts with its card's short key (`f172-06-…` for F172); `short_key` gives a card's.
`_live_context` gives `fast_lane` a card on its way in and not one on its way out (F192 D4): match against those same keys.
Tests to follow: `test_a_direction_for_a_fast_lane_ticket_shows_in_the_bay_before_its_tickets` in `tests/factory_dashboard/test_overview.py`.

### Done when
- An open escalation row for `f172-06-…`, with F172 in the fast lane and no ready F172 ticket, shows in the Fast lane bay, above the planner jobs.
- The same row with F172 out of the lane shows where it does today.
- A direction for a ready lane ticket still shows in the bay before its ticket (the existing test passes unchanged).

```yaml
# --- runner ---
result: done
attempts: 2
duration_s: 6002
gate_failures: ['stopped']
tokens: 8502352
```
