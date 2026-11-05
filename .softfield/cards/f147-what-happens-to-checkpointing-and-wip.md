# Milestone F147: What happens to parked work when Claude runs out

> **State:** ready · **Priority:** 2 · **Area:** factory
> Planted by the owner on 2026-10-16.

## Notes
What happens to checkpointing and WIP attempts that need directions when I'm out of Claude completely, is the work wasted?

The owner, on the lead's answer: "if there is a clash, the work is thrown away? shouldn't the merger (probably the lead) maybe decide to do a conflict resolution instead? does it not do that?"

## What the code does (2026-10-16)
- A Claude job a limit cuts off (lead ticket, direction, escalation, review, planner) commits its work on its branch as "wip … (parked)" (`_park` in `runner/loop.py`), keeps its session in `state.interrupted`, and resumes that session after the reset. A planner's drafts stay on `plan/<card>`. The queue goes on meanwhile.
- A developer ticket that waits for its direction keeps `task/<id>`. When it goes on, `_start_attempt` merges main into the branch (`_catch_up`). On a clash it runs `fresh_branch`, which is `git checkout -B task/<id> main`: the attempts' work is overwritten, and nothing saves its diff first.
- In that case (the `_start_attempt(s, branch, "")` call in `run_task`, before `give_direction`), the direction's `last.diff` is written from the reset branch, so it's empty, and the last attempt's prompt doesn't get `prompts.RESET["conflict"]` either. Nobody records a clash, so how often it happens is unknown.

## Expected outcome
A ticket whose branch clashes with main loses nothing: its work is saved before the reset, the direction reads it and decides, and the local developer reapplies it on main.

## Done when
- A clash saves the branch's diff against the merge base to the ticket's logs as `clash.diff`, then resets the branch, as today.
- The direction is told about the clash and reads `clash.diff`. The last attempt is told its branch was reset for a clash and is pointed at `clash.diff` to reapply.
- The run report and the job's note say "clashed with main", so a factory review can count clashes.

## Decisions
- **D1 The direction decides, the developer reapplies.** No new Claude job for a clash. The direction already runs on Claude right then, and reapplying a diff on fresh code is a local model's kind of work. A dedicated Opus job to resolve conflicts would cost about $2–5 each, and it would be held back by the same Claude limit that made the ticket wait.
- **D2 A diff file, not a kept branch.** `clash.diff` sits next to the other logs that the direction and the developer already read. No new branch for the runner to clean up.

## Tickets
1. `f147-01-clash-keeps-the-work` (lead): save the work before a clash resets the branch, and hand it to the direction and the last attempt.
