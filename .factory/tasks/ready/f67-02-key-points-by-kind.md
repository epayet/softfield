---
id: f67-02-key-points-by-kind
agent: lead
milestone: f67-in-proposals-sometimes-i-see-d1
difficulty: 5
depends_on: [f67-01-key-point-kinds]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/proposal.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A proposal's review page draws each key point by its kind, information first, and lets the owner answer a choice by tapping an option.

### Context
Follow the mock-up, `.factory/cards/f67-mockup/review.html`, which the owner approved with this plan. Read `.factory/cards/f67-in-proposals-sometimes-i-see-d1.md` D2, D3 and D4, `factory_dashboard/templates/proposal.html` (the `#key-points` deck and its script) and, in `factory_dashboard/planning.py`, `proposal_review`.
- Order in `proposal_review`: `info`, then `attention`, then `choice`, each by `n`; a point without `kind` sorts and draws as today's box, with the `attention` ones.
- `info`: a plain numbered line in `--muted`, no box, with a small Comment… link. `attention`: a box with a `--hazard` left edge and "Needs a look"; with `flag`, also "Changes an earlier decision" (the ⚑ goes). `choice`: a box with an `--opus` left edge, "Your choice", and one button per option (44 px tall, wrapping at 390 px), the `pick` one pressed and marked "Lead's pick".
- A one-line key above the points says what each edge colour means.
- A choice off the lead's pick counts as a change in the page's script: it adds `"Chose: <label>"` to that point's comment in the send-back value (with any text the owner wrote after it), the count and the Send back button update as for a comment, and tapping the lead's pick again takes it away.
- **The choice's comment is built in the page's script, so the send-back request and the runner stay as they are.**

### Done when
- a proposal with all three kinds shows the information lines first, then the "Needs a look" boxes, then the choices, at 390 px and 1440 px
- the lead's pick is pressed on load and Approve shows; tapping another option shows "Send 1 change back", and sending posts `{"comments": {"<n>": "Chose: <label>"}}`; tapping the pick again brings Approve back
- a flagged point says "Changes an earlier decision" in words; no ⚑ shows
- a proposal whose key points have no `kind` shows as today
- the layout check passes at 390 px
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
