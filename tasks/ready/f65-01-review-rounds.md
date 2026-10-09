---
id: f65-01-review-rounds
milestone: f65-what-happens-if-i-comment-on
agent: lead
difficulty: 7
depends_on: []
files:
  - runner/requests.py
  - runner/milestone.py
  - runner/prompts.py
tests:
  - tests/runner/test_requests.py
  - tests/runner/test_milestone.py
---

### Goal
Approving follow-up tickets on a card that waits for sign-off starts a review round: the card leaves the desk, and once those tickets are done a review of the round's diff alone writes a "This round" section for the owner.

### Context
Read `docs/milestones/f65-what-happens-if-i-comment-on.md` (D1, D2, D5), then `_approve_plan` in `runner/requests.py`, `_reviewed`, `due_reviews`, `run_due_review`, `review_milestone`, `_record_review` and `SIGNOFF_SECTIONS` in `runner/milestone.py`, `REVIEW` in `runner/prompts.py`, and `_field` in `factory_dashboard/line.py` (ripe = tickets done and sheet stored).
- At approval, on a card with a stored sheet: clear `milestones.signoff`, drop the key from `state.review_counts` and `state.review_stop`, tag `<key>-round-<n>-start` (n = 2 for the first follow-up), and queue the follow-up tickets with `priority: 0`.
- `run_due_review` takes the latest round tag as its base when one exists, else `<key>-start` as today.
- The round's review prompt carries the owner's last message on the card's thread (`metrics.planner_messages`) and asks for a `## This round` section at the top of the report, with the previous one moved under `## Earlier rounds`. `SIGNOFF_SECTIONS` reads `This round` as `round`, and `_record_review` stores beside it `round_no` (n) and `asked` (that message's text), for the card's page (f65-03).

### Done when
- approving a plan on a card with a sheet clears the sheet, resets its review rounds and stop, tags the round, and its tickets are queued with priority 0
- approving a plan on a card without a sheet does none of that
- with the round's tickets done, `due_reviews` lists the card, and its review's base is the round tag
- the round's review prompt holds the owner's last message and asks for `## This round`
- `signoff_sections` returns `round` from a report with `## This round`, and the stored sheet has `round_no` and `asked`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
