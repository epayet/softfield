---
id: f72-01-mockup-by-default
milestone: f72-i-really-like-the-mock-up
depends_on: []
agent: lead
difficulty: 2
files:
  - runner/prompts.py
  - docs/agents/lead.md
  - docs/agents/owner.md
tests:
  - tests/runner/test_prompts.py
---

### Goal
A card that changes how a page looks gets a Today/Proposed mock-up in the lead's first planning reply, without the owner asking.

### Context
Read F72's Decisions D1–D4 in `docs/milestones/f72-i-really-like-the-mock-up.md`, `PLANNER` in `runner/prompts.py`, `tests/runner/test_prompts.py`, the "Planning room" section of `docs/agents/lead.md` and "Mock-ups before UI tickets" in `docs/agents/owner.md`. The example of a Today section: `docs/milestones/f17-mockup/top-bar.html`.
- The owner (2026-10-09): "I really like the mock up feature, especially to see before/after change. This should be the default for frontend features".
- Add the paragraph to `PLANNER` only (in the part after `_PLANNER_HEAD`), not to `PLANNER_GENERAL`: the general thread drafts nothing.

### Done when
- `PLANNER` says: a card that changes what a page shows or how it is laid out gets a mock-up (D1, with the exceptions and "say why in a point" when skipped); one file with a Today / Proposed switch, Today copied from the live template and CSS, changes marked, real values (D2); the mock-up and the plan in the same reply, UI tickets naming the mock-up in Context (D3).
- A test in `tests/runner/test_prompts.py` checks that `PLANNER` carries "Today", "Proposed" and the mock-up's folder in that paragraph, and that `PLANNER_GENERAL` doesn't ask for a mock-up.
- `lead.md`'s Planning room gets one line on it; `owner.md`'s "Mock-ups before UI tickets" is widened to D1, dated 2026-10-09. Keep both short.
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
