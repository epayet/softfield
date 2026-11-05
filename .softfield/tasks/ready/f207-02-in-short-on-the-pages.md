---
id: f207-02-in-short-on-the-pages
milestone: f207-i-want-a-tl-dr-of
difficulty: 3
depends_on: []
files:
  - factory_dashboard/thread.py
  - factory_dashboard/templates/thread.html
  - factory_dashboard/templates/proposal.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_thread.py
  - tests/factory_dashboard/test_proposal.py
---

### Goal
A thread's lead reply and a proposal's review open with an "In short" plate above the points.

### Context
The picture to build is `.softfield/cards/f207-mockup/in-short.html`, Proposed (without its green marks and notes); its `.in-short` rules are the plate's. Read D4, D5 and D6 in `.softfield/cards/f207-i-want-a-tl-dr-of.md`. A proposal's words are in `proposal.tldr`, its optional field; a reply's are the message's text, drawn with `text_html` so its links stay. The rules go with the two pages' in `factory_dashboard/static/dashboard.css`, under `:is(.thread-page, .proposal-page)`. `tests/factory_dashboard/test_thread.py` has two tests of the "Full reply" fold whose text is short: give them a long text to keep testing the fold.

### Done when
- a lead message with points and text of at most 400 characters shows that text in an open plate labelled "In short", above its points, with no "Full reply" fold
- one with points and text over 400 characters keeps the closed "Full reply" fold and has no plate
- one with points and no text has neither; one with no points shows its text as before
- the earlier messages folded under "Earlier in this thread" follow the same rules
- a proposal with a `tldr` shows it in the plate under the page's header, above a mock-up's frame when there is one; one without has no plate and no empty space
- on a phone (390 px) the plate stays in place while ◀ ▶ step through the points
- the listed `tests:` pass, and fail without the change
