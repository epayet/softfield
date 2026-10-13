---
id: f108-01-desk-says-when
milestone: f108-in-your-answers-wanted-i-see
difficulty: 2
depends_on: [f75-01-archiving-on-approval, f51-01-desk-counts-what-waits-on-you]
files:
  - factory_dashboard/planning.py
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
On the owner's desk, a proposal's box says when the lead proposed it and a card to sign off says when it was reviewed, as a thread's box already says when the lead replied.

### Context
Read `docs/milestones/f108-in-your-answers-wanted-i-see.md` (D1–D5), then `_answers_wanted` (the example to follow: its `ago(now - _when(...))` line), `_open_proposals`, `_ripe` and `desk` in `factory_dashboard/planning.py`.
- `_open_proposals` takes `now`; `desk` passes it. `since` is already the time of the lead's reply that lists the proposal. An open proposal's words end with ` · proposed {ago} ago`: "5 key points · proposed 3 min ago", "merge F12 into F10 · 2 key points · proposed 2 h ago", and "plan · proposed 3 min ago" when it has no key points.
- A proposal on its way keeps `_NEXT_PICK` alone, with no time (D3).
- `_ripe`: the review's end is the latest `ended` of the milestone's jobs in the `jobs` table whose `role` is `review` and whose `outcome` isn't `running` (`jobs.milestone_id` is the `milestones` row's `id`). With one, the words are "reviewed {ago} ago · waits for your sign-off"; with none, they stay "reviewed · waits for your sign-off" (D4).
- Tests: follow the tests about the desk's proposals and its ripe card in `tests/factory_dashboard/test_planning.py`, with a fixed `now`.
- **Change only these two functions' words and `desk`'s call: no template, no `DeskItem` field, no other group.**

### Done when
- an open proposal listed in a lead reply stored 3 minutes before `now`: its desk item's words end with "· proposed 3 min ago", after its key points
- the same for a `merge` proposal, after its "merge … into …" words, and for a proposal with no key points, after its kind
- a later lead reply that lists the proposal again: the time is that later reply's
- a proposal with a pending approval: its words are "on its way · the runner applies it at its next pick", with no "proposed"
- a card to sign off whose `review` job ended 2 hours before `now`: "reviewed 2 h ago · waits for your sign-off"; with two finished review jobs, the later one's time
- a card to sign off with no finished `review` job: "reviewed · waits for your sign-off"
- the items' links, order, `on_its_way` and the Planning tab's count don't change
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
