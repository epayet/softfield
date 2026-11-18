---
id: f201-01-ticket-and-note-render-markdown
milestone: f201-ticket-pages-render-markdown
difficulty: 3
depends_on: [f216-02-findings-costs-and-markdown, f216-03-review-page-plates-and-folds, f216-06-fix-plain-line-after-list-outside-ul]
files:
  - factory_dashboard/milestones.py
  - factory_dashboard/app.py
  - factory_dashboard/templates/ticket.html
  - factory_dashboard/templates/milestone.html
  - factory_dashboard/templates/thread.html
tests:
  - tests/factory_dashboard/test_milestones.py
  - tests/factory_dashboard/test_tickets.py
---

### Goal
A ticket's page and a card's note show inline code, bold and links rendered, through one `md` template filter that reuses `_to_html`'s inline rules.

### Context
The picture to build is `.softfield/cards/f201-mockup/ticket-and-note.html`: only the text changes, no layout, class or colour. Read `.softfield/cards/f201-ticket-pages-render-markdown.md` (D1 to D4).
- `_to_html` in `factory_dashboard/milestones.py` (as f216-02 left it) already renders `` `x` ``, `**x**` and `[text](url)` after escaping. Split that inline part out as `inline_html(text: str) -> Markup` (it escapes, then applies the inline rules), and have `_to_html` use the same inline step, so there is one set of rules.
- Register it in `factory_dashboard/app.py` beside `usd`, `pct` and the others in `templates.env.filters.update(...)`, as `md`.
- Use `| md` on: each paragraph's text and list item in Goal and in "The lead's notes for the agent", and each Done when item, in `factory_dashboard/templates/ticket.html` (`#goal`, the parsed branch only; the `<pre>` fallback stays as it is); the owner's note on the card's page (`about.note`, both places) and each ticket's goal in the card's ticket table, in `factory_dashboard/templates/milestone.html`; the note in `#note` in `factory_dashboard/templates/thread.html`. The note keeps `white-space: pre-line`: line breaks and `- ` lines stay as typed.
- The existing `_to_html` tests in `tests/factory_dashboard/test_milestones.py` show the cases; `tests/factory_dashboard/test_tickets.py` shows how a ticket page is fetched.

### Done when
- `inline_html` turns `` `git show x` `` into `<code>git show x</code>`, `**x**` into `<strong>x</strong>`, `[a](https://x)` into a link, and `[a](javascript:x)` and `[a](../x.md)` into the text alone
- `inline_html("<script>")` and `` inline_html("`<b>`") `` come out escaped, and stars inside backticks stay as typed
- `_to_html`'s existing tests still pass unchanged
- a ticket page whose Goal holds `` `_to_html` `` shows `<code>_to_html</code>` in `#goal`, and so do its Done when items and notes
- a card page and its thread show a note's backticks as `<code>`, with its line breaks kept
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 9281
gate_failures: ['task-tests', 'stopped']
tokens: 7638553
```
