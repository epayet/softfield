---
id: f177-02-planner-resumes-only-warm
milestone: f177-planner-replies-cost-half-of-claude
agent: lead
difficulty: 3
depends_on: []
files:
  - runner/loop.py
  - runner/metrics.py
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_metrics.py
---

### Goal
A planner reply resumes its thread's Claude session only while the prompt cache still holds it; later, it starts a fresh session with the thread's history.

### Context
Read D2 and "What was found" in `.factory/cards/f177-planner-replies-cost-half-of-claude.md`, then `run_planner` in `runner/loop.py` (the `found["session_id"]` checks and `resume=`), `planner.history` in `runner/planner.py`, and `set_thread_session` in `runner/metrics.py`.
- The cache lives about an hour: a resume 25 minutes after the last reply read 97k tokens from it and wrote 8k; one the next day wrote 239k back ($1.92) before doing anything. Since 2026-10-13, cold resumes cost $1.65 a reply, warm ones $0.45.
- `PLANNER_WARM_S = 55 * 60` in `runner/loop.py`. A small `metrics` query gives when a session's last job ended (`jobs.ended`, by `session_id`).
- Warm (ended under `PLANNER_WARM_S` ago): resume as today. Cold, or no end recorded: no `resume`, and `earlier` is the thread's history exactly as for a thread with no session (the `while said and said[-1]["author"] != "lead"` trim included). The merged threads' histories (F49 D4) are added in both cases, as today. The new session's id replaces the thread's, as `set_thread_session` already does after the job.
- A job a usage limit cut off resumes through `state.interrupted`, not here: leave that path alone.

### Done when
- a planner job whose thread's session ended 10 minutes ago passes `--resume` with that session and no history
- one whose session ended 2 hours ago passes no `--resume`, and its prompt holds the thread's earlier messages
- after the cold job, the thread's session is the new one
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
