---
id: f241-01-limit-pause-notifies
milestone: f241-i-want-a-notification-when-a
agent: lead
difficulty: 2
depends_on: []
files:
  - runner/notify.py
  - runner/loop.py
tests:
  - tests/runner/test_notify.py
  - tests/runner/test_loop.py
---

### Goal
When Claude's usage limit pauses a job, the runner sends one quiet phone notification saying until when the work waits, with the hours in brackets: "Claude's 5-hour limit: work waits until 22:30 (3 h)".

### Context
Read "What happens today" and D1 to D6 in `.softfield/cards/f241-i-want-a-notification-when-a.md`, then `send`, `to_owner` and `item_message` in `runner/notify.py`, `_notify` in `runner/loop.py`, and the branch of the job loop in `runner/loop.py` that starts at the comment "a limit (ADR 15 item 12)" (it records the refusal with `metrics.add_usage_event`, then gives up, parks or waits). `metrics.refusals` in `runner/metrics.py` lists the earlier refusals.
- In `runner/notify.py`: a function giving the body from the window (`five_hour`, `seven_day`, other or None), the resume time and now, as D2 says; and a `quiet` keyword on `send` and `to_owner` that adds the header `Priority: low` (D5). The other notifications don't change.
- In the job loop: when the refusal is certain and the agent's name starts with `claude`, read the earlier refusals before recording this one; unless one from the last 6 hours has a `resets_at` within 10 minutes of this one (D3), send the notification through `_notify`, quiet, opening the Overview (`notify.OVERVIEW`). Its time is `limit.resets_at`, or, with none, when the runner tries again (`now` plus `s.cfg.backoff_min`). Send it before giving up, parking or waiting, so all three notify.
- No owner item and nothing new stored (D1, D3).

### Done when
- a body for `five_hour` resetting 3 h 10 min from now reads "Claude's 5-hour limit: work waits until HH:MM (3 h)", with no weekday when the reset is today
- a body for `seven_day` resetting in 77 hours starts "Claude's week limit" and carries the weekday ("Mon 16:00 (77 h)"); one 40 minutes away ends "(40 min)"
- a certain Claude refusal sends one notification with the low priority, opening the Overview, whether the job then parks or waits
- a second refusal for a reset 2 minutes from the first's, within the hour, sends nothing; one for a reset 5 hours later sends again
- a refusal that isn't certain, an expired login and a refusal by a non-Claude agent send nothing
- with no `[notify] ntfy` set, nothing is sent and the job goes on as today
- the listed `tests:` pass, and fail without the change (tests replace `notify._post`, so nothing reaches the network)
- all gates pass (see `docs/workflow.md`)
