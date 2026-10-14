---
id: f6-11-planning-requests
milestone: f6-planning-room
depends_on: [f6-05-replan]
agent: lead
difficulty: 3
files:
  - factory_dashboard/requests.py
  - runner/planner.py
tests:
  - tests/factory_dashboard/test_requests.py
  - tests/runner/test_planner.py
---

### Goal
The dashboard may ask for the planning room's five requests, and can read a card's draft (a mock-up, an ADR) from its plan branch, so f6-06 to f6-08 can be built on them.

### Context
Read D1, D4 and the Replan section in `docs/milestones/f6-planning-room.md`, `factory_dashboard/requests.py` (protected), `runner/requests.py` (the kinds' constants), `runner/planner.py` (`thread_key`, `plan_branch`, `is_draft`) and `docs/security.md`. Test-first; isolation tests for the protected file.
- **`POST /requests`:** `KINDS` gains `plan_message`, `plant`, `send_back`, `accept_adr` and `approve_plan`, with the same guard as today. The runner checks each value (`runner/requests.py`); the route stays a plain row write.
- **`planner.draft(repo, thread, path) -> bytes | None`:** the file at `path` on `plan/<thread>` while that branch exists, else on main; None when there is none.
  - It reads git, never the working tree: the runner checks the plan branch out during planner jobs.
  - It refuses (None) a path that isn't a draft (`is_draft`) and a thread `thread_key` refuses, so nothing outside `docs/` and `tasks/later/` is ever read through it.

### Done when
- each of the five kinds posted from the dashboard's own page writes one row; a foreign `Origin` still gets 403 for them
- `draft` returns a file only on the plan branch while it exists, main's after, and None for `runner/x.py`, `docs/../x` and a thread like `../x`
- `uv run runner check-all --task f6-11-planning-requests` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
