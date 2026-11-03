---
id: bug-58-a-card-page-reads-its-doc-as-words
milestone: bugs
difficulty: 2
depends_on: []
agent: lead
area: factory
finding: f85-when-i-sign-off-a-task-F7
files:
  - factory_dashboard/milestones.py
tests:
  - tests/factory_dashboard/test_milestones.py
---

### Goal
A card's "What it's about" shows its doc's `` `code` `` as code and a `[word](../adr/x.md)` as the word alone, never the Markdown marks.

### Context
Read `def _to_html` in `factory_dashboard/milestones.py`: it renders only `- ` lists and `**bold**`, and `read_card_doc` passes the card doc's Done when through it. F85's own after picture shows ``in `[shots]` of its `.softfield/project.toml` ([ADR 40](../adr/40-pictures-at-sign-off-in-every-project.md))`` as written. `bug-30-the-sheet-renders-steps-and-links` makes links of `/`, `#`, `http://` and `https://` targets in the same function; this ticket covers what it leaves: backticks, and a relative target, whose address means nothing on the dashboard. Keep escaping first: the marks are matched on the escaped text, and a relative target never becomes an `href`.

### Done when
- `` `[shots]` `` in a card's Done when comes out as `<code>[shots]</code>`
- `[ADR 40](../adr/40-x.md)` comes out as the plain word `ADR 40`, with no link and no `../adr`
- `<script>` inside backticks comes out escaped
- a text with only `- ` lists and `**bold**` renders exactly as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
