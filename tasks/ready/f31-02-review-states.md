---
id: f31-02-review-states
milestone: f31-when-i-click-on-approve-plan
difficulty: 5
depends_on: [f31-01-settle-and-reject, f6-24-plan-shows-tickets]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/proposal.html
  - factory_dashboard/templates/thread.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A proposal's review page and its card on the thread say where it stands, offer their buttons only while it's open, and each button can be pressed only once; the review page gets Reject.

### Context
Read `docs/milestones/f31-when-i-click-on-approve-plan.md` D3 and D8. In `factory_dashboard/planning.py`: `proposal_review`, `_proposals`, `_plan_changes` and `_KIND_COLOR`; `runner.planner.proposal_state` (f31-01) gives the state and `runner.metrics.latest_proposals` the thread's latest set (a proposal outside it is `replaced`). Templates: `factory_dashboard/templates/proposal.html` (the dock's `#primary`, `#send-back`, the Comment… buttons, "What happens next", f6-24's `#plan-changes`) and `factory_dashboard/templates/thread.html` (the `.proposal` cards, today "open" or "answered").
- The request's status partial is `factory_dashboard/templates/_partials/request.html` (it polls until the runner is done).
- Example to follow for re-fetching after a post: the thread's Send in `factory_dashboard/templates/thread.html` (`#conversation`, f6-21) and F13's `#plant-row` (`hx-select`).
- Reject posts `{"kind": "reject", "subject": "<thread>/<id>"}`, after a confirm step as "Remove seed" has on `factory_dashboard/templates/thread.html` ("Won't do: the drafts go, and a card with no tickets is removed").
- f6-24's rows: show each ticket's `agent` (lead, or developer when absent) and `difficulty` from its frontmatter beside its word, and colour the word: added `--good`, changed `--a7`, set aside and removed `--muted`.
- **Every state in plain words (owner.md): "open", "on its way", "approved", "rejected", "sent back", "replaced by a newer reply".**

### Done when
- an open proposal shows its buttons and Reject; pressing Approve plan replaces the dock at once with the dashed orange "on its way" box and the request's status, and a reload shows the same box, with no button
- an approved one shows "approved" and the runner's result, a rejected one "rejected", a sent-back one "sent back", with no buttons and no Comment…
- a proposal from an older reply shows "replaced by a newer reply", with no buttons
- a refused approval shows its result and the buttons again
- each card on the thread shows the same word as its review page
- f6-24's rows show "lead" or "developer" and the difficulty, the word coloured
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
