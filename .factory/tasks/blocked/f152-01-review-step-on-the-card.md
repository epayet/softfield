---
id: f152-01-review-step-on-the-card
milestone: f152-when-a-ticket-is-on-the
difficulty: 4
depends_on: []
files:
  - factory_dashboard/board.py
  - factory_dashboard/templates/board.html
  - factory_dashboard/templates/milestone.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_board.py
  - tests/factory_dashboard/test_milestones.py
---

### Goal
A growing card whose tickets are all done says which step its review is at (next, running or stopped), on the board and on its page, and a set-aside count says "won't run".

### Context
Read `.factory/cards/f152-when-a-ticket-is-on-the.md` (D1–D3) and the mock-up to build, `.factory/cards/f152-mockup/review-note.html` (Proposed).
- In `factory_dashboard/board.py`: `Card`, `_milestone_stage`, `_card_note` and `_cards`, which already reads the live jobs with `running_jobs` (`factory_dashboard/overview.py`, class `Running`: its `role`, `agent` and `milestone`, the full key).
- A stopped review is a row of the `owner_items` table with `kind = 'review-stop'`, `subject` the milestone's full key, `text` the runner's reason, and `resolved` NULL while it stands. Read them in `_cards` with one query, as it reads the threads.
- Add a field to `Card` for the step: its label ("Review running", "Review stopped", "Review next") and its words, from D2; empty on every other card (another stage, a ticket not done, a bug).
- `factory_dashboard/templates/board.html`, macro `card_link`: the step goes under the count, in a new `card-review` element styled as the mock-up's (`factory_dashboard/static/dashboard.css`, beside `.card-note`, with the existing tokens only). The set-aside count reads "N set aside, won't run".
- `factory_dashboard/templates/milestone.html`: the Stage line adds "· " and the step in lower case after "Growing: in the factory"; its Tickets line says "won't run" as the board does.
- The tests to follow: `test_every_ticket_done_is_growing_until_the_sheet_is_stored_then_ripe_then_harvested` (its F25 is a growing card with every ticket done) and `test_a_planted_card_says_what_it_waits_for` in `tests/factory_dashboard/test_board.py`.
- Change nothing in `runner/`: the dashboard only reads.

### Done when
- F25 with no review job and no stop says "Review next" and "Claude reviews it before the next ticket · then it's yours to sign off"
- with a live `review` job on F25 by `claude-opus`, it says "Review running" and "claude-opus reads the work · then it's yours to sign off"; a live job of another role says "Review next"
- with an unresolved `review-stop` item on F25 whose text is "end-to-end tests fail on staging", it says "Review stopped" and "end-to-end tests fail on staging · shown under Needs you"; once the item is resolved, "Review next"
- a growing card with a ticket not done, a ripe card and a bug have no step
- the board page shows the step inside F25's card, and F25's page shows it on its Stage line
- a card with one set-aside ticket reads "1 set aside, won't run" on the board and on its page
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: all-tests)
attempts: 3
tokens: 11934749
logs: .factory/var/runs/20261021-090717/f152-01-review-step-on-the-card
```

```yaml
# --- runner ---
result: blocked
reason: the finished work failed check-all; its work is on task/f152-01-review-step-on-the-card
```
