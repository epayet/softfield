---
id: f86-01-owner-time-numbers
milestone: f86-idea-tracking-time-the-human-spent
difficulty: 4
depends_on: [f59-01-reports-week-numbers]
files:
  - factory_dashboard/reports.py
  - tests/factory_dashboard/test_reports.py
tests:
  - tests/factory_dashboard/test_reports.py
---

### Goal
The week's numbers in `factory_dashboard/reports.py` also say how much of the owner's time the factory took: hours on the dashboard, by card, and how long things waited for them, with the week before.

### Context
Read `.factory/cards/f86-idea-tracking-time-the-human-spent.md` (D1 to D5) and follow `week` and `series` in `factory_dashboard/reports.py` (f59-01): the same projects list, the same weeks, the same dataclass style.
- The owner's actions are the rows of `owner_requests` (`kind`, `subject`, `project_id`, `created`); waits are `owner_items` (`created`, `resolved`).
- `created` carries its offset and the offsets differ between rows: order and subtract as datetimes, never as text (the card's "What we know" says what text order did).
- Sittings are found over every project's actions together, then each action's minutes are counted for its own project, so a sitting that switches project splits between them.
- Tests build their database as `tests/factory_dashboard/test_reports.py` already does.

### Done when
- three actions at 10:00, 10:12 and 11:00 give 5 + 12 + 5 = 22 minutes and two sittings
- actions stored as `2026-10-20T10:00:00+01:00` and `2026-10-20T09:10:00+00:00` are 10 minutes apart, in that order
- `by_card` puts `f158-milestones-don-t` under `f158` with that card's title, a `plant` under "Planting", a `pause` or a `reserve` on `five_hour` under "Steering the line", most minutes first
- an `f1` on two projects gives two cards, each with its project
- for one project, only its own actions and items count; for two, both
- `waited_hours` is the median over the items resolved in the week; a week with none gives None, not 0
- `Week` has `owner`, with the week before's hours and wait; `series` gives `owner.hours` for every week, None for weeks before the first `owner_requests` row
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
