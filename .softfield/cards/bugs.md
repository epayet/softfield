# Bugs: fixes outside the milestones

> **State:** building
>
> A standing key, never planned, reviewed or signed off ([ADR 19](../adr/19-feature-board.md) items 2 and 2b; D5 in [`f5-board.md`](f5-board.md)).

## What a bug ticket is
- A ticket `.softfield/tasks/<folder>/bug-<nn>-<slug>.md` with `milestone: bugs`, its `area:` (factory or product, required) and an optional `priority:` (50 if missing, lower first). The format is in [`docs/task-format.md`](../../docs/task-format.md)) ("Bug tickets").
- One small fix, written like any ticket: a goal, the files to read, and Done when.
- It waits in `.softfield/tasks/later/` until queued, and in `.softfield/tasks/ready/` `runner run` takes it like any other ticket.
- It is done when it merges. Checkpoints count its merge like any developer merge; a stand-in checkpoint's fix of a bug is a bug too.
- `runner milestone bugs`, `runner review --milestone bugs` and `runner signoff bugs` refuse: there is nothing to plan, review or sign off.

## Where bugs come from
- A review's finding worth a run (route `later`, ADR 35). The first pass (f5-13, 2026-10-23) set aside bug-05 to bug-47 from the old backlog file, retired by F149.
- A finding that doesn't belong to a running milestone.
