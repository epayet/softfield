---
id: f308-05-fix-a-note-with-send-tests
milestone: f308-when-an-adr-is-being-sent
area: factory
difficulty: 2
depends_on: []
files:
- tests/factory_dashboard/test_proposal.py
tests:
- tests/factory_dashboard/test_proposal.py
finding: f279-i-would-like-to-be-able-C2857-2
tests_only: true
---

### Goal
Fix a checkpoint finding on f308-01-a-note-with-send-back's tests: New note tests miss key labels, hiding rules, trimming, and cleared textarea content.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f308-01-a-note-with-send-back.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f279-i-would-like-to-be-able-C2857-2, should-fix: in `tests/factory_dashboard/test_proposal.py`, line 1224.

### Finding
f279-i-would-like-to-be-able-C2857-2: New note tests miss key labels, hiding rules, trimming, and cleared textarea content.
> The tests must cover the exact "Send 2 changes and a note back" label (not just 1-change-with-note), the "Send 2 changes back" label, and whitespace trimming in posted text. They must verify that a note hides Accept ADR and Approve first as well as Approve plan, and that success empties the note textarea and reload leaves it empty—not merely that sessionStorage's entry is removed.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
