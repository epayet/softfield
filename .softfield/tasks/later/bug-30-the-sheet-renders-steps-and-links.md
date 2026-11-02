---
id: bug-30-the-sheet-renders-steps-and-links
milestone: bugs
difficulty: 4
depends_on: []
agent: lead
area: factory
priority: 57
finding: f50-the-data-safety-review-it-asks-F5
files:
  - factory_dashboard/milestones.py
tests:
  - tests/factory_dashboard/test_milestones.py
---

### Goal
A review's sheet shows its numbered "How to test" steps as a list and its `[text](link)` as links, on the card's page and the milestone page.

### Context
Read `def _to_html` in `factory_dashboard/milestones.py`: it renders only `- ` lists and `**bold**`, escaping first, and its output goes through `| safe` in `factory_dashboard/templates/thread.html`. **Security:** the sheet is the lead's Markdown, so keep escaping first, and make a link only of a target that starts with `/`, `#`, `http://` or `https://` (anything else, `javascript:` included, stays text). Test-first: write the escaping and link-scheme cases before the code.

### Done when
- lines `1. Open the board` and `2. Drag F12` become one `<ol>` with two `<li>`
- `[the review](/milestones/f12)` becomes `<a href="/milestones/f12">the review</a>`; an `https://` link too
- `[x](javascript:alert(1))` and `<script>` in the text come out as escaped text, no tag and no link
- a sheet with only `- ` lists and `**bold**` renders exactly as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
