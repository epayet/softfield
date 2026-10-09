---
id: f9-30-fix-phone-title-and-filter-one-line
milestone: f9-line-polish
difficulty: 2
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
finding: f9-line-polish-C4-1
---

### Goal
Fix a checkpoint finding on f9-08-fix-the-phone-title-and: its test reads the CSS text and never shows that, on a phone, the title and the project filter sit on one line.

### Context
Found by the lead at a checkpoint, on the merge of `tasks/done/f9-08-fix-the-phone-title-and.md`. Read the end of `test_the_top_bar_has_the_mockups_title_hazard_stripe_and_tab_segment` in `tests/factory_dashboard/test_app.py`, and the "Phone top bar (f3-30)" block in `factory_dashboard/static/dashboard.css`.
- The added lines slice 700 characters after a comment, then match `display: grid`, the column template and `grid-area: 1 / 2` with regexes. It passes if the CSS says so even when the browser lays the bar out otherwise; a person would look at the page.
- Its comment cites a finding id (`f9-line-polish-C423-1`) that doesn't exist.
- Examples of browser tests at 390 px, with `page.route` serving the app and `layout_problems(page)`, are in `tests/factory_dashboard/test_overview.py` (search `set_viewport_size({"width": 390`).

### Done when
- a browser test at 390 px opens a page with the top bar and asserts the brand's box and the project select's box overlap vertically (same line) and the select sits to the right of the brand
- the test also fails when `.bar-top` is not a grid on the phone (check by temporarily removing the rule)
- the CSS-regex lines and the made-up finding id are removed from the old test
- the listed `tests:` pass
- all gates pass

```yaml
# --- runner ---
result: escalated
reason: pre-flight failed
attempts: 0
tokens: 0
logs: var/runs/20261009-020915/f9-30-fix-phone-title-and-filter-one-line
```
