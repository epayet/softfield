---
id: f133-04-area-retires-from-the-runner
milestone: f133-each-project-has-its-own-series
agent: lead
difficulty: 3
depends_on: [f133-01-cards-take-the-projects-series, f133-03-board-without-areas, f222-04-the-number-goes]
files:
  - runner/tasks.py
  - runner/milestone.py
  - runner/planner.py
  - runner/requests.py
  - runner/loop.py
  - runner/session.py
  - runner/setup.py
  - runner/prompts.py
  - runner/instructions/task-format.md
tests:
  - tests/runner/test_tasks.py
  - tests/runner/test_milestone.py
  - tests/runner/test_planner.py
  - tests/runner/test_requests.py
---

### Goal
The runner no longer reads, writes or asks for a card's or a bug's area: a new card's header has no `**Area:**` line and a bug passes pre-flight without `area:`.

### Context
Read D4 in `.softfield/cards/f133-each-project-has-its-own-series.md` (ADR 30 already turned ADR 19 2b's area into the project), then the places below as F222's ticket f222-04 left them (it took the priority out of the same headers and files):
- `runner/tasks.py`: `AREAS`, `ticket_area`, `AREA_MISSING` and its check, the `area` field of a task. Ready tickets carry `area: factory` today, and an unknown value must stop failing them too.
- `runner/milestone.py`: `_CARD_AREA_RE` and the `area` field of `Card`.
- `runner/planner.py`: `_area`, `planting`, `seed_area`, `seed_card` (its header).
- `runner/requests.py`: `_plant`, which compares and records the area; its guard that a title can't set the card keeps checking the state and `milestone_after`. Keep this file's own `_CARD_AREA_RE`: `_card_marked` still writes the fast lane after an old doc's Area.
- `runner/session.py`: `record_ticket` and the card sync (`sync_cards`) that pass `area=`, and `ticket_area`'s import.
- `runner/loop.py`: the fix ticket's `meta |= {"area": …}`.
- `runner/setup.py`: `publish_cards`.
- `runner/prompts.py`: the planner's words on a bug's frontmatter, which ask for `area:`.
- `runner/instructions/task-format.md`: the `area:` line, the milestone header's **Area:** and the bug rules.
The `area` columns stay in the database (no migration); nothing writes them. An old doc's `**Area:**` line, or a ticket's `area:`, is accepted and ignored. `planting` returns a title and thoughts; its callers follow. A plant's `area` stays ignored, never refused (D2). The review's and the reports' product and factory split stays (D6).

### Done when
- a planted card's doc header has no Area, and marking it fast lane still writes the mark in that header
- a bug ticket without `area:` passes pre-flight, and so does one with `area: product` or `area: other`
- no call in `runner/` passes `area=` to `metrics.upsert_milestone` or `metrics.upsert_ticket`
- `runner/instructions/task-format.md` and the planner's prompt no longer ask for an area
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
