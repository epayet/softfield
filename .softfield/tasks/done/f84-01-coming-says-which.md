---
id: f84-01-coming-says-which
milestone: f84-when-the-planner-is-replying-to
difficulty: 3
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/planning.html
  - factory_dashboard/templates/thread.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
In the Planning room, only the thread the lead is answering says it is being written; every other waiting thread says its place in line and about when its reply comes, and the "The factory now" tile names the reply being written.

### Context
Read `.softfield/cards/f84-when-the-planner-is-replying-to.md` ("What happens today", then D1–D6). The picture to build is `.softfield/cards/f84-mockup/coming-says-which.html` (Proposed).
- `_next_reply`, `_typical`, `_held`, `coming` (the threads waiting for the lead) and `factory_now` are in `factory_dashboard/planning.py`; the thread page passes `next_reply` to `factory_dashboard/templates/thread.html` (`#waiting`).
- A running planner job's queue row has `started_job` set to the job's id; its `subject` is `<thread>#<message>` and its `reason` says what it is for ("your message on F84", "a ticket blocked on F132"). `queued_jobs` in `factory_dashboard/overview.py` shows how to leave out a started row and order the rest with `dispatch.plan`.
- A thread's title for the tile comes from `_card_titles` and `_thread_title`, as Coming already does.
- The "Writing now" label and the left edge use the `--opus` token in `factory_dashboard/static/dashboard.css`; add a class there rather than more inline style.

### Done when
- with a planner job running on f84 and planner rows waiting for f85 and f86: Coming lists f84 first with "Writing now" and "the lead is writing this reply · … in"; f85 reads "next, after F84's reply · about …"; f86 reads "3rd in line · about …"
- no Coming box nor thread page says "writing" for a thread whose row has not started
- a running planner job whose queue row's reason starts "a ticket blocked on" reads "the lead is looking at the blocked ticket"
- with a ticket job running and no planner job, the first waiting thread reads "next, after <ticket id> · …" as today, the second "2nd in line · …"
- f86's thread page shows "Next for the lead · 3rd in line · about …"; f84's shows the "writing this reply" words
- the tile reads "Writing now: F84, <title>" with F84 linked to `/planning/f84`, and "Then 2 replies in line, about …" under it
- a reply held for a Claude limit, and a plant with no queue row yet, read as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 1091417
logs: .softfield/var/runs/20261027-005355/f84-01-coming-says-which
```
