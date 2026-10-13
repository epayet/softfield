---
id: f22-01-archive-at-the-bottom
milestone: f22-move-archive-button-on-planning-desk
difficulty: 2
depends_on: [f12-03-remove-review-probe]
files:
  - factory_dashboard/templates/thread.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
On a card's thread page, the Archive row and "Remove seed" move from the card's header to the bottom of the page, under the reply box.

### Context
Read `docs/milestones/f22-move-archive-button-on-planning-desk.md` (D1, D2) and `factory_dashboard/templates/thread.html`: the `#remove-seed` details and the `#archive` div sit in `<header id="card">`; the reply form `#reply` (class `dock`, sticky on a phone: `factory_dashboard/static/dashboard.css`) closes `#conversation`.
- Move both blocks as they are (ids, `hx-` attributes and conditions unchanged) into one row placed after `#conversation`'s closing tag, inside the same column.
- The tests to extend are the archive tests in `tests/factory_dashboard/test_planning.py` (`test_a_threads_button_archives_it_and_an_archived_ones_opens_it_again` and its neighbours); the ids they look for stay.
- **Put the row after `#conversation`, not inside it: a reply reloads `#conversation`, and inside it the row would sit under the sticky Send box.**

### Done when
- on a thread with messages, `id="archive-button"` comes after `id="reply"` in the page, and `<header id="card">` holds neither it nor `id="remove-seed"`
- on a seed, `id="drop-seed"` comes after `id="reply"` too
- while a reply waits (`id="waiting"` instead of the form), the Archive row still shows after it
- an archive on its way still shows its dashed "Archiving at the runner's next pick" pill in the new place, with no button
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 2775
gate_failures: []
tokens: 2386810
```
