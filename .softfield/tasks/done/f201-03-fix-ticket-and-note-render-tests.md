---
id: f201-03-fix-ticket-and-note-render-tests
milestone: f201-ticket-pages-render-markdown
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_milestones.py
tests:
- tests/factory_dashboard/test_milestones.py
- tests/factory_dashboard/test_tickets.py
finding: f265-the-factory-now-section-in-planning-C2444-2
tests_only: true
---

### Goal
Fix a checkpoint finding on f201-01-ticket-and-note-render-markdown's tests: Card-note and ticket-table Markdown rendering lacks integration coverage.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f201-01-ticket-and-note-render-markdown.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f265-the-factory-now-section-in-planning-C2444-2, should-fix: in `tests/factory_dashboard/test_milestones.py`, line 1034.

### Finding
f265-the-factory-now-section-in-planning-C2444-2: Card-note and ticket-table Markdown rendering lacks integration coverage.
> The card fixtures test escaped `<b>` text and ordinary note text, but never use backticks or verify `<code>`, and they do not assert line-break preservation or Markdown in either ticket-goal table branch. `tests/factory_dashboard/test_tickets.py` also verifies only a subset of ticket-page inline Markdown; it does not cover links, Context, or the different ticket-body fallback. These tests would miss the plain `t.goal` rendering defect.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 2451
gate_failures: []
tokens: 3753831
```
