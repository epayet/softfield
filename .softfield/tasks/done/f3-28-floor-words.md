---
id: f3-28-floor-words
milestone: f9-line-polish
depends_on: []
difficulty: 2
files:
  - factory_dashboard/line.py
  - factory_dashboard/static/factory.js
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
The floor's plates and rows say short, clean words: a rating as a bare number like "3.5", never "rated 3.4770…", and a planted row without a title says "F3", not "F3 ·".

### Context
Read `_machines` and `_field` in `factory_dashboard/line.py`, `rows` and `machine` in `factory_dashboard/static/factory.js`, and the document tests in `tests/factory_dashboard/test_line.py`. The picture: the plates and planted rows of `docs/milestones/f3-line-mockup/Line.dc.html` ("LOCAL GPU · rated 5", "F5 · steer and the board").
- **What the review saw (f3-22, `var/shots/f3-22/desktop-1440-dark-line-live.png`, on the real metrics):**
  - the plates read "CLAUDE · rated 6.026345…" and "LOCAL GPU · rated 3.4770…": `queries._rating` returns the latest `rating_changes.after`, a float, and the floor prints it whole;
  - every planted row reads "F3 ·", "F5-BOARD ·" with nothing after the dot: the live runner never writes a milestone's title (only `runner/backfill.py` does), so `title` is null.
- **The rule lives in Python** (`docs/milestones/f3.md` D11): the document's machine `rating` is rounded to one decimal (`10.0` stays 10, `6.03` becomes 6). `_scale` keeps reading the unrounded value.
- **The owner (2026-10-04):** "i don't need to see 'rated', just a number is enough like the mockup". The plate reads "LOCAL GPU · 3.5", and the machine's `title` keeps "rated 3.5" for a hover.
- **A row, a ripe milestone or a stash tile without a title** shows its key alone, with no " · ".

### Done when
- a document test: a machine whose latest rating is 3.4770 has `rating` 3.5, and one rated 10 has 10
- a browser test: a plate reads its rating without the word "rated"
- a browser test: a planted row with a null title reads its key alone, without "·"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 2294
gate_failures: []
tokens: 2082608
```
