---
id: bug-51-no-page-shows-escaped-html
milestone: bugs
difficulty: 3
depends_on: []
agent: developer
area: factory
finding: f158-milestones-don-t-show-me-their-F3
tests_only: true
files:
  - tests/factory_dashboard/test_app.py
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
One dashboard test opens every page on the test data and fails on escaped `&lt;ul&gt;`, `&lt;li&gt;` or `&lt;p&gt;`.

### Context
From the old backlog file, in the review's words:

F158's card page printed its Outcome as `<ul><li>…` text: `_to_html`'s output reached the template without `| safe`, and the tests' `section()` helper unescapes the text it reads, so they passed. A dashboard test that opens every page on the test data and fails on `&lt;ul&gt;`, `&lt;li&gt;` or `&lt;p&gt;` in the HTML would catch it on any page; `_to_html` could also return `Markup`. Stays: one case so far, fixed with its own test; a ticket if it shows again.

Checked against main on 2026-11-09 (F231): no test in `tests/factory_dashboard/test_app.py` looks for escaped markup yet. Queued now because F216's `_to_html` rework (f216-02) is about to touch the same rendering.

### Done when
- the test fails when a page prints escaped markup, and passes on today's pages
- the listed `tests:` pass
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1724
gate_failures: []
tokens: 793905
```
