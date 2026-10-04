---
id: f4-35-fix-crate-card-untested-unescaped
milestone: f3
difficulty: 3
depends_on: []
files:
  - factory_dashboard/static/factory.js
  - tests/factory_dashboard/test_line.py
tests:
  - tests/factory_dashboard/test_line.py
finding: f3-19-crate-details-checkpoint-7
---

### Goal
Fix a checkpoint finding on f3-19-crate-details: the card writes ticket titles into the page as HTML, and the card's machine, waits and batch contents have no test.

### Context
Read `showCard` in `factory_dashboard/static/factory.js` and the "crate card (f3-19)" tests in `tests/factory_dashboard/test_line.py`.
- `showCard` builds the card with `card.innerHTML = html` from `info.title`, `info.ticket`, `info.role` and `info._agent`. A title such as `Fix <b>x</b> & y` is rendered as markup, not shown as written. Titles come from ticket files.
- The three tests only click a queued crate and check the link; none checks the title text, which the ticket's "Done when" names.
- Nothing tests the card for a crate on a machine (agent, attempt, minutes), for a queued crate that waits (`waits`), for a batch crate (role, no link), or the Enter key and the click-outside close.
- `crateInfo` looks in `doc.queue` twice and reads `doc.merged`; the ticket names only queue and machine crates.

### Done when
- the card shows the title as text: a test with a ticket title holding `<` and `&` reads the card's text and finds them as written
- a browser test: a queued crate that waits shows what it waits for in the card
- a browser test: a crate on a machine shows its agent, attempt and minutes; a batch crate shows its role and has no link
- a browser test: Enter on a focused crate opens the card, and a click outside the crates closes it
- the listed `tests:` pass, and fail without the behaviour they check
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 5729
gate_failures: ['task-tests', 'stopped']
tokens: 5081233
```
