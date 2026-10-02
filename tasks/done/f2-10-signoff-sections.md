---
id: f2-10-signoff-sections
milestone: f2
depends_on: []
difficulty: 3
files:
  - runner/milestone.py
  - factory_dashboard/templates/milestone.html
tests:
  - tests/runner/test_milestone.py
  - tests/factory_dashboard/test_milestones.py
---

### Goal
The milestone page shows the whole sign-off sheet, including "Decisions waiting for you" and "What clogged the factory line".

### Context
Read `docs/agents/lead.md` ("Sign-off sheet": seven numbered sections), `runner/milestone.py` (`SIGNOFF_SECTIONS`, `signoff_sections`, `_SUBHEADING_RE`), `factory_dashboard/templates/milestone.html` and the tests `test_milestone_detail_shows_signoff_parts_by_text` (in `tests/factory_dashboard/test_milestones.py`) and the `signoff_sections` tests in `tests/runner/test_milestone.py`. `docs/reviews/f1.md` is a real sheet with all seven.
- `SIGNOFF_SECTIONS` maps five headings today. Add "Decisions waiting for you" → `decisions` and "What clogged the factory line" → `clogged`.
- On the page, in the sheet's order: What changed, How to test, Decisions waiting for you, What next, Left for later, How the work went, What clogged the factory line. Each one shows "Not written yet" when missing, like the others.
- `factory_dashboard/milestones.py` already passes every key of the stored sheet to the template; check it, don't change it unless a key is filtered out.
- The sheet reaches the database at a review and on `uv run runner backfill`; the lead also made each run and `runner signoff` record it.

**The dashboard is English-only and never writes the database.**

### Done when
- `signoff_sections` on a review with all seven headings returns all seven keys
- the milestone page shows the two new sections' text, and "Not written yet" without them
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
merged_by: the lead, interactively with the owner (2026-10-02)
```
