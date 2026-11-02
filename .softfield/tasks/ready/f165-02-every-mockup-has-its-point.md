---
id: f165-02-every-mockup-has-its-point
milestone: f165-there-s-been-a-few-conversations
agent: lead
difficulty: 3
depends_on: [f152-02-every-mockup-is-listed]
files:
  - runner/planner.py
  - runner/loop.py
tests:
  - tests/runner/test_planner.py
---

### Goal
A card's mock-ups never drop out of its thread's list: when a planner reply lists proposals, every mock-up on the card's plan branch that the list doesn't name is listed by the runner too, whether or not this job changed it.

(The file name is from the card's first draft; a planner job can't rename a file. The goal above is the ticket.)

### Context
Read `.softfield/cards/f165-there-s-been-a-few-conversations.md` (D2).
- f152-02-every-mockup-is-listed added, in `runner/planner.py`, the function that appends a `mockup` proposal for each mock-up file the job's drafts commit added or changed and the reply didn't name, and its call in the planner job in `runner/loop.py`. Read both as built, and its tests in `tests/runner/test_planner.py`.
- The gap it leaves: a mock-up listed on an earlier turn, unchanged since, that a newer non-empty list forgets. The thread page and the review tabs read only the latest list, so the mock-up vanishes from both.
- Widen the paths it is given: the `.html` files under `.softfield/cards/<card>-mockup/` that differ between main and `plan/<card>` (`git diff --name-only` of main against the branch after the drafts commit); a file removed on the branch is left out. Apply it when the reply lists at least one proposal, or when this job added or changed a mock-up (as f152-02 does). A reply that lists nothing and changed no mock-up stays as it is: the last list stands (f51-03).
- Same proposal shape as f152-02's (`id` `<file stem>-mockup`, `title` from the file's `<title>`, the "Listed by the runner" key point).

### Done when
- turn 1 lists `plan` and a mock-up `a.html`; turn 2 changes only the plan and lists only `plan`: the stored turn-2 list ends with a `mockup` proposal for `a.html`
- a reply with no proposals that changed no mock-up stays with no proposals
- a mock-up already named, one on main and unchanged on the branch, or one removed on the branch is not listed
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
