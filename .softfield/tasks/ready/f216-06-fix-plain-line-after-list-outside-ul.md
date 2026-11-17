---
id: f216-06-fix-plain-line-after-list-outside-ul
milestone: f216-let-s-redesign-the-milestone-review
difficulty: 2
depends_on: [f216-05-fix-to-html-nested-list-inside-li]
files:
  - factory_dashboard/milestones.py
tests:
  - tests/factory_dashboard/test_milestones.py
finding: f216-05-F1
---

### Goal
A plain line after a bullet list is written after the list's `</ul>`, not inside it.

### Context
Read the "Regular line" branch of `_to_html` in `factory_dashboard/milestones.py` and `test_to_html_nested_list_followed_by_plain_line` in `tests/factory_dashboard/test_milestones.py`. Facts from the merged f216-05:
- `"- Top\n  - A\n  - B\nplain text"` gives `<ul><li>Top<ul><li>A</li><li>B</li></ul></li><p>plain text</p></ul>`: the `<p>` sits inside the outer `<ul>`, which is invalid HTML. Before f216-05 the branch closed `</ul>` first; the merge moved `if in_ul: </ul>` to after the `<p>`.
- The same happens for `"- a\nplain"`: `<ul><li>a</li><p>plain</p></ul>`.
- The test asserts that wrong string, so it passes.

### Done when
- `"- Top\n  - A\n  - B\nplain text"` gives exactly `<ul><li>Top<ul><li>A</li><li>B</li></ul></li></ul><p>plain text</p>` (assert on the whole string)
- `"- a\nplain"` gives exactly `<ul><li>a</li></ul><p>plain</p>`
- a blank line after a list still closes it, and `"1. a\nplain"` still gives `<ol><li>a</li></ol><p>plain</p>`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
