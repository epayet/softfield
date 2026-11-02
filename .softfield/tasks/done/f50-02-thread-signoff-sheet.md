---
id: f50-02-thread-signoff-sheet
milestone: f50-the-data-safety-review-it-asks
depends_on: [f50-01-ripe-after-review]
difficulty: 3
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/thread.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A card's page shows its review's sign-off sheet (what changed, how to test, decisions waiting) above the conversation, so a finished card is never an empty page.

### Context
Read `thread_page` and `_header` in `factory_dashboard/planning.py`, `factory_dashboard/templates/thread.html`, and in `factory_dashboard/milestones.py` `get_milestone_detail` (how the `signoff` JSON is read) and `milestone_detail` with `_to_html` (how its sections become HTML); `factory_dashboard/templates/milestone.html` uses the headings below.
- Show only the keys `changed`, `how_to_test` and `decisions`, under the headings "What changed", "How to test" and "Decisions waiting for you", each only when present; then a link "The whole review" to `/milestones/<full key>` (keep the page's `q`).
- Show the block whenever the card's `milestones.signoff` is stored, with or without a thread, in `<section id="review">` between the card header and `#conversation`.
- With no thread yet, the reply box's label stays as it is.
- The desk's ripe item (`_ripe`) reads "reviewed · waits for your sign-off" instead of "every ticket merged · waits for your sign-off".
- The sheet's text is the lead's Markdown: render it only through `_to_html`, never `| safe` on raw text.

### Done when
- a card with a stored sheet and no thread: `#review` shows What changed and How to test with their text, and the link to its milestone page
- a sheet without `decisions` shows no "Decisions waiting for you" heading
- a card with no sheet has no `#review`
- the desk's ripe item reads "reviewed · waits for your sign-off"
- assert within `#review`, on its text with tags stripped and entities unescaped (`_text` in `tests/factory_dashboard/test_planning.py`)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
note: built by the lead in a terminal session (owner, 2026-10-08)
```
