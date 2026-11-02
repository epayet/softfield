---
id: f85-01-pictures-at-the-review
milestone: f85-when-i-sign-off-a-task
agent: lead
difficulty: 7
depends_on: []
files:
  - runner/shots.py
  - runner/milestone.py
  - runner/config.py
  - .softfield/project.toml
tests:
  - tests/runner/test_shots.py
  - tests/runner/test_milestone.py
---

### Goal
Before each review round of a card whose doc lists pages under `## Before and after`, in a project whose `.softfield/project.toml` has `[shots]`, the runner starts that project's app on sample data and saves a picture of each page as it was at the card's start and as it is on main, on a phone and on a wide screen. Softfield gets its own `[shots]`.

### Context
Read ADR 40 in `.softfield/adr/40-pictures-at-sign-off-in-every-project.md` (it must be Accepted; it was ADR 35 until 2026-10-29, see "Blocked on 2026-10-29" in the card) and D1 to D6 and D9 in `.softfield/cards/f85-when-i-sign-off-a-task.md`. Then `review_milestone` in `runner/milestone.py` (where the base `<key>-start` comes from), how `.softfield/project.toml` is read (`project_checks` and its neighbours in `runner/config.py`), the `dashboard` command in `runner/cli.py` (`--port`, `--db`), and the browser tests' Playwright use in `tests/factory_dashboard/test_overview.py` (`open_overview`).
- `runner/shots.py` owns `pages(doc_text) -> list[str]` (the backticked addresses under `## Before and after`, in order; none without the section) and the picture-taking. `[shots]` is read with the project's other settings: `prepare`, `serve` (with `{port}`), `ready`, and an optional `live` (a base address the dashboard links to, D7; never used for pictures); a project without it gets no pictures and no folder.
- `prepare` runs once per round that takes pictures, in the repo, with `SOFTFIELD_SHOTS_DATA` set to a new temporary folder. `serve` runs in the tree being pictured (the repo for the after; for the before, once per review, a `git worktree add --detach` of `<key>-start` in a temporary folder) on a free port of 127.0.0.1, with the same variable. The current `[shots]` commands serve both trees.
- Wait for `ready` to answer (with a time limit), picture each address, then stop the server and its children. Remove the worktree and the data folder after, a failure included.
- The browser lets only GET requests to `127.0.0.1:<port>` through: any other method or host is aborted.
- Phone is 390 px wide, wide 1440 px, full page. File names and the list file as D5 says, in the reviewed project's `.softfield/var/shots/<key>/`.
- Nothing may stop the review: an address the old code answers 404 is recorded as didn't exist before; any other failure (the server won't start, a 500, a time limit, Chromium missing) is recorded with its reason, and the round goes on. Log one line saying how many pictures were taken.
- Softfield's `[shots]` (D4): `prepare` copies the metrics database into the data folder; `serve` starts the dashboard from the tree on that copy, so the before runs the old dashboard. Prove it on this repo once by hand and say in the ticket's commit what the pictures showed.
- The test that takes real pictures is marked like the other browser tests and uses a tiny app of its own as `serve`; the parsing, the GET-only rule, the file names and the failure records are plain tests.

### Done when
- `pages` reads the addresses under `## Before and after` in order, and returns none for a doc without the section
- a review round of a card listing two pages, in a project with `[shots]`, leaves `before-phone-1.png`, `before-wide-1.png`, `after-phone-1.png`, `after-wide-1.png` (and the same for 2) and a list file naming both addresses
- a second round takes the after again and leaves the before as it was
- an address the start tag's code answers 404 is recorded as didn't exist before, with no before picture; the after is taken
- a server that doesn't start is recorded with its reason, and the round runs
- a project without `[shots]`, or a card without the section, gets no folder, and its review runs as today
- a POST from a pictured page, and a request to another host, never reach anything
- no server, worktree or data folder is left behind, after a failure too
- Softfield's `.softfield/project.toml` has `[shots]`, and pictures of `/` can be taken with it
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: blocked
reason: the lead ticket changed nothing
```
