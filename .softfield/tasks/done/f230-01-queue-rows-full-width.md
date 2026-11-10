---
id: f230-01-queue-rows-full-width
milestone: f230-cards-in-the-queue-wrap-words
difficulty: 2
depends_on: []
files:
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/templates/_partials/queue.html
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
On the Overview's Queue panel, the fast lane's label and every row without a number read across the whole row, one line where they fit, on a phone and on a wide screen alike, and the fast lane looks like its bay again.

### Context
Read `.softfield/cards/f230-cards-in-the-queue-wrap-words.md` ("Why it happens", D1–D3).
- `.belt li` in `factory_dashboard/static/dashboard.css` is a grid of two columns, `28px 1fr`: the number, then the text. A row with one child (the `lane-label` row, and a queued job's row: Planning, Plant, any job) puts its text in the 28px column, so it wraps one word per line.
- The `.lane-bay` rules in the same file are left over from before `f81-12-fix-readout-units-and-belt-markup` turned the bay into rows of the list (`lane-label`, the lane's rows, `bay-end` in `factory_dashboard/templates/_partials/queue.html`); nothing uses them now.
- The existing tests find the bay with `_lane_bay` in `tests/factory_dashboard/test_overview.py`, which looks for the exact text `<li class="lane-label">` and `<li class="bay-end">`: keep those two rows' class attributes as they are, and put the new marker class only on the rows between them.
- For test data, copy `test_a_fast_lane_card_s_ticket_comes_first_in_its_bay_above_a_planner_job`: `_queue_on(board_db, "planner", "f11#1")` and `_reserve_client(board_db, tmp_path, "f23-planted")` give the fast lane and a Planning row below it. `metrics.upsert_ticket` takes no `priority`.
- For a browser test, follow the one in `tests/factory_dashboard/test_line.py` (`.softfield/developer.md`, "Factory line"): the page from `TestClient`, `/static/` from disk with `page.route`.

### Done when
- a `.belt` row with no `.n` takes both columns: at a 390px-wide viewport, the `lane-label` row's text "Fast lane goes before everything" sits on one line (a browser test reads its height against one line's), and so does a queued Planning job's row prefix
- rows with a number keep the 28px number column
- the fast lane's rows, from `lane-label` to `bay-end`, carry the hazard stripe on their left as `.lane-bay::before` drew it (mark the rows between them with a class in the template), and the label keeps `.lane-bay .label`'s look; the stripe uses `--hazard` and `--hazard-ink` only
- the unused `.lane-bay` rules are gone, and the template's markup stays valid (only `li` inside the `ol`)
- the existing tests in `tests/factory_dashboard/test_overview.py` pass unchanged
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 2778
gate_failures: ['no-changes', 'mypy']
tokens: 5234270
```
