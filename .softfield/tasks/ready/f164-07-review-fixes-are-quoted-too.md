---
id: f164-07-review-fixes-are-quoted-too
milestone: f164-i-like-reading-the-milestone-reviews
difficulty: 2
depends_on: [f164-01-reviews-quote-their-ideas, f164-03-idea-plates-with-plant]
agent: lead
files:
  - runner/prompts.py
  - docs/workflow.md
  - docs/how-it-works.md
  - runner/instructions/lead.md
  - .softfield/cards/bugs.md
  - .softfield/cards/f164-i-like-reading-the-milestone-reviews.md
tests:
  - tests/runner/test_prompts.py
---

### Goal
A review writes a small fix worth a run as a quoted line the owner can plant from its plate, and no longer sets a bug ticket aside on the board (ADR 43).

### Context
Read `.softfield/adr/43-the-owner-plants-a-reviews-fixes.md`. The plate and its buttons are F164's (`.softfield/cards/f164-i-like-reading-the-milestone-reviews.md`, D1, D2, D5); nothing changes on screen.
- `REVIEW` in `runner/prompts.py`: the `later:` route becomes ADR 43 items 1 and 2, with no ticket and no `softfield check-tickets`, and item 5's line that a security finding never takes it. Build on the "6. What next" sentence f164-01 wrote.
- `docs/workflow.md`: the Discoveries step (ADR 43 item 4), and the Nit and Re-review lines of "Milestone review loop". Its Report paragraph's "what was set aside" stays true of a `report` finding: reword it only if it names a bug ticket.
- `docs/how-it-works.md`: "nits become set-aside bug tickets".
- `runner/instructions/lead.md`, "Sign-off sheet", item 3 ("the bug tickets set aside") and item 6: the same rule, for the lead.
- `.softfield/cards/bugs.md`, "Where bugs come from": a review's finding is no longer one; a planted fix the lead writes as a bug ticket can be.
- F164's doc: add D7 saying a fix worth a run is a quoted line too (ADR 43), and this ticket under Tickets.
- `runner/review.py` doesn't change: the route stays `later`.

### Done when
- `REVIEW` tells the `later` route to write one quoted line under the right bullet of "6. What next", and no longer asks for a bug ticket or names `.softfield/tasks/later/` for it
- `REVIEW` says a security finding never takes the route `later`
- a test in `tests/runner/test_prompts.py` checks both
- `docs/workflow.md`, `docs/how-it-works.md`, `runner/instructions/lead.md` and `.softfield/cards/bugs.md` say the same, and none says a review sets a bug ticket aside
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
