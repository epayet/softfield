---
id: f301-01-review-opens-on-what-changed
milestone: f301-the-what-it-s-about-section
difficulty: 3
depends_on: [f261-02-thread-review-short-plate]
agent: developer
files:
  - factory_dashboard/milestones.py
  - factory_dashboard/thread.py
  - factory_dashboard/templates/milestone.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_milestones.py
  - tests/factory_dashboard/test_thread.py
---

### Goal
A reviewed card's page opens on What changed: "What it's about" becomes Behind it's first fold, with the Done when tally as its gist, and a Done when line still "Not yet" heads What changed.

### Context
Read `.softfield/cards/f301-the-what-it-s-about-section.md` (D1–D4) and build Proposed in `.softfield/cards/f301-mockup/review-top.html`. Its dashed outlines and green notes belong to the mock-up, not the page.
- `factory_dashboard/templates/milestone.html`: the `#about` plate is drawn only when `sheet` is empty. With a sheet, its contents move into a `<details id="meant">` first inside `#behind`, built with the `summary` macro like the other folds. The Not yet block goes at the top of `#what-changed`'s body (D2). Remove `show_note` and its conditions: without a sheet the note shows in the plate as today; with one it shows only in "Your note and how it grew".
- The Done when tally: f261-02 counts `done_check`'s bullets by their first label for the thread. Put that function in `factory_dashboard/milestones.py` (move it there from `factory_dashboard/thread.py` if it is there) and use it from both pages. It returns the tally text and the Not yet lines; `gists()` in `milestones.py` gains the fold's gist from it.
- `factory_dashboard/static/dashboard.css`: `.not-yet` beside `.card-plate.asks`, from the existing tokens only (the hazard edge on `--plate`).

### Done when
- a card with a review sheet has no `#about` plate; `#what-changed` (or "Needs your answer" when there is one) comes first after the head
- Behind it's first fold is "What it was meant to do", closed, holding What it will do and Done when as of now (or the plan's Done when), its gist the tally, e.g. "Done when: 4 met · 2 your check"; a sheet without `done_check` shows the fold with no gist
- a `done_check` with `**Not yet:**` lines shows each at the top of What changed under "Not yet · from Done when"; one without shows no block; a sheet with Not yet lines and no `changed` still shows them
- a card with no review sheet shows "What it's about" exactly as before, the note included
- the thread's review tally from f261-02 reads the same as before
- no horizontal scroll at 390 px
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
