---
id: f106-06-red-main-blocks-nothing
milestone: f106-where-do-blocked-tickets-go-for
difficulty: 6
depends_on: [f106-01-blocked-reaches-the-owner]
agent: lead
files:
  - runner/loop.py
  - runner/checks.py
  - docs/workflow.md
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_checks.py
---

### Goal
A ticket whose checks fail only where main fails too is not blocked: the run stops once, says main is red and what would fix it, and the ticket's work waits on its branch.

### Context
Read `.factory/cards/f106-where-do-blocked-tickets-go-for.md` (D5 and "What happened on 2026-10-12"), `.factory/adr/29-the-lead-looks-at-a-blocked-ticket.md` (item 7), then `run_lead_task`, `block`, `_check_all`, `_recover` and `work_queue` in `runner/loop.py`, and `check_all` in `runner/checks.py`. `runner/**` is protected: write the tests first, each failing for the right reason.
- On 2026-10-12 a scratch file on main failed the `layout` gate. Four lead tickets finished their work, passed every other check and were blocked one after the other, about $10 of Opus, while the ticket that removed the file waited behind them.
- **The test:** when a lead ticket's `check-all` fails, the runner runs the checks that failed, and only those, on main. Main failing every one of them means main is red.
- **Main is red:** the ticket stays in `.factory/tasks/ready/`, its branch is kept and its next run builds on it (as an interrupted lead job's does, `state.interrupted`), never restarted from main. The runner stores one owner item of kind `main-red` (subject the first failing check, text its first lines and, when a ready ticket's `files:` names the failing file, that ticket's id) and takes no other lead ticket until main passes; developer tickets go on, as their gates already compare with main.
- **Main passes them:** the ticket is blocked as today.
- The item resolves when a later `check-all` on main passes those checks.
- **No check is skipped or loosened: a ticket still merges only when its whole `check-all` passes.**

### Done when
- a lead ticket whose `check-all` fails on a check main fails too: it is still in `.factory/tasks/ready/`, `task/<id>` holds its work, an open `main-red` item names the check, and the pick takes no other lead ticket
- its next run, once main passes, starts from its branch and merges without redoing the work
- a lead ticket whose `check-all` fails on a check main passes is blocked as before
- two checks failing, one of them only on the branch: blocked as before
- a developer ticket is still picked while main is red
- `docs/workflow.md` says what a red main does to the queue
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
