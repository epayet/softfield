---
id: f216-05-fix-to-html-nested-list-inside-li
milestone: f216-let-s-redesign-the-milestone-review
difficulty: 4
depends_on: [f216-04-to-html-lists-and-href]
files:
  - factory_dashboard/milestones.py
tests:
  - tests/factory_dashboard/test_milestones.py
finding: f216-04-F1
---

### Goal
`_to_html` writes a nested `<ul>` inside its parent's `<li>`, and its tests compare the whole output.

### Context
Read `_to_html` in `factory_dashboard/milestones.py` and the `test_to_html_*` tests in `tests/factory_dashboard/test_milestones.py` (f216-04's). Facts from the merged code:
- `"- Top\n  - A\n  - B\n- Bottom"` gives `<ul><li>Top</li><ul><li>A</li><li>B</li></ul><li>Bottom</li></ul>`: the `<li>` is closed before the nested `<ul>` opens, so a `<ul>` sits directly in a `<ul>`. f216-04's Done when asked for it inside the `<li>`.
- `test_to_html_consecutive_indented_bullets_nest_in_one_ul` and `test_to_html_three_consecutive_indented_bullets_in_one_ul` take `result.index("<ul>")`, which is the outer `<ul>`, so their "inside the parent's `<li>`" asserts hold trivially.
- A dedent to a smaller non-zero indent sets `current_indent = 0` inside the loop; a numbered item or a plain line with a nested `<ul>` open is the other path that must close it.

### Done when
- `"- Top\n  - A\n  - B\n- Bottom"` gives exactly `<ul><li>Top<ul><li>A</li><li>B</li></ul></li><li>Bottom</li></ul>` (assert on the whole string)
- a nested list that ends the text, or is followed by a plain line, closes its `</ul></li>` before the outer `</ul>`
- the same whole-string check for `1. a`, `- b`, `2. c` and for a url with a `"`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
