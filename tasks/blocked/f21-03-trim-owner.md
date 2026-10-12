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
priority: 0
---

### Goal
`docs/agents/owner.md` holds each of the owner's preferences as one dated rule, without the stories behind them, in under 800 words.

### Context
Read `docs/milestones/f21-lead-briefs.md` (D3) and `docs/agents/owner.md`.
- Keep every rule and its date. Drop the incident that taught it ("two of the first answers that night were wrong until…"): if it isn't already in a milestone or review doc, leave it out, don't move it.
- Keep the headings and the order, so the owner can compare the diff.
- **No rule is dropped or changed in meaning: when unsure, keep the sentence.**

### Done when
- `docs/agents/owner.md` is under 800 words, and a test in `tests/runner/test_prompts.py` keeps it so (every lead job pays for each word)
- every bold-titled rule of the old file is still there with its date
- the diff removes only explanations, examples and history, never a "do" or "don't"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: blocked
reason: the lead ticket changed nothing
```
