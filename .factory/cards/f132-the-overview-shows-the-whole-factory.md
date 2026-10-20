# Milestone F132: The Overview shows the whole factory, not the picked project

> **State:** idea · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-15.

## Notes
From the terminal session of 2026-10-14 (ADR 30, after the owner's second `softfield init`).

The owner, 2026-10-14: "when i change project it stops showing what it's currently doing, that's
not good. the project change is just for planning and board, not for the overview and general
things that talk about what the factory is doing."

Done already: the top bar's status covers every project (`app.factory_wide_status`): a pause
first, then a running job, a wait for Claude, anything live, Stopped last; it names the project
when there is more than one, and its Pause / Resume posts to that project.

Still per project, and should be the whole factory's:
- the Overview: Now (running jobs), Next in line (the queue), Needs you, Coming, While you were
  away, allowances, the line on the Overview (`factory_dashboard/overview.py`, `_live_context`,
  `/live`);
- the Line page (`/line`, `/line/live`), Jobs, Runs, Timeline: what the factory did, with each
  item naming its project.

Stays per project (the picker's job): Planning, Board, Tickets, Milestones, a project's page.

Open questions: does the picker stay in the top bar, or move into the per-project pages only? How
does the Overview show several projects' queues: one list in the runner's real order (what
`softfield run --dry-run` prints across projects), each item tagged with its project?

A mock-up first (owner.md, 2026-10-09): Today and Proposed of the Overview on real data, two
projects running.

### From F160: the top bar on what's running atm is a bit buggy depending… (merged by the lead on 2026-10-20)
the top bar on what's running atm is a bit buggy depending on what project i'm looking at, it should the same regardless of current project viewed. similalrly, the overview should be the same across all projects, as there is one factory and runner for all projects. right now a developer ticket is working on softfield but top bar says Running: travel-companion · picking the next ticket.
