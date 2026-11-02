---
id: f95-01-sign-offs-counted-once
milestone: f95-overview-currently-says-i-have-2
priority: 1
depends_on: [f110-01-ripe-is-one-rule]
difficulty: 3
files:
  - factory_dashboard/overview.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview's Needs you shows a milestone waiting for sign-off once, through the desk's entry, so it never counts more sign-offs than the desk lists.

### Context
Read `factory_dashboard/overview.py` (`needs_you`, `_live_context`) and `factory_dashboard/templates/_partials/needs_you.html`. Follow the worked example in `tests/factory_dashboard/test_overview.py`: `test_a_lead_reply_shows_once_in_the_desk_entry`.
- Needs you draws two things about a sign-off today: the desk's entry ("N things wait for you on your desk", which counts the desk's "Finished, to talk through" items) and one row per open `owner_items` row of kind `signoff`, which the runner stored at the milestone's verdict.
- The stored row can outlive the desk's item (the milestone got new tickets after its verdict, or has no review sheet), so the Overview showed two sign-offs while the desk listed one (F95).
- `_live_context` already leaves the `planning` items out of `needs` because the desk's entry stands for them (f6-09). Do the same for `signoff`: the desk is the one place a sign-off shows.
- It waits for f110-01: until the desk lists a reviewed card whose only unfinished tickets are set aside (F31, 2026-10-13), dropping the stored row would leave that sign-off on neither page.
- Leave `notify` as it is (built from every open item), and leave `needs_you` itself and the runner alone.

### Done when
- with an open `signoff` owner item for a milestone that is on the desk's "Finished, to talk through", `/live` shows the desk's entry and no separate `signoff` row
- with an open `signoff` owner item for a milestone that is not on the desk (it has a ready ticket), `/live` shows no `signoff` row
- items of other kinds (`adr`, `blocked`, `reserve`) still show, each with its command
- `data-needs` on `#live-facts` still carries the `signoff` item
- the listed tests pass, and fail without the change

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 4625
gate_failures: []
tokens: 2667375
```
