---
id: f6-17-drop-seed
milestone: f6-planning-room
depends_on: [f6-14-talk-while-paused]
agent: lead
difficulty: 4
files:
  - runner/requests.py
  - runner/loop.py
  - runner/metrics.py
  - factory_dashboard/requests.py
  - factory_dashboard/templates/thread.html
  - docs/milestones/f6-planning-room.md
tests:
  - tests/runner/test_requests.py
  - tests/runner/test_loop.py
  - tests/factory_dashboard/test_planning.py
---

### Goal
The owner can remove a seed they no longer want from its card's page, and a card or ticket whose file is gone leaves the dashboard.

### Context
Read F6's D1 table and D4's merges in `docs/milestones/f6-planning-room.md`, `KINDS` and the `plant` and merge handling in `runner/requests.py`, `KINDS` in `factory_dashboard/requests.py` (protected: the dashboard's one write), `sync_cards` and `sync_tickets` in `runner/loop.py`, and `upsert_milestone` and `remove_missing_tickets` in `runner/metrics.py`.
- The owner (2026-10-07): "i need a way to delete a seed. i planted a test and want to get rid of it". The lead removed F12 by hand that day (`git rm` and its `milestones` row deleted).
- **A new kind, `drop_seed`:** subject the card's short key (`f11`), no value. Refused, with its reason and main unchanged, when the card isn't an idea (`**State:** idea`) or any ticket in `tasks/` names its milestone. Otherwise one commit `F11 removed by the owner` `git rm`s its doc; its thread (if any) gets a lead message "Removed by the owner on <date>.", its open planner rows close, and its `planning` owner item resolves. Result: `removed docs/milestones/f11-test.md`.
- **The button:** on a seed's thread page (`/planning/<card>` for an idea card), a "Remove seed" button with a confirm step ("Remove F11? Its notes go too.").
- **Leftovers, found 2026-10-07:** `sync_cards` only upserts, so a card whose doc is gone (an f6-12 merge, a `git rm`) stays a seed on the desk; and `remove_missing_tickets` marks only `ready` rows, so a deleted ticket's `blocked` row (f4-21's, cleared by hand on 2026-10-07) kept "1 blocked now" on the Overview. Both now drop what no file in `docs/milestones/` or `tasks/` names: a card leaves the board (a `removed` state, or delete the row when nothing references it; pick one and say which in D1), and any ticket row whose file is in no `tasks/` folder is `removed`.
- Update F6's D1 table with the new kind.

### Done when
- a `drop_seed` for an idea card with no tickets removes its doc in one commit, posts the lead message on its thread and closes its planner rows; for a building card, or one with a ticket, it is refused and main is unchanged
- after a merge or a `drop_seed`, the card is gone from the desk's seeds; a `blocked` ticket row whose file was deleted no longer counts as blocked
- the dashboard posts `drop_seed` from the button, and refuses an unknown kind as before
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
