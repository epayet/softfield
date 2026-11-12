---
id: f210-05-typed-comments-wait-for-real
milestone: f210-bundle-a-card-s-conversation-with
difficulty: 4
depends_on: [f210-03-typed-comments-wait]
files:
  - factory_dashboard/static/deck.js
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/thread.py
  - factory_dashboard/templates/thread.html
  - factory_dashboard/templates/proposal.html
  - factory_dashboard/templates/_partials/card_steps.html
tests:
  - tests/factory_dashboard/test_thread.py
  - tests/factory_dashboard/test_proposal.py
finding: f210-03-F1
---

### Goal
Make f210-03 work: comments typed on a thread or a proposal page wait in the tab across steps, come back in their open boxes, go after a successful send, and the strip says which step holds some.

### Context
f210-03 merged only `factory_dashboard/static/deck.js`, with no test. Read that file's `f210-03` block, `factory_dashboard/templates/_partials/card_steps.html`, the `textarea.comment` boxes and scripts in `factory_dashboard/templates/thread.html` and `factory_dashboard/templates/proposal.html`, and D5 in `.softfield/cards/f210-bundle-a-card-s-conversation-with.md`. The picture: `.softfield/cards/f210-mockup/one-box.html`. Facts about what is there now:
- `card_steps.html` has no `data-unsend`, no "not sent" text and no per-step path the script can read, so the strip shows nothing; the script's `#card-steps` `data-unsend` update does nothing visible.
- Nothing stores or reads the lead's latest message id: the script reads `[data-latest]`, which no template has, and `stored._latest` on an array is always undefined, so an older message's comments come back. The thread page's view (`thread_page` in `factory_dashboard/thread.py`) must pass it to `thread.html`.
- `_clearPageComments` is never called: a sent comment returns on reload. A failed send must keep them.
- The restore adds to the strip's counts on every `htmx:afterSettle`, so they grow.
- On a proposal page, restore opens `label.comment-box` but never runs the page's `update()`, so Approve plan stays beside Send back. Its script's variables (`primary`) go stale after a swap.
- The storage keyed by page path holds a list of `[point, text]`; the strip must count comments for other pages' paths too, from `sessionStorage`.
- `deck.js` is loaded as plain JavaScript: no TypeScript syntax; `node --check` must pass on it.
- The "not sent" colour goes in `dashboard.css` beside `.steps a.waits`, using `--hazard`.

### Done when
- the browser test: type a comment on a thread's point, go to a proposal step, the strip's Conversation says "1 comment not sent" in `--hazard`; come back, the comment is in its box, open
- the same on a proposal page: its comment returns, Send back shows, Approve plan is hidden
- after a successful Send or Send back the comment is gone from the box and the strip, on a reload too; after a failed one it stays
- a comment stored for an older lead message doesn't come back
- the strip's count does not grow across swaps
- the existing browser tests in both files still pass (the phone deck, the lead's answer on an open thread)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
