---
id: f170-05-fix-desk-offers-the-fix
milestone: f170-there-s-a-blocked-ticket-that
difficulty: 3
depends_on: []
files:
- factory_dashboard/planning.py
tests:
- tests/factory_dashboard/test_planning.py
finding: f170-there-s-a-blocked-ticket-that-C1695-1
---

### Goal
Fix a checkpoint finding on f170-03-desk-offers-the-fix: Blocked-item text and button states do not match the ticket

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f170-03-desk-offers-the-fix.md`. What it found is under Finding:
- f170-there-s-a-blocked-ticket-that-C1695-1, should-fix: in `factory_dashboard/planning.py`.

### Finding
f170-there-s-a-blocked-ticket-that-C1695-1: Blocked-item text and button states do not match the ticket
> The ticket requires: “The words under the ticket keep the runner's reason and "· N tickets wait behind it", without "its work is on task/…" and without today's "· the lead's fix waits on F152's thread" or "· the lead is looking at it": the plate says those now.” The regex truncates the text from “work is on task/” onward, which also drops any trailing ticket-wait count; then `_blocked` appends the forbidden lead-status phrases. In `factory_dashboard/templates/planning.html`, the plate uses `fix_first_point` to distinguish a reply from no reply, so a lead reply with no points incorrectly shows the “still looking” message. The retry button is also rendered as quiet and labeled “Try again as it is” for every blocked item, contrary to the Done-when requirement that “a blocked bug ticket: "Try again" and "Set aside" as today.”

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
