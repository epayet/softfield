---
id: f144-01-review-reads-the-real-page
milestone: f144-a-review-should-open-the-real
agent: lead
difficulty: 2
depends_on: []
files:
  - runner/prompts.py
  - runner/instructions/lead.md
tests:
  - tests/runner/test_prompts.py
---

### Goal
A milestone review that changed a factory page reads that page on the live database before the tests, checks one fixture against a real record, and says in its report what it looked at.

### Context
Read `.softfield/adr/37-a-review-reads-the-real-page-first.md` (items 1–4), then `REVIEW` in `runner/prompts.py` and the "Review" section of `runner/instructions/lead.md`.
- In `REVIEW`, the paragraph "Read the tests as closely as the code" gains, before it, the look of items 1–2: which diff counts as a page change, `softfield look page <address>` for each changed page (text, and the raw HTML where escaping or attributes matter), one fixture per new test file against a real record (`.softfield/cards/`, `softfield look sql`), and a tidier fixture as a should-fix on the test. Item 3's line in the report goes with the report's instructions further down.
- The prompt can't name the lead's or the owner's doc (`test_the_lead_prompts_no_longer_point_at_lead_md_or_owner_md`), and keeps its `{…}` fields as they are (`runner/milestone.py` formats it).
- In `runner/instructions/lead.md` "Review", the bullet "Take screenshots of new screens when you have a browser" becomes: read a changed factory page with `softfield look page` before the tests (ADR 37), and screenshots for product pages when you have a browser.

### Done when
- `REVIEW` asks for the page look before "Read the tests", and for the fixture check and the report line
- `prompts.REVIEW.format(...)` with the fields `runner/milestone.py` passes still works
- the "Review" section of `runner/instructions/lead.md` names `softfield look page` and ADR 37
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
