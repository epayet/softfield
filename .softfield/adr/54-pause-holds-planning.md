# ADR 54: A pause holds everything, planning too

- **Status:** Proposed
- **Date:** 2026-11-25
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 22](22-one-visible-queue.md) item 5's ⚑ "Except planning" (owner, 2026-10-07; built in f6-14), and what [F6](../cards/f6-planning-room.md) D1 "While paused" and D2 "As built (f6-13)" say about pauses. Nothing else changes: Pause and Resume on the top bar, a running job finishing before the pause takes hold, the pause's usage event, the daily backup, the fast lane being held by a pause (ADR 35 item 5), and the per-project pause (ADR 30).
- **Evidence:** the owner, 2026-11-25: "the runner is paused atm, i assumed that means it would be safe to do some work on the folder, but planning still goes through even paused", then "for now i'd rather have the pause actually pause everything". During that session a planner job on F293 had the main folder on `plan/f293` while the factory was paused. A planner job checks out its card's plan branch in the main folder (`_plan_branch` in `runner/planner_job.py`), and the hold's requests commit on main (`commit_all` in `runner/requests.py`: plants, approvals, the board's order), so anything left uncommitted in the folder can end up in one of their commits. `lead.md` already says to merge into main "while the runner is stopped (or paused on main)", which only holds once this ADR is built.

## Decisions (⚑ = deviates from an earlier decision)
1. ⚑ **While paused, nothing starts:** no planner job, no setup job, no ticket and no Claude job. `dispatch.PLANNING` is no longer an exception to `PAUSED`, and the hold (`_hold_for_the_owner` in `runner/loop.py`) ends only at a resume.
2. ⚑ **The owner's requests wait for the resume too.** While paused, the hold applies only a resume; plants, messages, approvals, send-backs and changes to the board wait in the database and are applied, in the order they came, as soon as the owner resumes. The backup still runs (it writes outside the repo). The dashboard already shows each one as on its way (dashed orange edge), so the owner sees it was taken.
3. **A pause starts at the end of the running job**, as today: the top bar says "pausing" until that job has finished and the runner is back on main, then "paused". From that point the folder is the owner's.
4. **The top bar's words change** from "only planning goes until you resume" to "nothing runs until you resume; what you send waits for it", and the desk's planning rows say "waits for your resume" while paused.
5. ⚑ **Approving a `replan` no longer lifts a pause**, since nothing is approved during one. The planner prompt (`prompts.PLANNER`) stops suggesting a pause before a `replan`. A ticket the line is running is still refused by the approval (f6-13).
6. **The docs follow:** ADR 22 item 5 and F6 D1 and D2 point here; `lead.md`'s "Steering loop" says that a replan runs after the resume, and its line on merging "while the runner is stopped (or paused on main)" stays as it is.

## Alternatives turned down
- **Keep planning during a pause, and give each planner job a worktree of its own** (the lead's recommendation, 2026-11-25): the main folder would never leave main, and the steering loop would keep working while the line holds. Turned down for now: the owner wants a pause that means "hands off", and this is the smaller change. It stays a candidate for later.
- **Hold planner jobs but keep applying requests:** plants, approvals and the board's order commit on main, so a plant could pick up the owner's unsaved edits in its commit.
- **Use Stop:** this already holds everything today, but Pause is the button on the dashboard and its name says it holds the work.

## Consequences
- **Steering while the line holds is gone** (the reason for item 5's ⚑ on 2026-10-07): a message sent during a pause gets its answer only after the resume, and the line may start a ticket before a `replan` about it is approved. To change work before it starts, the owner moves it down the board or sets it aside, then resumes.
- The folder is safe to work in once the top bar says "paused": it stays on main, and the runner neither checks out nor commits anything there.
- A long pause builds up a backlog: on resume the requests are applied first, then the planner jobs go first (dispatch's order), before any ticket.
