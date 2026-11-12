---
id: f239-01-run-config-and-stacks
milestone: f239-i-want-to-be-able-to-3
agent: lead
difficulty: 6
depends_on: []
commands: [docker compose version, docker info]
files:
  - runner/config.py
  - runner/stacks.py
  - tests/runner/test_stacks.py
tests:
  - tests/runner/test_stacks.py
---

### Goal
A project's `[run]` table is read, and `runner/stacks.py` starts, stops, reads the state and the logs of its app's Docker Compose stack, from a checkout of main of its own.

### Context
Read ADR 46 in `.softfield/adr/46-run-a-project-from-the-dashboard.md` and D1 to D4 in `.softfield/cards/f239-i-want-to-be-able-to-3.md`; they fix the functions, paths and file shapes. Follow `project_shots` in `runner/config.py` for `project_run`, and `update_live` and `softfield_repo` in `runner/loop.py` for the detached worktree and for telling Softfield apart (`stack_for` returns None for it).
- `state` reads `docker compose -p <project> ps --all --format json`: no containers is stopped; the main service up and healthy (or without a health check) is running; created, restarting or health starting is starting; exited with a non-zero code, or restarting more than 3 times, is crashed; the last update's result file with `ok: false` for the checkout's commit is update failed, whatever the containers say. `url_port` is the main service's published host port.
- `start` creates the checkout if it is missing (`git worktree add --detach` at main), then `up -d`; `stop` runs `stop`. Both take the lock file of D3 and give up with a plain error if it is held for more than 60 s.
- Docker missing, or the user without access to it, is a `StackState` of its own with the reason in `detail`, never an exception.
- D9: run `docker compose version` and `docker info` once on this machine. If either fails, finish the ticket anyway (no test needs Docker) and end your last message with "Docker: <what failed>, for the owner to fix".

### Done when
- `project_run` returns None without `[run]`, defaults `path` to `/`, and raises `ConfigError` without `service`
- `stack_for` is None for Softfield's own repo and for a project without `[run]`
- each state word of the second bullet above comes out of a recorded `ps` output in the tests
- `start` on a project with no checkout creates it at main, and every Compose call carries `-p <project>` and `APP_DATA` set to the data folder of D3
- no test runs the real `docker`: every call goes through `_docker`, replaced in the tests
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
