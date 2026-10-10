---
id: f17-01-status-dot-and-sign
milestone: f17-tighter-running-and-pause-presence-in
difficulty: 4
depends_on: []
files:
  - factory_dashboard/app.py
  - factory_dashboard/templates/_partials/bar_status.html
  - factory_dashboard/templates/base.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
The top bar's status becomes a dot (orange: the lead on a job, blue: a developer, grey: no job) and its Pause or Resume button a sign, ⏸ or ▶; on a phone only the dot and the sign show, beside the brand.

### Context
Read `factory_dashboard/app.py` (`class Status`, `def factory_status`), `factory_dashboard/templates/_partials/bar_status.html`, the top bar's script in `factory_dashboard/templates/base.html`, the `.factory-status` and `.pill.big` rules and the phone `.bar-top` grid in `factory_dashboard/static/dashboard.css`, and the top-bar tests in `tests/factory_dashboard/test_app.py` (`test_the_top_bar_says_what_the_factory_does_with_pause_or_resume` and the Playwright ones after it). The picture: `docs/milestones/f17-mockup/top-bar.html`.
- `Status` gains the dot: `lead`, `developer`, `idle`, `waiting` or `stopped`. A live job whose role is in `DEVELOPER_ROLES` (`factory_dashboard/line.py`) is `developer`; any other live job (lead ticket, checkpoint, review, direction, escalation, the planner) is `lead`, paused or not. Waiting for Claude is `waiting`; no live run is `stopped`; else `idle`.
- Colours: `--opus` for the lead, `--copilot` for a developer (the floor's), `--muted` for idle; waiting is an `--opus` ring, stopped a `--muted` ring. The dot breathes slowly only while a job runs, and not under `prefers-reduced-motion`.
- The words stay as they are, in the `role="status"` span: shown beside the dot from 640 px; under 640 px hidden, and the dot is a button that shows them on a tap (and as its `aria-label` and `title`).
- The sign keeps its 44 px target and says its action to a screen reader: `aria-label` "Pause after this job" or "Resume".
- What was asked shows at once as now: the dashed `--opus` edge, moved from the pill to `#factory-status`.

### Done when
- each state of the parametrised test has its dot (`lead` for the planner while paused); its words are unchanged
- a live developer job gives `developer` and a live lead ticket gives `lead` (add the one the fixture lacks)
- the buttons are found by `aria-label`, show only ⏸ or ▶, and post the same `pause` or `resume`
- at 390 px the brand, the dot, the sign and the project select share one row, and no words show until the dot is tapped
- at 1024 px the dot and the words show side by side
- tapping ⏸ still shows "Pausing after this job" with the dashed edge at once, and posts one `pause`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: layout)
attempts: 3
tokens: 12701418
logs: var/runs/20261010-085423/f17-01-status-dot-and-sign
```
