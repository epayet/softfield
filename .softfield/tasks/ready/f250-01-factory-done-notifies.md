---
id: f250-01-factory-done-notifies
milestone: f250-i-want-a-notification-when-the
agent: lead
difficulty: 3
depends_on: [f241-01-limit-pause-notifies]
files:
  - runner/notify.py
  - runner/loop.py
tests:
  - tests/runner/test_notify.py
  - tests/runner/test_loop.py
---

### Goal
When no project can start anything on its own for 12 hours or more, `softfield run` sends one phone notification saying so and until when: "Done until Mon 16:00 (51 h): Claude's week is used up. You can switch off."

### Context
Read "What happens today" and D1 to D4 in `.softfield/cards/f250-i-want-a-notification-when-the.md`. Then, in `runner/loop.py`: `run_projects` and `project_round` (the round over every project), `work_queue`'s branch where `job is None` without `wait` (it sets the idle line), `_idle_line`, `_lead_tickets_passed_over`, `_resets` and `s.state.parked`; and in `runner/notify.py`: `send` and the body function f241-01 added for F241 D2's time words (the weekday when not today, the hours in brackets, minutes under an hour).
- `claude_resumes(s, ready, paused, held)` in `runner/loop.py` (D2): the earliest moment Claude-held work of this session could start (the parked tickets' resets not yet due, and the "until" `_lead_tickets_passed_over` computes), or None when Claude holds nothing. `_idle_line` uses it, so its words don't change.
- `notify.done_message(resumes, now, *, reserve, waiting)` (D3): the body; `resumes` None means "All work done: nothing is ready."; `reserve` true when only the reserve passes lead work over; `waiting` the count of open owner items across projects.
- In `run_projects`: after a round where no job ran, decide D1 across every live session; once it has held 10 minutes in a row, send it once with `notify.send("Softfield", …, notify.OVERVIEW)`, its failure noted in a session's report as `_notify` does; a round where a job ran re-arms it (D4). Nothing is stored.
- The single-project `runner run` (`work_queue` with `wait`) doesn't notify: only the command that serves every project sees the whole factory.

### Done when
- two projects, one with lead tickets parked for Claude's week resetting in 51 hours and developer tickets depending on them, the other with no ready ticket: after 10 minutes of rounds where nothing ran, one notification "Done until <weekday> HH:MM (51 h): Claude's week is used up. You can switch off.", titled "Softfield", opening the Overview; further idle rounds send nothing more
- the same with two open owner items: the body ends " · 2 things wait for you"; with one, " · 1 thing waits for you"
- lead work held only by the week's reserve reads "Claude's week is down to your reserve"
- every project with no ready ticket and no queued job: "All work done: nothing is ready. You can switch off."
- nothing is sent when the earliest Claude resume is under 12 hours away (a 5-hour reset), when the work left waits only for the owner, while the owner's pause is on, or before 10 minutes have passed; a job running in between re-arms it, and the next rest sends again
- `_idle_line`'s words are unchanged for the same state (its existing tests pass as they are)
- with no `[notify] ntfy` set, nothing is sent and the runner goes on as today
- the listed `tests:` pass, and fail without the change (tests replace `notify._post`, so nothing reaches the network)
- all gates pass (see `docs/workflow.md`)
