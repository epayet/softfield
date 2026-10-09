---
id: f9-19-fix-planted-row-sprout
milestone: f9-line-polish
difficulty: 3
depends_on: []
files:
- factory_dashboard/static/factory.js
- tests/factory_dashboard/test_line.py
tests:
- tests/factory_dashboard/test_line.py
finding: f9-line-polish-C2-1
---

### Goal
Fix a checkpoint finding on f9-03-field-links: the planted rows' links changed the sprout's drawing and moved the rows out of their station.

### Context
Found by the lead at a checkpoint, on the merge of `tasks/done/f9-03-field-links.md`. Read `factory_dashboard/static/factory.js`, `rows()` and `seeds()`; and the test `test_planted_row_links_to_milestone_and_seeds_to_set_aside_tickets` in `tests/factory_dashboard/test_line.py`.
- The ticket was to make rows tappable, not to redraw them. The sprout path `d` in `rows()` was edited: the second leaf's last curve was `c0-7 3-10 10-10 0 7-3 10-10 10` before the ticket (`git show e070f3c9e^:factory_dashboard/static/factory.js`), and now reads `c0-7 3-10 10-10 0 7-10-10 10 `. The leaf is drawn differently, and no test noticed.
- `make_link(svg, …)` is given the root `svg`, so each `[data-row]` group is no longer inside the `rows` station group (`g[data-station="rows"]`), as it was before; its words and bars also stay outside the station that holds the soil and the footer text.
- `rows()` reads `window.location.search` and builds the `?project=` query on every row, and `seeds()` does the same: the same two lines three times in the file.

### Done when
- the sprout path is exactly what it was before f9-03, and a test would fail if the path changed (compare the `d` attribute of a row's `.sprout` with the expected string)
- each `[data-row]` sits inside `g[data-station="rows"]` again (a link inside the station, around the row group), and a test says so
- the `?project=` query is built once, in one helper the seeds and rows both use
- the listed `tests:` pass and the earlier tapping test still passes
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 2171
gate_failures: []
tokens: 1095417
```
