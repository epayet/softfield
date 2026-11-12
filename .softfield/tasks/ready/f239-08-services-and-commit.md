---
id: f239-08-services-and-commit
milestone: f239-i-want-to-be-able-to-3
agent: lead
difficulty: 2
depends_on: [f239-04-replan]
files:
  - runner/stacks.py
  - tests/runner/test_stacks.py
tests:
  - tests/runner/test_stacks.py
---

### Goal
The module that owns every Docker call also lists a stack's services and says which commit an update failed on, the two things the developers' logs page and app row need and can't add themselves (`runner/` is protected).

### Context
Read the `## Replan` log in `.softfield/cards/f239-i-want-to-be-able-to-3.md`, then `logs`, `state`, `_failed_update` and `_docker` in `runner/stacks.py`, and its existing tests.
- `services(stack) -> list[str]`: the names `docker compose -p <project> config --services` prints, through `_compose`, each checked as a service name; an empty list when Docker fails.
- `StackState` gets `commit: str = ""`, filled from the failed update's record, so `UPDATE_FAILED` carries the commit it failed on.

### Done when
- `services` returns the names a replaced `_docker` prints, and `[]` when it fails
- `state` of a stack whose last update failed holds that update's commit
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
