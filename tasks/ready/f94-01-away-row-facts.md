---
id: f94-01-away-row-facts
milestone: f94-opus-f9-25-seeds-and-planting
depends_on: []
difficulty: 3
files:
  - factory_dashboard/queries.py
  - factory_dashboard/templates/_partials/away.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
Each ticket's row under "While you were away" says who did it once, then how it went, when it finished and how long it took on its first line, and the title always on a second line.

### Context
Read F94's Decisions D1–D4 in `docs/milestones/f94-opus-f9-25-seeds-and-planting.md` and its picture, `docs/milestones/f94-mockup/away-rows.html` (the Proposed side). Then `away` and `AwayTicket` in `factory_dashboard/queries.py`, `factory_dashboard/templates/_partials/away.html`, `.steps .what` in `factory_dashboard/static/dashboard.css`, and the away tests in `tests/factory_dashboard/test_overview.py`.
- `label` loses the name and the " · " before it: "finished after 3 developer attempts", "lead ticket", "1st try", "2 attempts"; still empty with no `merged_by`. The tests that expect "Opus · …" in `label` or in the page change with it.
- `AwayTicket` gains `finished` (a datetime: the `at` that `away` already sorts by) and `took` (a timedelta: from the earliest `started` among the ticket's jobs to `finished`).
- The page writes "finished 10:32" in local time (`.astimezone()`), or "finished 9 Oct 23:05" when that day isn't `now`'s; and "took " with the `ago` filter of `factory_dashboard/app.py` ("took 58 min").
- The first line's facts are joined by " · " in one element, `class="how"`; the title is in its own, `class="title"`, which takes a whole row of `.steps .what` (`flex-basis: 100%`). Scope both rules to `#away`, and use the colour tokens, no raw colour.
- **Change only these rows: the summary line above them and the "Nothing happened" line stay as they are.**

### Done when
- a developer ticket merged by `claude-opus` after 3 developer jobs has the label "finished after 3 developer attempts", and "Opus" appears once in its row on the page
- a ticket whose first job started at 08:00 and whose last job ended at 08:20 the same day as `now` shows "finished 08:20" and "took 20 min"; one that finished the day before `now` shows the day and the month before the time
- a ticket with no `merged_by` shows no name and no label, but its "finished" and "took"
- in the page, each row's `class="how"` element comes before its `class="title"` element, and the title's text is inside `class="title"` only
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
