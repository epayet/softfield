---
id: f177-02-planner-resumes-only-warm
milestone: f177-planner-replies-cost-half-of-claude
agent: lead
difficulty: 2
depends_on: []
files:
  - runner/loop.py
  - runner/prompts.py
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_prompts.py
---

### Goal
Every planner reply starts a fresh Claude session holding the thread's history; none resumes the thread's session. (The id keeps its first name, from before D2 was revised.)

### Context
Read D2 and "What was found" in `.factory/cards/f177-planner-replies-cost-half-of-claude.md`, then `run_planner` in `runner/loop.py` (the `if not found["session_id"]:` block and `resume=`) and `planner.history` in `runner/planner.py`.
- Why: a resume hours later first writes the whole old session back into the prompt cache. Since 2026-10-13, 57 such replies cost $1.62 each; a fresh session starts from the brief and the thread's history. The owner chose one rule with no timer, so nothing depends on how long the cache lives.
- `earlier` is always the thread's history, built as for a thread with no session today (the `while said and said[-1]["author"] != "lead"` trim included), then the merged threads' histories (F49 D4) as today. `resume` is None.
- The thread still records the session it got (`set_thread_session` after the job): leave it.
- A job a usage limit cut off resumes through `state.interrupted`, not here: leave that path alone.
- What carries an investigation from one reply to the next is the card's doc (D2, revised 2026-10-30). `prompts.PLANNER` (card threads only, not `PLANNER_GENERAL`) gains one line in "How to answer": what you found and what you ruled out (the facts, the files and functions they come from, the numbers) goes in the card's doc under its plan, kept current, since the next reply starts a fresh session from that doc and the thread; check what the code says now before relying on it.

### Done when
- a planner job on a thread that has a session passes no `--resume`, and its prompt holds the thread's earlier messages
- a thread with merged cards unread still gets their histories once
- after the job, the thread's session is the new one
- a card thread's planner prompt holds the line about keeping findings in the card's doc once; the general thread's doesn't
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
