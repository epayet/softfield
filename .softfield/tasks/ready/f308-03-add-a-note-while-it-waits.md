---
id: f308-03-add-a-note-while-it-waits
milestone: f308-when-an-adr-is-being-sent
difficulty: 3
depends_on: [f308-02-what-was-sent-back, f267-01-waiting-notes-one-reply, f308-06-fix-note-box-on-a-phone]
files:
  - factory_dashboard/templates/proposal.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_proposal.py
area: factory
---

## Goal
While a proposal's send-back is on its way or with the lead, its review page has an "Add a note" box whose note goes to the card's thread and shows at once under what was sent.

## Context
- The picture to build: `.softfield/cards/f308-mockup/send-back.html` (Proposed, moments 2 and 3).
- Read `.softfield/cards/f308-when-an-adr-is-being-sent.md`, D3 and D4.
- The worked example: `#reply` in `factory_dashboard/templates/thread.html`, F267's plate ("Add a note") and its `plan_message` request (subject: the card's short key). The review page's box sends the same request, with `text` and empty `comments`.
- f308-02 already lists the card's notes since the lead's last reply in the dock (`Standing` in `factory_dashboard/thread.py`).

## Done when
- With the state on its way, the dock shows the plate "Add a note" ("the lead reads it with this"), a box labelled "Anything you forgot? It goes with this send-back, in the same reply." and an "Add note" button. With the state sent back, the plate reads "after this reply".
- Add note posts a `plan_message` on the card's thread. On success, the note shows at once at the end of the notes, dashed, and the box is emptied. On failure, the words stay in the box with the answer in its status line.
- An empty box sends nothing.
- An open, approved, rejected or replaced proposal has no such box.
- Add note is outside the part of `#actions` that an on-its-way state hides.
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
