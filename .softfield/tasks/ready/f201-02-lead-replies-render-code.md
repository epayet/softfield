---
id: f201-02-lead-replies-render-code
milestone: f201-ticket-pages-render-markdown
difficulty: 3
depends_on: [f201-01-ticket-and-note-render-markdown]
agent: lead
files:
  - factory_dashboard/merges.py
tests:
  - tests/factory_dashboard/test_thread.py
---

### Goal
On a planning thread, the lead's and the runner's words (messages, each point's title, answer and action) show inline code and bold rendered, with the card, ticket and ADR links they have today.

### Context
Read `.softfield/cards/f201-ticket-pages-render-markdown.md` (D5). `_text_with_links` in `factory_dashboard/merges.py` escapes the text and links card numbers, tickets, ADRs and `/planning/<key>`; `factory_dashboard/thread.py` feeds it every lead and runner text. Apply `inline_html`'s rules (from `factory_dashboard/milestones.py`, f201-01) to the escaped text there, before the references are linked: a ticket name in backticks then becomes a linked code chip. Markdown links (`[a](https://…)`) stay out of this step: the references' own links already cover what the lead writes, and a reference linked inside a markdown link's `href` would break the page. The owner's own messages stay plain, as they are. Test-first.

### Done when
- a lead point's answer holding `` `f201-01-ticket-and-note-render-markdown` `` shows a `<code>` holding the ticket's link
- `**x**` in a lead message shows as `<strong>x</strong>`
- `` `<script>` `` and `<script>` in a lead message still come out escaped
- a reference with its added name (`F22`, then ", Archive at the bottom") reads as today outside backticks
- the owner's messages render as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
