---
id: f21-03-trim-owner
milestone: f21-lead-briefs
difficulty: 2
depends_on: []
agent: lead
files:
  - docs/agents/owner.md
  - tests/runner/test_prompts.py
tests:
  - tests/runner/test_prompts.py
---

### Goal
`docs/agents/owner.md` holds each of the owner's preferences as one dated rule, without the stories behind them.

### Context
Read `.factory/cards/f21-lead-briefs.md` (D3, "As found (2026-10-28)") and `docs/agents/owner.md`.
- Set aside on 2026-10-28: the file is 1,802 words, not the 1,380 the ticket was planned on, because the owner added rules on 2026-10-13 and 2026-10-22. Cutting only the stories saves about 50 words, so no word target can be met without rewording rules, and rewording is the owner's to ask for.
- Bring it back only if the owner asks for a reworded owner.md; then their message sets the target and says whether rules may be merged or reworded.
- Keep every rule and its date, the headings and the order, so the owner can compare the diff. No word-count test: owner.md grows with each new preference, and a ceiling would block adding one.

### Done when
- every bold-titled rule of the old file is still there with its date, and a test in `tests/runner/test_prompts.py` checks that owner.md still has each of those bold titles
- the diff removes or rewords only what the owner's message allows
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: blocked
reason: the lead ticket changed nothing
```

```yaml
# --- runner ---
result: blocked
reason: the lead ticket changed nothing
```
