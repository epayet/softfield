# Milestone F282: The re-check row says Copilot already did the checkpoint while Claude was out

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-21.

## Notes
This was in the queue while Claude was out of memory: Checkpoint: f275-a-project-created-by-web-interface · Claude re-checks f62-03-projects-planning-jobs-name-the-card and f275-02-start-plate-on-top, after a stand-in · waits until Mon 23 Nov 16:00 · softfield

Isn't copilot doing checkpoints in this case?

## What happened (lead, 2026-11-23)
Copilot did the checkpoint: job 2611, `copilot-auto` standing in for Claude on 21 Nov at 01:36, on f62-03 and f275-02. It found three problems and filed f62-04, f62-05 and f275-03 (f275-03 is merged). The row the owner saw is the second step of ADR 16 item 9 / f8-08: Claude checks the stand-in's review again once its limit resets. It parks, it doesn't hold the line. Its wording hid that Copilot had already done the work.

## Decisions
- **D1. No re-check after a stand-in** (owner, 2026-11-24; ADR 53). Copilot's passed checkpoint closes its merges. Claude's next checkpoint and the milestone's review catch what it missed. The runner's `recheck` state, note and reason go, and so does the old Copilot bench line in `known-range.md`. (Replaces the first plan, which only reworded the re-check row.)

## Tickets
- f282-01-recheck-row-names-the-stand-in (lead: `runner/` is protected; its name is from the first plan, and its body is ADR 53's change)
