# Milestone F245: An approved card shows as Seed until the runner's next round

> **State:** ready · **Area:** factory · **Fast lane:** yes
> Planted by the owner on 2026-11-13.

## Notes
I accpedfed a plan as go first but the milestone is not showing in the board at all for roller coaster app it's the title click thing why can't see
Oh it went to seed for some reason

## What happened (the lead, 2026-11-13)
- coaster-ranker's M12, "Tap the title for a roller coaster ride across the sign", was approved with Approve first at 20:53:08 (thread 229). Its ticket `m12-01-title-ride` ran 20:53:54–21:07:42, the review 21:07:54–21:10:02, and M12 is now Ripe, waiting for sign-off.
- Approving (`_approve_plan` in `runner/requests.py`) writes the card `ready` on main, archives its thread and writes `board_order`, but leaves the card's `milestones.state` row as it was: `idea`. `apply_owner_requests` (`runner/loop.py`) then calls `sync_tickets` only.
- The board (`_milestone_stage` in `factory_dashboard/board.py`) shows an `idea` card with no open thread as **Seed**. So from the approval until the runner's next round read the cards again (`run_projects`' `turn`, after the developer and the review had run), M12 sat in Seed, with its ticket at work. Every first-plan approval does this, on every project.

## Decisions
- **D1: an applied request reads the cards again at once.** `apply_owner_requests` calls `sync_cards` beside `sync_tickets` whenever a request was applied, so an approved card is Planted (or in the fast lane) on the board before its first ticket starts. A merge, a seed or a dropped card reaches the board the same way.
- No change to the board's stage rule: it was right, its copy of the card was stale.
- No mock-up: the fix restores what the board already meant to show.
