---
id: f276-01-the-bar-sees-setup-jobs
milestone: f276
difficulty: 3
depends_on: []
files:
  - factory_dashboard/app.py
tests:
  - tests/factory_dashboard/test_app.py
area: factory
---

## Goal
The top bar's status sees the lead's setup job (a project started from the Projects page): its dot is the lead's while it runs, paused or not, and its words say which project the lead is setting up.

## Context
- `factory_dashboard/app.py`: `factory_status` and `factory_wide_status`. While the owner's pause holds, only a live `planner` job lights the lead's dot (`"the lead is answering you"`), but the runner also runs `setup` jobs during the pause (`runner/dispatch.py`, `SETUP`), so the bar says "Paused by you since …" with no dot while the lead sets up a project.
- A running job with no ticket shows its raw role: "Running: softfield · planner, job 2502" (seen on the bar on 2026-11-19), and a setup job would read "setup, job N". The owner's rule is plain words, no internal names.
- Follow the cases in `tests/factory_dashboard/test_app.py` (`test_the_top_bar_says_what_the_factory_does_with_pause_or_resume`, fixture `_pause_held_planner`): add a fixture with a second project being set up (`metrics.SETTING_UP`) whose run has a live `setup` job.

## Done when
- Paused, with a live setup job on project X: the bar reads "Paused by you since 11:40 · the lead is setting up X", with the lead's dot and Resume; with both a planner and a setup job live, the planner's words win (it is the owner's conversation).
- Among several paused projects, the one whose lead dot is lit is the one the bar shows (today the first in the projects' order wins, dot or not).
- Not paused, a live setup job on X reads "Running: the lead is setting up X" (no " · X" added again in front), with the lead's dot, and Pause's words are "Pausing after the setup of X".
- Not paused, a live planner job reads "Running: <project> · the lead is answering you" (one project: "Running: the lead is answering you"), not "planner, job N".
- Every existing case of the test keeps its words and dot.
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 122019
logs: .softfield/var/runs/20261121-011446/f276-01-the-bar-sees-setup-jobs
```

```yaml
# --- runner ---
result: done
finished_by: lead
```
