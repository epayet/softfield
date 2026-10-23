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
On a card's page, the Outcome and Done when read from the card's doc show as a real list and paragraphs, not as literal `<ul><li>` text.

### Context
Fix a checkpoint finding on `f158-01-card-says-what-its-about`. `<section id="about">` in `factory_dashboard/templates/milestone.html` prints `{{ about_data.outcome_html }}` and `{{ about_data.done_when_html }}` without `| safe`, while the other `_to_html` uses on the page (`outcome_html | safe`, `signoff_html`) have it. `_to_html` escapes the text itself and returns a plain `str`, so with autoescape on, the page shows the tags as text.
- The tests did not catch it: `section()` in `tests/factory_dashboard/test_milestones.py` now runs `html.unescape` over the stripped text, so escaped tags read as the words. Keep the unescape only if a test needs it for an apostrophe; the content tests for `#about` must look at the raw HTML of the section and assert `<li>The page shows this outcome</li>` is there and `&lt;li&gt;` is not.
- Two smaller things in the same code, fix them here: `read_card_doc` returns an `AboutDoc` for any card doc, even one with no Outcome and no Notes, so a stored `milestone.outcome` is never shown then (the template falls back to it only when there is no doc); and `_card_note` copies the notes reader of `factory_dashboard/planning.py` that the ticket said to reuse. Reuse that reader if it can be imported without a cycle, else leave it and say why in the commit.
- A card doc with a `## Done when` but no `## Outcome` loses its Done when; show the stored or doc Outcome/Done when by the same rule.

### Done when
- the raw HTML of `#about` for a card with an Outcome has `<li>` items and no `&lt;li&gt;`
- a card doc with neither Outcome nor Notes, and a stored outcome, shows the stored outcome in `#about`
- the listed `tests:` pass, and the first one fails without the template change
- all gates pass (see `docs/workflow.md`)
