---
id: f86-03-report-reads-your-time
milestone: f86-idea-tracking-time-the-human-spent
difficulty: 3
depends_on: [f86-01-owner-time-numbers, f59-03-weekly-report-job]
agent: lead
files:
  - runner/prompts.py
  - tests/runner/test_prompts.py
tests:
  - tests/runner/test_prompts.py
---

### Goal
The weekly report's brief carries the owner's time, and asks the lead for a paragraph on where it went and, when it can, an idea that saves some.

### Context
Read `.factory/cards/f86-idea-tracking-time-the-human-spent.md` (D5, D7). Write the test first.
- `REPORT` in `runner/prompts.py` (f59-03) already carries `week`'s numbers for each scope as text; add `Week.owner` (the reports module, as f86-01 left it) to the same text: hours and the week before's, waited hours and items, the top cards with their minutes.
- The idea, when there is one, is a quoted line under "Ideas for the factory" or "Ideas for <project>", as F59 D7 says.

### Done when
- the brief for a week with owner actions has "Your time" with its hours, the week before's, the wait and the top cards, for each scope
- a week with no owner action says "no time recorded" rather than 0 h
- the brief asks for one paragraph on the owner's time and at most one idea for it, in the quoted form
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
