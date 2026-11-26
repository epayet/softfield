---
id: f308-02-what-was-sent-back
milestone: f308-when-an-adr-is-being-sent
difficulty: 3
depends_on: [f308-01-a-note-with-send-back]
files:
  - factory_dashboard/thread.py
  - factory_dashboard/templates/proposal.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_proposal.py
area: factory
---

## Goal
After Send back, the review page shows what was sent: each comment under its point, and the note and any later notes in the dock, until the lead's next reply.

## Context
- The picture to build: `.softfield/cards/f308-mockup/send-back.html` (Proposed, moments 2 and 3).
- Read `.softfield/cards/f308-when-an-adr-is-being-sent.md`, D1.
- `factory_dashboard/thread.py`: `_standing` builds the review page's `Standing` from `_since` (the owner's requests since the lead's last reply) and `proposal_requests`. Add what was sent to `Standing`. Read a request's words with `planner.message`, as `thread_page` does for waiting messages.
- Notes are the card's `plan_message` requests (subject: the card's short key) in `_since`, oldest first. Leave out the one a send-back becomes at the runner's pick: its text starts `I sent back your proposal “` (`sent_back` in `runner/planner.py`).
- `factory_dashboard/templates/proposal.html`: `#actions.on-its-way` is the dashed box; `#settled` says "Sent back".

## Done when
- While the proposal's send-back is on its way, each commented key point shows "You said · on its way" with the comment under it, dashed hazard. The dock shows "Sent back HH:MM · N comments and a note" (the counts as sent) and the note, if any.
- The owner's other `plan_message` notes on the card since the lead's last reply show in the dock under it, oldest first, each with its time. The send-back's own message never shows as a note.
- Once the runner has taken it (state "sent back"), the same words show solid, stamped "You said · with the lead".
- An open proposal with no send-back since the lead's last reply shows none of this. Neither does one the lead's newer reply has replaced.
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 5330290
logs: .softfield/var/runs/20261126-115035/f308-02-what-was-sent-back
```
