---
id: f9-08-fix-the-phone-title-and
milestone: f9-line-polish
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
finding: f9-line-polish-C423-1
tests_only: true
---

### Goal
Fix a checkpoint finding on f3-30-phone-top-bar: the test doesn't show that the phone title and project filter share one line.

### Context
A should-fix finding (f9-line-polish-C423-1) by copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f3-30-phone-top-bar.md`. What it found is under Finding.

- The CSS is already right on main: f6-16 rewrote the phone rule. In `factory_dashboard/static/dashboard.css`, the block under the comment `/* Phone top bar (f3-30): ... */` (`@media (max-width: 639px)`, around line 255) sets `.bar-top { display: grid; grid-template-columns: minmax(0, 1fr) auto; ... }` and `.bar-top .filters label { grid-area: 1 / 2; ... }`. There is no `flex-direction: column` left in it. So this ticket changes only the test, and its test passes on main's code, as it should.
- The file has an earlier `@media (max-width: 639px)` block (the allowance block, around line 177). A test that searches from the first such media query finds the wrong block; anchor on the "Phone top bar (f3-30)" comment.
- The test to strengthen is `test_the_top_bar_has_the_mockups_title_hazard_stripe_and_tab_segment` in `tests/factory_dashboard/test_app.py`; the branch already holds an attempt at it.

### Finding
> The mobile rule sets `.bar-top` to `flex-direction: column`, directly contradicting f3-30’s requirement that the title and filter share a line. The height assertion does not catch this layout failure.

### Done when
- a test checks, in the phone top bar block, that `.bar-top` is a two-column grid (`grid-template-columns: minmax(0, 1fr) auto`) and that `.bar-top .filters label` sits on row 1, column 2 (`grid-area: 1 / 2`)
- nothing outside `tests/` changes
- the listed `tests:` pass, and all gates pass

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: tests-fail-on-main)
attempts: 3
tokens: 1495691
logs: var/runs/20261009-020915/f9-08-fix-the-phone-title-and
```

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 1964
gate_failures: ['stopped', 'stopped']
tokens: 302539
```
