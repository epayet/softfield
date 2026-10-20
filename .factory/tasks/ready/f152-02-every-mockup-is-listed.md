---
id: f152-02-every-mockup-is-listed
milestone: f152-when-a-ticket-is-on-the
agent: lead
difficulty: 4
depends_on: []
files:
  - runner/planner.py
  - runner/loop.py
tests:
  - tests/runner/test_planner.py
---

### Goal
A mock-up a planner job draws always reaches the owner: when the reply lists no `mockup` proposal for a mock-up file the job added or changed, the runner lists one itself.

### Context
F152's first reply drew `.factory/cards/f152-mockup/review-note.html` but listed only a `plan` proposal whose `path` was the card's doc. The proposal page shows a mock-up only from a proposal whose `path` is a mock-up file (`_MOCKUP_RE` in `factory_dashboard/planning.py`), so the owner saw none.
- Read `runner/planner.py` (`parse_reply`, `Reply`, `_checked`, `_proposal`) and, in `runner/loop.py`, the planner job that calls `_commit_drafts` and then `planner.parse_reply`.
- Add a function to `runner/planner.py` that takes the `Reply` and the paths of the mock-up files the job's drafts commit added or changed (under `.factory/cards/<card>-mockup/`, `.html` only). It returns the `Reply` with one `mockup` proposal appended for each path that no proposal names as its `path`: `id` `<file stem>-mockup`, `title` the file's `<title>` text (the file name when it has none), `path` the file, one key point titled "Listed by the runner" whose text is "The lead drew this mock-up without listing it." A reply with no block (all text) gets them too.
- In the planner job, call it after `parse_reply` with the paths from the drafts commit (`git diff --name-only` of that commit; none when nothing was committed).

### Done when
- a reply that lists a `plan` only, after a job that added `.factory/cards/f9-mockup/a.html`, ends with a `mockup` proposal whose `path` is that file and whose title is the file's `<title>`
- a mock-up already named by a proposal's `path` is not listed twice
- a changed mock-up file is listed like an added one; a removed one, a `.css` beside it, or a file outside `-mockup/` is not
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
