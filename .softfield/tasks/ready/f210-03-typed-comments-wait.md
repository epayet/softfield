---
id: f210-03-typed-comments-wait
milestone: f210-bundle-a-card-s-conversation-with
difficulty: 3
depends_on: [f210-02-one-strip-of-steps]
files:
  - factory_dashboard/static/deck.js
  - factory_dashboard/templates/thread.html
  - factory_dashboard/templates/proposal.html
  - factory_dashboard/templates/_partials/card_steps.html
tests:
  - tests/factory_dashboard/test_thread.py
  - tests/factory_dashboard/test_proposal.py
---

### Goal
Comments typed on a card's conversation or proposal wait in that browser tab when the owner moves between its steps, and the strip of steps says which step holds some.

### Context
The picture to build: `.softfield/cards/f210-mockup/one-box.html` (Proposed, "2 comments not sent"). Read D5 in `.softfield/cards/f210-bundle-a-card-s-conversation-with.md`, `factory_dashboard/static/deck.js`, and the `textarea.comment` boxes and their scripts in `factory_dashboard/templates/thread.html` and `factory_dashboard/templates/proposal.html`. Both pages load `deck.js`.
- Keep them in `sessionStorage`, keyed by the page's path and the point's number. Only `textarea.comment`, not the reply box.
- On a page's load and after a swap of `#conversation`, each saved comment goes back in its box, its box open. On a proposal page, the box is `label.comment-box`, opened as `.change-btn` does, and the page's `update()` runs, so Send back shows.
- A successful Send or Send back removes that page's comments. A failed one keeps them.
- Each step whose path holds comments shows "N comment(s) not sent" in its small line, in `--hazard`.
- A thread's comments are tied to the lead's latest message. Store that message's id with them (a `data-` attribute on `#conversation`), and drop them when a newer reply has come: its points are others.

### Done when
- the browser test: type a comment on a thread's point, go to its mock-up, the strip's Conversation says "1 comment not sent"; come back, and the comment is in its box, open
- the same on a proposal page: its comment returns, Send back shows and Approve plan is hidden
- after a successful Send, the comment is gone from the box and the strip, on a reload too
- a comment stored for an older lead message doesn't come back
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
