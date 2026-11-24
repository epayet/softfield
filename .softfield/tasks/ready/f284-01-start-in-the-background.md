---
id: f284-01-start-in-the-background
milestone: f284-i-find-the-docker-run-buttons
agent: lead
difficulty: 4
depends_on: []
files:
  - runner/stacks.py
  - factory_dashboard/stacks_routes.py
  - .softfield/cards/f284-i-find-the-docker-run-buttons.md
tests:
  - tests/runner/test_stacks.py
  - tests/factory_dashboard/test_stacks_routes.py
---

### Goal
Run and Stop answer at once, and what the app is doing is written down, so a refresh, a dashboard reload or a second press shows the start under way instead of losing it.

### Context
Read "What happens today" and D1 to D5 in `.softfield/cards/f284-i-find-the-docker-run-buttons.md`, then `start`, `stop`, `follow_main`, `_locked` and `state` in `runner/stacks.py`, and `run_app`, `stop_app`, `STATE_WORDS` and `UP` in `factory_dashboard/stacks_routes.py`.
- Test first, with `_docker` replaced as the existing tests in `tests/runner/test_stacks.py` do: no test starts Docker, and none waits on a real child process (replace the launch too).
- D2's record `run/<project>.doing.json` is written right after the lock is taken and removed in the same `finally` that lets it go, by `start`, `stop` and `follow_main` alike (`follow_main` only when it rebuilds). Add its path to `Stack` beside `lock_file`, and `build_log` for D4.
- D3: `STOPPING = "stopping"` and `UPDATING = "updating"` join the words; `state` reads the record before `ps` (a dead `pid` is ignored, and the stale file may be removed). `STATE_WORDS` gets "Stopping" and "Updating"; `UPDATING` joins `UP` (the old app still runs); `STOPPING` doesn't. `StackState` gets `busy: bool`, true only when the state comes from a live record: a container still in its health check stays `STARTING` from `ps`, not busy.
- D4: `up -d --build` streams into `build_log` (stdout and stderr together), still bounded by `DOCKER_TIMEOUT`; a failed start keeps its tail in the result file as today. `build_lines(stack, lines=40) -> str` returns the end of `build_log`, "" without one.
- D1: `begin(stack, doing)` (`"start"` or `"stop"`) launches this same Python on `runner/stacks.py`'s own entry (`python -m runner.stacks start|stop <repo>`, with `sys.executable`, `start_new_session=True`, output to `build_log` for a start) and returns at once. The child takes the lock; when another command holds it, it ends without doing anything (D5), not after 60 s.
- D5: `run_app` and `stop_app` keep the guard and the 404s; when `state(stack).busy`, they answer the row as it is and launch nothing; otherwise they call `begin` and answer `app_row`, which now reads the record and so shows the busy word.
- Log in the card doc, under "## As built", anything a later ticket (f284-02, f284-03) must know that D2 to D4 don't say: the field names as built, the module entry's command line.

### Done when
- a test shows `run_app` returns before the start's `up` ends, and the row it answers says "Starting"
- with a `start` record whose `pid` is alive, `state` says starting and `busy`, whatever `ps` says; with a dead `pid` it says what `ps` says
- a second Run while a record says start launches nothing and answers the same busy row
- `follow_main` writes an `update` record while it rebuilds and removes it after, also when the build fails
- `build_lines` returns the last lines of the streamed build output, and "" when there is none
- the guard still answers 403 before anything runs, and an unknown project 404
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
