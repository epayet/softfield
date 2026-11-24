---
id: f286-02-code-lines-in-review-numbers
milestone: f286-i-want-code-reviews-to-highlight
difficulty: 4
depends_on: []
agent: lead
files:
  - runner/report.py
  - runner/gitops.py
  - tests/runner/test_report.py
tests:
  - tests/runner/test_report.py
---

### Goal
`softfield report <key>` shows how much code a milestone added and removed, and the Trends table shows the net for every milestone, so a review's numbers say whether the code grew or shrank (ADR 52 item 4).

### Context
Read `.softfield/adr/52-a-review-leaves-the-code-simpler.md` (item 4) and `.softfield/cards/f286-i-want-code-reviews-to-highlight.md` (D4). Write the tests first.
- The milestone's merged tickets and their squash commits are in the metrics database, `tickets."commit"` (written in `runner/loop.py` beside `lines_changed`).
- Follow `Git.commit_size` in `runner/gitops.py` (`git show --numstat`): add a sibling that returns added and removed lines for one commit, leaving out paths under `tests/`, `docs/` and `.softfield/` and any `*.md`.
- `milestone_report` in `runner/report.py` today takes only the database; `write_milestone_report` has the repo. Pass what it needs; a commit git no longer has counts as nothing.

### Done when
- for a milestone whose two merged tickets changed `runner/x.py` (+30 −10), `tests/runner/test_x.py` (+50) and `docs/x.md` (+5), the results table has a row `| Code lines | +30 −10 (net +20) |`
- the Trends table has a "Net code lines" column, one value per milestone, and the **All** row sums them
- a ticket whose commit is missing from the repo, or that has no commit, adds nothing and raises nothing
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
