---
id: f85-05-fix-slow-page-still-pictured
milestone: f85-when-i-sign-off-a-task
agent: lead
difficulty: 3
depends_on: []
files:
  - runner/shots.py
  - runner/config.py
  - .softfield/project.toml
  - runner/instructions/bootstrap.md
tests:
  - tests/runner/test_shots.py
---

### Goal
A page that takes more than a few seconds to draw still gets its picture: the runner stops asking the app whether it is ready, and takes the picture once the app's port takes a connection.

### Context
Read D3, D6 and D11 and "F219's After that wasn't drawn" in `.softfield/cards/f85-when-i-sign-off-a-task.md`, and the Amendments of `.softfield/adr/40-pictures-at-sign-off-in-every-project.md`. Then `_answers` and `_serving` in `runner/shots.py`, and `Shots` and `project_shots` in `runner/config.py`.
- `_serving` waits, up to `READY_LIMIT`, for a plain connection to the port to succeed: no HTTP request, so nothing is left running in the app. `PAGE_LIMIT` then decides each picture, as it does now. `softfield dashboard` runs with `reload=True`, whose parent opens the port before the app has loaded: a request made in that gap waits for the app, inside `PAGE_LIMIT`.
- `ready` goes from `Shots`, from `[shots]` in `.softfield/project.toml` and from `runner/instructions/bootstrap.md` (which then says to check that the page renders). A `ready` left in a project's file is ignored, not an error. Only Softfield has set `[shots]`.
- Reasons (D11): the app never opening its port says `the app didn't open its port in 180 s`, with no output quoted; the app stopping by itself keeps its code and the tail of its output. So the page never shows the app's own start-up line.
- The test uses a tiny app whose page takes longer than the old 5 s check, as the other tests in `tests/runner/test_shots.py` serve theirs.
- Once built, take the pictures of `/` on this repo once, on the real data (`take` in `runner/shots.py` with a card that lists `/`, in a throwaway folder if needed), and say in the commit how long `/` took and whether the After came out: that confirms the cause on the card, which was timed by hand.

### Done when
- a page that takes 8 s to answer gets its pictures, and the app receives one request per picture, none from a readiness check
- an app that never opens its port is recorded with `the app didn't open its port in 180 s` (the limit's value) and none of its output
- an app that stops by itself is recorded with its code and the tail of its output
- `project_shots` reads a `[shots]` with no `ready`, and one with a leftover `ready`, to the same result; a missing `prepare` or `serve` is still refused
- `.softfield/project.toml` has no `ready`, and pictures of `/` come out on this repo
- the listed `tests:` pass, and fail without the change
- all gates pass (see `runner/instructions/workflow.md`)
