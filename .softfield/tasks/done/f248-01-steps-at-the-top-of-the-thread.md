---
id: f248-01-steps-at-the-top-of-the-thread
milestone: f248-this-card-s-steps-in-at
difficulty: 3
depends_on: []
files:
  - factory_dashboard/templates/thread.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_thread.py
---

### Goal
On a card's thread, "This card's steps" sits at the top, in the card's header under its title, where a proposal's page already has it.

### Context
The picture to build: `.softfield/cards/f248-mockup/steps-at-the-top.html` (Proposed). Read D1 and D2 in `.softfield/cards/f248-this-card-s-steps-in-at.md`. Follow `factory_dashboard/templates/proposal.html`, which includes `factory_dashboard/templates/_partials/card_steps.html` inside its `header.card-head`.
- In `factory_dashboard/templates/thread.html`, the strip and its `#steps-note` move out of `#conversation` into `header#card`, after the title and the merged links. The partial itself doesn't change.
- The strip still changes without a reload: today it rides the conversation's redraws (the 5 s poll, and the redraw after Send). Outside `#conversation`, those redraws must also replace `#card-steps` and `#steps-note` from the page they fetched (or remove them when the fetched page has none, add them when it has). `#conversation-stamp` already changes with a proposal's state.
- `factory_dashboard/static/deck.js` marks steps with comments not sent; it reads `#card-steps` wherever it is, but it must run again after the strip is replaced.
- The tests in `tests/factory_dashboard/test_thread.py` that place the strip under the lead's reply (`test_the_strip_reads_conversation_mock_up_plan_under_the_reply`, `test_on_a_phone_the_strip_comes_before_the_reply_box`) change to the new place.

### Done when
- a thread with a plan and a mock-up: the strip and "Nothing becomes a ticket until you approve it." are inside the card's header, under its title, before "Your note" and the lead's latest reply; nothing of the strip is left inside `#conversation`
- at 390 px, the strip's top is above the lead's latest reply, each step at least 44 px tall, nothing overflows
- the owner sends a message: the open proposals' steps say "being revised", dashed, without a reload
- the lead's reply with a first proposal arrives through the 5 s poll on a thread that had none: the strip appears in the header without a reload
- a comment typed on a proposal's point, then the thread opened: the strip's step says "1 comment not sent", as before
- a thread with no proposals has no strip
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 3598
gate_failures: []
tokens: 4187306
```
