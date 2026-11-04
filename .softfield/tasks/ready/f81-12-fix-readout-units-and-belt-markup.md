---
id: f81-12-fix-readout-units-and-belt-markup
milestone: f81-assess-the-current-ui-state-of
area: factory
difficulty: 3
depends_on: [f81-10-fix-now-readouts]
files:
- factory_dashboard/templates/_partials/running.html
- factory_dashboard/templates/_partials/queue.html
tests:
- tests/factory_dashboard/test_overview.py
finding: f81-06-readout-units-and-belt-markup
---

### Goal
Fix a checkpoint finding on f81-06-now-readouts: the Elapsed readout prints a wrong unit, and the Next in line list is invalid markup.

### Context
Files: `factory_dashboard/templates/_partials/running.html`, `factory_dashboard/templates/_partials/queue.html`. The `ago` filter (`factory_dashboard/app.py`) already returns its own unit (`30 s`, `12 min`, `2 h`).
- Elapsed: `{{ job.elapsed | ago }}<small>s</small>` prints `12 mins`, `2 hs`, `30 ss`. The test only checks `"12 min" in now`, so it passes.
- Difficulty readout has an empty `<small></small>`; the `.n` spans of non-ticket rows are empty.
- A job with no tokens reported now reads `0 tokens` where it said "no tokens reported yet" before.
- `queue.html`: the `<ol class="belt">` holds a `<div class="lane-bay">` and a final `<li>` "Reorder on the board" link; a `div` is not allowed in an `ol`, and the bay's `<li>`s have no list parent.

### Done when
- Elapsed shows the `ago` text with no added unit, and a test checks the exact readout text (`12 min`, not `12 mins`)
- a running job with no token counts says that no tokens are reported yet, and a test shows it
- every `<li>` of Next in line sits directly in an `ol`/`ul` (the fast lane bay included), with no empty `<small>` or `.n` left, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
