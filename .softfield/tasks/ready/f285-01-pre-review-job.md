---
id: f285-01-pre-review-job
milestone: f285-i-think-i-said-at-some
depends_on: []
agent: lead
difficulty: 4
area: factory
files:
  - runner/loop.py
  - runner/router.py
  - runner/prompts.py
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_router.py
---

### Goal
The runner can do a pre-review: Copilot reads one finished milestone, read-only, against its card, and files developer fix tickets for what it finds, its findings recorded for the review (ADR 51).

### Context
Read ADR 51 (`.softfield/adr/51-copilot-pre-reviews-while-claude-is-out.md`) and D1 and D4 in `.softfield/cards/f285-i-think-i-said-at-some.md`. Then in `runner/loop.py`: `stand_in_checkpoint` (the example to follow), `_read_only_review`, `_merge_files`, `fix_tickets`, `fix_ticket`, `record_findings`, `runner_commit`, `record_ticket`; in `runner/router.py`: `stand_in`, `lead_only`; in `runner/prompts.py`: `CHECKPOINT_STAND_IN`. Tests to follow: the stand-in checkpoint's in `tests/runner/test_loop.py` (search `stand_in_checkpoint`) and `stand_in` in `tests/runner/test_router.py`.
- `pre_review(s: Session, milestone: str) -> bool` takes the milestone to read; choosing it and when it runs are f285-02's. True when its job passed.
- `router.stand_in` gets a keyword `paced: bool = False`; the stand-in checkpoint keeps calling it as today.
- Copilot runs no git: the prompt lists paths (the card doc, each done ticket, each changed file), as `_merge_files` does.
- A written fix ticket the pre-review may not keep (`agent: lead`, or a file under `read_protected`) is deleted again before the commit; its findings keep route `report`.
- No `s.state.recheck` or `recheck_filed` change.

### Done when
- `router.stand_in(..., paced=True)` refuses Copilot past its month's pace line and allows it under; unpaced, it still allows up to the cap
- with a fake Copilot answer of two should-fix findings and one nit on a developer ticket of the milestone, `pre_review` writes one developer fix ticket in `.softfield/tasks/ready/`, records the three findings under `<milestone>-P<job id>-`, commits "pre-review of …", and returns True
- a finding whose fix ticket would be the lead's leaves no ticket in ready, and is recorded with route `report`
- a failed Copilot job returns False and writes nothing
- `state.recheck` is unchanged after a pre-review
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
