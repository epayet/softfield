---
id: f308-01-a-note-with-send-back
milestone: f308-when-an-adr-is-being-sent
difficulty: 2
depends_on: []
files:
  - factory_dashboard/templates/proposal.html
  - factory_dashboard/static/deck.js
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_proposal.py
area: factory
---

## Goal
A proposal's review page has a note box for the whole proposal, and Send back sends its words with the comments.

## Context
- The picture to build: `.softfield/cards/f308-mockup/send-back.html` (Proposed, moment 1).
- Read `.softfield/cards/f308-when-an-adr-is-being-sent.md`, D2.
- `factory_dashboard/templates/proposal.html`: `#send-back` posts `send_back` with `text: ""`; its page script (`update`) shows it and sets its label from the filled `textarea.comment` boxes.
- `factory_dashboard/static/deck.js` keeps unsent comments in the tab (`window.sentComments` clears them after a successful send). The note is kept and cleared the same way.
- `runner/requests.py` `_send_back` already passes `text` on to the lead; nothing in `runner/` changes.

## Done when
- While the proposal is open, the dock has a box labelled "A note for the lead, on the whole proposal", above Send back, as in the mock-up.
- Send back's `value` carries the note's trimmed words as `text`, beside `comments`.
- Send back shows, and Approve, Accept ADR and Approve first hide, when there is a comment or a note. Its label reads "Send 2 changes back", "Send 2 changes and a note back", "Send 1 change and a note back" or "Send a note back".
- A note typed and not sent comes back after a reload, and is gone after a successful Send back.
- Refresh against main still sends its own words.
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 3821
gate_failures: []
tokens: 3610563
```
