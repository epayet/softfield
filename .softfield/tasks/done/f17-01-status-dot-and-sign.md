---
id: f17-01-status-dot-and-sign
milestone: f17-tighter-running-and-pause-presence-in
difficulty: 4
depends_on: [f12-03-remove-review-probe]
files:
  - factory_dashboard/app.py
  - factory_dashboard/templates/_partials/bar_status.html
  - factory_dashboard/templates/base.html
  - factory_dashboard/static/dashboard.css
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
The top bar's status becomes a dot (orange: the lead on a job, blue: a developer, grey: no job) and its Pause or Resume button a sign, ⏸ or ▶; on a phone only the dot and the sign show, beside the brand.

### Context
Read `factory_dashboard/app.py` (`class Status`, `def factory_status`), `factory_dashboard/templates/_partials/bar_status.html`, the top bar's script in `factory_dashboard/templates/base.html`, the `.factory-status` and `.pill.big` rules and the phone `.bar-top` grid in `factory_dashboard/static/dashboard.css`, and the top-bar tests in `tests/factory_dashboard/test_app.py` (`test_the_top_bar_says_what_the_factory_does_with_pause_or_resume` and the Playwright ones after it). The picture: `.softfield/cards/f17-mockup/top-bar.html`.
- `Status` gains the dot: `lead`, `developer`, `idle`, `waiting` or `stopped`. A live job whose role is in `DEVELOPER_ROLES` (`factory_dashboard/line.py`) is `developer`; any other live job (lead ticket, checkpoint, review, direction, escalation, the planner) is `lead`, paused or not. Waiting for Claude is `waiting`; no live run is `stopped`; else `idle`.
- The dot is about the job the words name: the first live job of `running_jobs`, the one "Running: …" and "Pausing after …" already read. While paused, only the planner counts: `lead` when it is live, else `idle` (the picture's two paused states; the branch has this right).
- Colours: `--opus` for the lead, `--copilot` for a developer (the floor's), `--muted` for idle; waiting is an `--opus` ring, stopped a `--muted` ring. The dot breathes slowly only while a job runs (`lead` and `developer`, not `waiting`), and not under `prefers-reduced-motion`.
- The words stay as they are, in the `role="status"` span: shown beside the dot from 640 px; under 640 px hidden, and the dot is a button that shows them on a tap (and as its `aria-label` and `title`).
- The sign keeps its 44 px target and says its action to a screen reader: `aria-label` "Pause after this job" or "Resume".
- What was asked shows at once as now: the dashed `--opus` edge, moved from the pill to `#factory-status`.

### The branch so far (the lead read it, 2026-10-10)
Your branch holds nearly all of it: the dot in `Status`, the template, the dashed edge on `#factory-status`, the tap on the dot, and the tests. Don't start again and don't re-read everything. What is left is small:
- The `layout` gate failed twice on `tests/factory_dashboard/test_probe_tmp.py`. That file was never yours: a review left it on main, and the direction you were given was wrong to call it your leftover. This ticket now waits for the ticket that removes it, so that gate is clean when you start.
- The phone sizes are the wrong way round. In the picture the dot's button and the sign are both 44 px by 44 px on a phone; 28 px (the dot's button) and 36 px (the sign) are its `.wide` sizes, for 640 px and up. The branch's phone block has `.dot-btn` at 28 px and `.sign` at 36 px.
- A 44 px sign does share the brand's row. Attempt 3 measured tops of 4 (the sign, 44 px tall) and 15.5 (the brand, about 21 px tall): their middles are both at 26. `test_phone_at_390px_all_share_one_row` compares tops, so it fails any two things of different heights; "one row" is the middles (`y + height / 2`) agreeing.
- Resume's `data-asked` on main is "Resuming…", the words the server then gives (`factory_status`). The branch says "Resuming from 11:40", which nothing else says.
- `_status` still names each button by its text (⏸, ▶), and the Playwright tests find the sign by its `.sign` class. The Done when asks for the `aria-label`: the name a screen reader says.
- `test_tapping_pause_shows_pausing_with_dashed_edge_at_once` repeats `test_pause_in_the_top_bar_shows_pausing_at_once_and_posts_a_pause`, which also checks the stored request. Keep one test for the tap on ⏸.
- `serve_lead` in `tests/factory_dashboard/conftest.py` leaves `write_live`'s developer job live beside its lead ticket, so the page says "Running: f1-04-live" under a lead's dot, and `_dot_for_job` grew a special case to make that pass. `serve_between()` gives a live run with no job; `_pause_held_planner` in `tests/factory_dashboard/test_app.py` shows a job started on a run of its own.
- `LEAD_ROLES` leaves out the checkpoints and the planner, and the rule doesn't need it: not in `DEVELOPER_ROLES` means `lead`.
- The dot's glow on the branch is two raw colours pasted from the picture (`rgba(255,150,64,.18)`, `rgba(122,167,255,.18)`). `dashboard.css` uses the tokens only, so the light theme can redefine them (`docs/agents/developer.md`, "Dashboard colours and fonts").
- Run `uv run pytest -x -q tests/factory_dashboard/test_app.py` plain, with nothing added after it, after each edit; then your finish line once.

### Done when
- each state of the parametrised test has its dot (`lead` for the planner while paused); its words are unchanged
- a live developer job gives `developer` and a live lead ticket gives `lead`, each the only live job in its test, with the words naming that same job
- the buttons are found by `aria-label`, show only ⏸ or ▶, and post the same `pause` or `resume`
- at 390 px the brand, the dot, the sign and the project select share one row (their middles within a few pixels), the dot's button and the sign are each 44 px by 44 px, and no words show until the dot is tapped
- at 1024 px the dot and the words show side by side
- tapping ⏸ still shows "Pausing after this job" with the dashed edge at once, and posts one `pause`; tapping ▶ shows "Resuming…"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: layout)
attempts: 3
tokens: 12701418
logs: .softfield/var/runs/20261010-085423/f17-01-status-dot-and-sign
```

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 588061
logs: .softfield/var/runs/20261016-071035/f17-01-status-dot-and-sign
```
