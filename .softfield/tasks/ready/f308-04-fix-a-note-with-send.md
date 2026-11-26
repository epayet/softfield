---
id: f308-04-fix-a-note-with-send
milestone: f308-when-an-adr-is-being-sent
area: factory
difficulty: 2
depends_on: []
files:
- factory_dashboard/static/dashboard.css
tests:
- tests/factory_dashboard/test_proposal.py
finding: f279-i-would-like-to-be-able-C2857-1
---

### Goal
Fix a checkpoint finding on f308-01-a-note-with-send-back: The note box is hidden on every mobile proposal review.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f308-01-a-note-with-send-back.md`. What it found is under Finding:
- f279-i-would-like-to-be-able-C2857-1, blocking: in `factory_dashboard/static/dashboard.css`, line 452.

### Finding
f279-i-would-like-to-be-able-C2857-1: The note box is hidden on every mobile proposal review.
> The rule `.proposal-page .action-buttons .comment-box.change { display: none; }` breaks the ticket on phones. It makes the whole-proposal note unavailable and prevents a note-only send, contrary to "While the proposal is open, the dock has a box labelled 'A note for the lead, on the whole proposal'".

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
