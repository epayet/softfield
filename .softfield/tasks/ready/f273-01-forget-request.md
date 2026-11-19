---
id: f273-01-forget-request
milestone: f273-i-need-the-ability-to-forget
difficulty: 2
depends_on: [f262-01-archive-a-project]
files:
  - runner/requests.py
  - runner/cli.py
  - factory_dashboard/requests.py
tests:
  - tests/runner/test_requests.py
agent: lead
---

### Goal
The owner can forget an archived project with a request, as `softfield forget` does in the terminal: it leaves every list, and nothing is deleted.

### Context
Read D1 to D4 of `.softfield/cards/f273-i-need-the-ability-to-forget.md`, then D1 to D3 of `.softfield/cards/f262-i-want-ability-to-archive-a.md`, which f262-01 built.
- f262-01's `archive_project` in `_apply` (`runner/requests.py`) is the example for the new kind `forget_project`; add it to `KINDS` in `factory_dashboard/requests.py`.
- `_forget` in `runner/cli.py` sets `paused` to `metrics.FORGOTTEN`; the request does the same with `metrics.set_project_paused`, and `_forget`'s printed words stay as they are.
- `metrics.is_archived(row)` (f262-01) says whether the project is archived.
- `state` in `runner/stacks.py` says whether a project's app runs; `stack_of` in `factory_dashboard/stacks_routes.py` shows how a project's stack is found from its row.

### Done when
- a `forget_project` request on an archived project sets its `paused` to "forgotten" and answers "forgotten: off every page; `softfield init` in its folder brings it back"; again, "already forgotten"
- on a project that isn't archived (running, paused or being set up), it answers "archive it first" and `paused` is unchanged
- on an archived project whose app is running, it answers "its app is running: stop it first" and `paused` is unchanged; a project without a stack is forgotten as usual
- no row of the project is deleted: its milestones, tickets, threads and owner items are all still there after the request
- the dashboard's `POST /requests` takes the kind
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
