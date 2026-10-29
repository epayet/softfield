---
id: f37-02-thread-links-numbers
milestone: f37-in-planning-mode-it-tends-to
difficulty: 5
depends_on: []
files:
  - factory_dashboard/merges.py
  - factory_dashboard/thread.py
  - factory_dashboard/templates/thread.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_thread.py
---

### Goal
On a planning thread, every card number links to its thread and every ticket to its page, and a card the lead left bare shows its name beside the number.

### Context
The picture to build: `.factory/cards/f37-mockup/thread-names.html` (Proposed). Read `.factory/cards/f37-in-planning-mode-it-tends-to.md` D2 and D3.
- The example to grow is `_text_with_links` in `factory_dashboard/merges.py` (it escapes first, then links `/planning/<key>`). Card titles come from `_card_titles` in `factory_dashboard/coming.py`; the set of cards on main from `_known_cards` in `factory_dashboard/merges.py`.
- `thread_page` in `factory_dashboard/thread.py` sets `text_html` today only for a lead message without points (the loop after the comment "Lead messages without points"); the lead's points and the runner's messages get none. In `factory_dashboard/templates/thread.html` the lead's text is the `p.said` line and each point is an `li.point`.
- Ticket ids come from the `tickets` table (column `ticket`), as `/tickets/<id>` finds them (`factory_dashboard/tickets.py`). ADR titles come from the first heading of `.factory/adr/<NN>-*.md` in the project's repo (`_repo` in `factory_dashboard/planning.py`).
- The links keep the page's `?project=`. A new style for the muted name goes in `dashboard.css` from its existing tokens.
- The owner's messages stay plain text.

### Done when
- in a lead point, `F42` links to `/planning/f42` and shows ", The space for me to scroll…" (cut to 40 letters at a word, the whole title as the link's `title`); `F15, Reprioritising tickets` links F15 and adds nothing
- `f15-06-card-actions` links to `/tickets/f15-06-card-actions`; `f63-01` links to `f63-01-desk-order` and adds ", desk order"; a number that names no card or ticket stays plain
- `ADR 29` shows ", The lead looks at a blocked ticket", with no link
- the same holds in a lead message's text (with and without points) and in a runner message; an owner's message with `F42` or `<b>` shows them as plain text
- the layout check passes at 390 px
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
