---
id: f158-02-fix-about-shows-html-tags
agent: developer
milestone: f158-milestones-don-t-show-me-their
difficulty: 2
depends_on: []
files:
  - factory_dashboard/templates/milestone.html
  - factory_dashboard/milestones.py
  - tests/factory_dashboard/test_milestones.py
tests:
  - tests/factory_dashboard/test_milestones.py
finding: f158-milestones-don-t-show-me-their-C1-1
---

### Goal
On a card's page, a card doc that says nothing (no Outcome, no Done when, no Notes) no longer hides the milestone's stored outcome, and a card doc with a `## Done when` but no `## Outcome` shows its Done when.

### Context
Fix a checkpoint finding on `f158-01-card-says-what-its-about`. The review of F158 already fixed part of the finding on main; leave those parts as they are:
- `<section id="about">` in `factory_dashboard/templates/milestone.html` already prints `about.outcome_html | safe` and `about.done_when_html | safe`. Keep both `| safe`: `_to_html` escapes the text itself. Removing them makes the existing test `test_a_card_with_outcome_shows_it_in_about_and_folds_the_note` fail on its `<li>The page shows this outcome</li>` assertion.
- `read_card_doc` in `factory_dashboard/milestones.py` already reuses `_note` from `factory_dashboard/planning.py`; there is no `_card_note` any more.

What is left:
- `read_card_doc` returns an `AboutDoc` for any card doc, even one with no Outcome, no Done when and no Notes. `milestone_detail` falls back to the stored outcome (`read_card_doc(...) or AboutDoc(_to_html(detail.outcome), ...)`) only when it returns None, so the stored outcome never shows then. Make `read_card_doc` return None in that case; `milestone_detail` and its fallback need no change.
- In the template, the Done when block sits inside `{% if about.outcome_html %}`, so a doc with only a `## Done when` (and no Notes) falls to "Nothing written about it yet." Show the Done when whenever `about.done_when_html` is set, with or without an Outcome. Keep every other branch and its words as main has them: the three existing `#about` tests (`card_doc_client`, `card_note_only_client`, `card_nothing_client` in `tests/factory_dashboard/test_milestones.py`) must pass unchanged.
- New tests go next to those three, with fixtures written like `card_nothing_client` (a card doc in `tmp_path / ".factory" / "cards"`, `metrics.upsert_project(..., repo=str(tmp_path))`); store an outcome with `metrics.upsert_milestone(conn, pid, "f1", outcome=..., done_when=...)`. Check the raw HTML of `section(html, "about")`'s source, not only its text: `section()` unescapes.

### Done when
- a card doc with neither Outcome, Done when nor Notes, and a stored outcome, shows the stored outcome in `#about` (as `<p>`/`<li>`, no `&lt;`), and not "Nothing written about it yet."
- a card doc with a `## Done when` and no `## Outcome` or `## Notes` shows "Done when" and its items in `#about`
- the three existing `#about` tests pass unchanged
- the listed `tests:` pass, and the new ones fail on main
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 5803
gate_failures: ['stopped', 'task-tests']
tokens: 3618023
```
