---
id: f286-01-review-looks-for-simpler
milestone: f286-i-want-code-reviews-to-highlight
difficulty: 3
depends_on: [f280-01-package-names-no-project]
agent: lead
files:
  - runner/prompts.py
  - runner/instructions/lead.md
  - docs/workflow.md
  - tests/runner/test_prompts.py
tests:
  - tests/runner/test_prompts.py
---

### Goal
Every milestone review looks for complexity after correctness and routes it by the Boy Scout rule, suggests the features that follow from what it built, treats Softfield as the product in Softfield's own reviews, and checks no project's language but its own; every plan names what a new mechanism reuses or retires (ADR 52 items 1–3 and 5–8).

### Context
Read `.softfield/adr/52-a-review-leaves-the-code-simpler.md` and `.softfield/cards/f286-i-want-code-reviews-to-highlight.md` (D1–D3, D5). Write the tests first. F280's ticket, before this one, already reworded `lead.md`'s French line and the sign-off sheet: build on it, don't redo it.
- `REVIEW` in `runner/prompts.py`: after the grading lines, add what to look for (item 1) and how to route it (items 2 and 3): the milestone's own complexity is a should-fix; older complexity in the files it touched is at most two `> Simpler: …` lines under "6. What next".
- `REVIEW`'s "6. What next" heading line: at most two quoted feature ideas that follow from the milestone's work (item 6); on the factory's own project, no Product bullet and everything under Factory (item 7). The `{…}` fields the runner fills already tell you whether the project is the factory, or add one beside them in `runner/prompts.py` only.
- `REVIEW`: remove "Check the French." (item 8). `docs/workflow.md` "Milestone review loop" step 1: remove "and the French" the same way.
- The planner's brief (`_PLANNER_HEAD` and what follows it in `runner/prompts.py`): one sentence for item 5.
- `runner/instructions/lead.md` "Review" and `docs/workflow.md` "Milestone review loop": one bullet each for items 1–3 and 6–7, citing ADR 52. Keep `lead.md` short.

### Done when
- `REVIEW` names the kinds of complexity of ADR 52 item 1, says the milestone's own is a should-fix, and asks for at most two quoted lines starting "Simpler:" about older code in the files the milestone touched
- `REVIEW` asks for at most two quoted feature ideas following from the milestone's work
- the review brief built for the factory's own project says Softfield is the product and has no Product bullet; the one built for another project keeps Product and Factory
- neither `REVIEW` nor `docs/workflow.md` mentions French
- the planner's brief asks a plan that adds a mechanism to name in its Decisions what it builds on and what it makes removable
- `lead.md` "Review" and `docs/workflow.md` "Milestone review loop" carry the rules once each, citing ADR 52
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
