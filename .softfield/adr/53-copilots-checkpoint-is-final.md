# ADR 53: Copilot's stand-in checkpoint is final

- **Status:** Accepted (by the owner, 2026-11-24)
- **Date:** 2026-11-24
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** f8-08 (Claude re-checks the merges a stand-in reviewed), as built under [ADR 16](16-claude-window-and-named-milestones.md) item 9. Nothing else changes: the checkpoint every two merges, Copilot standing in when Claude can't, its fix tickets, [ADR 38](38-no-checkpoint-the-review-will-read.md), [ADR 51](51-copilot-pre-reviews-while-claude-is-out.md)'s pre-review.
- **Evidence:** F282 (owner, 2026-11-21 and 2026-11-24). Copilot reviewed f62-03 and f275-02 on 21 Nov (job 2611), found three problems and filed f62-04, f62-05 and f275-03. The queue then held a second checkpoint, "Claude re-checks f62-03 and f275-02, after a stand-in", waiting for Claude's reset. The owner: "no need to re checkpoint if copilot took over and did checkpoint. claude will catch whatever's left in the next checkpoint if it can or the review."

## Decisions (⚑ = deviates from an earlier decision)
1. ⚑ **A stand-in checkpoint closes its merges.** Once Copilot's checkpoint passes, its merges leave the unchecked list and nothing queues them again for Claude. Its fix tickets are merged and checked like any others.
2. **What it missed is left to the next reader:** Claude's next checkpoint (on the merges that follow, including the fix tickets) and the milestone's review, which reads the whole milestone (ADR 38).
3. **The re-check goes from the runner:** the `recheck` and `recheck_filed` state, the re-check note in Claude's checkpoint prompt, and the "Claude re-checks …, after a stand-in" reason. Re-checks still queued when this lands are dropped.
4. **The old Copilot bench line goes** from `runner/instructions/author/known-range.md` (2 of 5 on F2's checkpoint, 2026-10-02): it is out of date and was the reason for the re-check. Copilot's record now comes from the reviews' ratings of its findings (ADR 51 item 6).

## Alternatives turned down
- **Keep the re-check, reworded to name Copilot** (the lead's first F282 plan): it costs a Sonnet run (about $0.25) on every stand-in and queues a row the owner reads as the checkpoint not being done yet. The review reads those merges anyway.

## Consequences
- One Claude job fewer after each stand-in. Over a weekend with Claude out, that is every second developer merge.
- A problem Copilot misses can stay until the milestone's review, and later tickets may build on it. The review sees it whole, and its fix tickets repair it.
