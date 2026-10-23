---
id: f159-02-ticket-notes-keep-their-lines
milestone: f159-there-s-a-bug-set-aside
agent: developer
difficulty: 2
depends_on: []
finding: f159-there-s-a-bug-set-aside-F2
files:
  - factory_dashboard/tickets.py
  - factory_dashboard/templates/ticket.html
tests:
  - tests/factory_dashboard/test_tickets.py
---

### Goal
On a ticket's page, the Goal and the folded "The lead's notes for the agent" keep their paragraphs and their `- ` bullets as a list, instead of running every line into one paragraph.

### Context
- `parse_ticket_body` in `factory_dashboard/tickets.py` keeps `goal` and `context` as one string each, and `factory_dashboard/templates/ticket.html` shows each in one `<p>`, so bug-03's notes read as one block with "- The lead's first pass…" in the middle of it (`/tickets/bug-03-roadmap-items-to-seeds`).
- The example to follow: `done_when` in the same function, a list of lines that the template shows as `<li>`.
- Make `goal` and `context` lists of blocks: a blank line starts a new paragraph, and a run of lines starting with `- ` is one list whose items are the text after `- `. A line that doesn't start with `- ` right after a bullet carries on that bullet's text. Show each paragraph as a `<p>` and each list as a `<ul>`.
- Only these two fields change; `done_when`, the plate, and a body without the headings stay as they are. Update the three `test_parse_ticket_body_*` tests for the new shape.

### Done when
- a Context of "Intro line.\n- first\n- second\n\nLast paragraph." shows as a paragraph, a list of two items and a paragraph inside the closed `<details>`
- a Goal of two paragraphs shows as two `<p>`
- a bullet wrapped over two lines is one list item holding both lines
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1575
gate_failures: []
tokens: 987469
```
