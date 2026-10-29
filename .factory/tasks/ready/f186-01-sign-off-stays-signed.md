---
id: f186-01-sign-off-stays-signed
milestone: f186-why-can-t-i-sign-off
agent: lead
difficulty: 3
depends_on: []
files:
  - runner/owner.py
  - runner/cli.py
  - runner/requests.py
tests:
  - tests/runner/test_owner.py
  - tests/runner/test_cli.py
  - tests/runner/test_requests.py
---

### Goal
A milestone the owner signed off stays signed off: a review ending after the sign-off doesn't reopen it, a second sign-off settles instead of failing, and an item already reopened (F142's) is cleared by the runner on its own.

### Context
Read `.factory/cards/f186-why-can-t-i-sign-off.md`: "What happens today" tells what happened to F142, and D1–D3 are what this ticket builds.
- `runner/cli.py`: `_review` runs `owner.verdict` after `run_due_review` with no check that the milestone is still unsigned. `runner/milestone.py`: `signed_off` is the check to use (doc "Status: done", or the `<key>-done` tag); `_record_review` sets status `review`.
- `runner/owner.py`: `signoff` commits, then tags, then calls `_signed_off`; `verdict` appends the `signoff` `OwnerItem`; `_MILESTONE_KINDS` and `_resolve` pick the items about a milestone.
- `runner/metrics.py`: `upsert_owner_item` reopens a resolved item (`resolved = NULL`), which is why a late verdict brings the sign-off back.
- `runner/requests.py`: `apply_requests` applies the owner's requests before each pick (the sign-off request calls `owner.signoff`, near `_apply`). D3's heal goes there, once per call, for the project's own database.
- Today item 250 (`signoff`, `f142-why-am-i-not-getting-notifications`, project softfield) is open and that milestone's status is `review`, though its card says done and its tag exists.

### Done when
- after a review stops on a milestone that is signed off, `_review` records no verdict, writes no session "Verdict", leaves the milestone's status as it is, and opens no owner item (D1)
- `owner.signoff` on a milestone already signed off (doc done and tag there) raises nothing, makes no commit and no tag, leaves the doc's date, and resolves its `signoff` and `review-stop` items and sets the milestone done (D2)
- `apply_requests` resolves an open `signoff` or `review-stop` item whose milestone is signed off and sets that milestone's status to done; an item whose milestone isn't signed off stays open (D3)
- a first sign-off works as before: doc, review, commit, tag, item resolved
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
