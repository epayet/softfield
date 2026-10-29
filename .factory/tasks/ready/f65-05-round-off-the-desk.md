---
id: f65-05-round-off-the-desk
milestone: f65-what-happens-if-i-comment-on
difficulty: 5
depends_on: [f65-04-drop-a-round]
files:
  - factory_dashboard/line.py
  - factory_dashboard/coming.py
  - factory_dashboard/planning.py
  - factory_dashboard/thread.py
  - factory_dashboard/templates/thread.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_line.py
  - tests/factory_dashboard/test_thread.py
---

### Goal
A card with more work approved leaves To sign off the moment the owner presses Approve, and its page says so in place of Sign off, with Drop this round to bring it back.

### Context
Read `.factory/cards/f65-what-happens-if-i-comment-on.md` (D6, D7) and the picture to build, `.factory/cards/f65-mockup/round-gap.html` (Proposed). Then `_field` in `factory_dashboard/line.py`, `_ripe` and `desk` in `factory_dashboard/planning.py`, `_acted_on` in `factory_dashboard/coming.py` (the example: a request still waiting shows on its way), `class Review` and `_review` in `factory_dashboard/thread.py`, and the `#review` section of `factory_dashboard/templates/thread.html`.
- A card is in a round when an `approve_plan` request for its thread is not done yet, or when it has a review stored and tickets ready or running, or a `review` job open for it (`open_jobs` in `runner/metrics.py`).
- A card in a round is not ripe: not in To sign off, not on the floor's Ripe.
- Its page keeps the review, and shows the plate where Sign off was: "More work approved", its tickets each a link (none listed yet while the approval waits: "queued at the runner's next pick"), "Comes back to To sign off once it's built and reviewed", a strip of four steps (Approved, Building, Review, Back for sign-off) with the current one lit, and Drop this round. Drop posts `set_aside` with the card's short key and the value `round` (f65-04); it shows on its way at once (the dashed `--hazard` edge of `.thread-page .pill.asked`, "Dropping this round at the runner's next pick") and the button goes.
- New colours or shapes join the tokens at the top of `factory_dashboard/static/dashboard.css` first.

### Done when
- with an `approve_plan` waiting for a ripe card, the desk's To sign off doesn't list it and its page shows the plate with "queued at the runner's next pick"
- with its tickets ready, the plate lists them, each a link; with a review open for it, it isn't ripe
- with every ticket done and no review open, it is ripe and Sign off shows as today
- pressing Drop this round shows "dropping at the runner's next pick" with the dashed edge at once, and posts one `set_aside` with the value `round`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
