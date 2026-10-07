---
id: f6-20-desk-coming
milestone: f6-planning-room
depends_on: []
difficulty: 3
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/planning.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
The owner's desk shows what they asked for and is on its way, as a "Coming" group with a dashed orange edge: a plant the runner hasn't done yet, and every thread waiting for the lead's reply, with when it is expected.

### Context
Read `desk`, `_seeds`, `_answers_wanted` and `_next_reply` in `factory_dashboard/planning.py`, and the groups loop in `factory_dashboard/templates/planning.html`. Follow `_seeds`: a function returning `DeskItem`s.
- The owner (2026-10-07): "whenever i plant something… i also want to see it on my desk so that i know that it's coming, perhaps orangely dotted"; and, after writing on F11: "i asked a question about test 1, and now it's gone?". F11's thread exists, but its last message is the owner's, so it is neither a seed nor an answer wanted.
- Write a new function `coming(conn, project, now) -> DeskGroup` (key `coming`, name "Coming", colour `--hazard`). Keep it out of `desk()`: `desk()`'s items are what waits for the owner, and the Overview's Needs you and the Planning tab's count read them, so "Coming" must not change either.
- Its items, in this order:
  - each `owner_requests` row with `kind = 'plant'` and `done IS NULL`: its value's `title`, the words "planting at the runner's next pick", no link (an empty string);
  - each thread with an open `plan_message` request (`done IS NULL`) or an open planner row (`metrics.open_jobs`, kind `planner`, subject starting `<card>#`): its title (`_thread_title`), the words "waiting for the lead · " followed by what `_next_reply` says, and the link `/planning/<card>`.
- In `factory_dashboard/templates/planning.html`, show the group first, only when it has items, with `border: 1px dashed var(--hazard)` (a `.desk-coming` rule in `factory_dashboard/static/dashboard.css`). The floor's dashed crates already mean "waits".

### Done when
- an open `plant` request shows in Coming with its title; once done, it doesn't
- a thread whose last message is the owner's, with an open planner row, shows in Coming with its link; once the lead's reply is stored, it is under "Your answers wanted" instead and not in Coming
- the Planning tab's count and the Overview's Needs you don't change when Coming has items
- assert within the group's element, on its text with tags stripped and entities unescaped (`_text` in `tests/factory_dashboard/test_planning.py`)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
