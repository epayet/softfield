---
id: f149-01-reviews-stop-writing-a-backlog
milestone: f149-is-docs-backlog-md-still-used
difficulty: 3
depends_on: []
agent: lead
files:
  - runner/prompts.py
  - runner/milestone.py
  - runner/review.py
  - docs/workflow.md
  - docs/how-it-works.md
  - docs/agents/lead.md
  - docs/agents/owner.md
  - .softfield/cards/bugs.md
tests:
  - tests/runner/test_prompts.py
  - tests/runner/test_review.py
  - tests/runner/test_milestone.py
---

### Goal
No review or checkpoint, in any project, sends a finding to a backlog file: a finding worth a fix becomes a bug ticket set aside in `.softfield/tasks/later/`, and one not worth a run is said in the review report only (ADR 35).

### Context
Read `.softfield/adr/35-no-backlog-file.md` and `.softfield/cards/f149-is-docs-backlog-md-still-used.md` (What we know, D1–D3).
- `REVIEW` in `runner/prompts.py`: its `backlog:` route line becomes the `later` and `report` routes of ADR 35 items 1–2; a `later` ticket is shaped as D3 says, and runs `softfield check-tickets <its files>` like a `local` one. f164-01 (ready) also edits `REVIEW`, the "6. What next" sentence: leave that sentence to it.
- `CHECKPOINT`, `CHECKPOINT_SHADOW`, `CHECKPOINT_STAND_IN`: `"backlog"` becomes `"report"` (ADR 35 item 4).
- `_fix_scope` in `runner/milestone.py`: "go to the backlog" (twice) becomes the `later` or `report` route.
- `ROUTES` and `_finding`'s default in `runner/review.py`: D1.
- The docs: every line naming the backlog in `docs/workflow.md` (Discoveries, Milestone review loop, Report), `docs/how-it-works.md`, `docs/agents/lead.md` ("Left for later"), `docs/agents/owner.md` ("never a parked backlog item": "never a parked note"), `.softfield/cards/bugs.md` ("Where bugs come from"). Leave `docs/backlog.md` itself to f149-02.

### Done when
- `REVIEW` asks for `later` (a set-aside bug ticket with `finding:`) or `report`, and names no backlog
- the checkpoint prompts and `_fix_scope` name no backlog
- `ROUTES` holds `later` and `report`, still reads `backlog` from an old file, and a finding with no route reads as `report`
- a test in `tests/runner/test_prompts.py` fails if "backlog" appears in any prompt of `runner/prompts.py` or in `_fix_scope`'s text
- no file listed above names `docs/backlog.md`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
