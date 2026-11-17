---
id: f261-02-thread-review-short-plate
milestone: f261-the-review-notes-on-the-planning
difficulty: 3
depends_on: [f261-01-review-writes-in-short, f216-03-review-page-plates-and-folds]
agent: developer
files:
  - factory_dashboard/thread.py
  - factory_dashboard/templates/thread.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_thread.py
---

### Goal
A card's thread shows its review as one short plate, with How to test folded and a link to the whole review, so the conversation starts high on a phone.

### Context
Read `.softfield/cards/f261-the-review-notes-on-the-planning.md` (D2, D3, D4) and build Proposed in `.softfield/cards/f261-mockup/thread-review.html`. Its dashed outlines and green notes belong to the mock-up, not the page.
- `_review` and `Review` in `factory_dashboard/thread.py`: today they pass `_SHEET`'s sections as a list. Pass the parts D2 names instead: `in_short` (or D3's first sentence of `changed`), `decisions` when it doesn't start "none", the tally and the Your check / Not yet lines from `done_check`, `how_to_test` with its step count, and the gist for the whole review's link.
- `factory_dashboard/templates/thread.html`, the `{% if review %}` section: the order in D2. In short uses the `.in-short` plate the lead's messages use in the same template; the folds follow `#note`'s `<details>` with `summary.fold`. Keep the ids `review`, `signoff-button`, `signing-off` and `signoff-status`, and Sign off's on-its-way behaviour as it is.
- `factory_dashboard/static/dashboard.css`: the tally, the check lines and the link plate under `.thread-page #review`, from the existing tokens only, no status colour.

### Done when
- a sheet with `in_short` shows it in the In short plate; a sheet without it shows the first sentence of What changed there
- What changed is no longer on the thread; "The whole review ›" links to the card's page and its gist names what is there
- How to test is a closed fold whose summary says "n steps"; ideas from the review are a closed fold with their count, only when there are some
- a `decisions` starting "None" shows nothing; any other shows "Needs your answer" open, above In short
- a sheet with `done_check` shows the tally and only its Your check and Not yet lines; a sheet without it shows no tally
- Sign off, its on-its-way pill and a refused sign-off's words behave as before
- no horizontal scroll at 390 px
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
