# ADR 51: Copilot pre-reviews a finished milestone while Claude is out

- **Status:** Accepted (by the owner, 2026-11-24)
- **Date:** 2026-11-23
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 38](38-no-checkpoint-the-review-will-read.md) item 1 (a merge the review will read gets no checkpoint) and [ADR 16](16-claude-window-and-named-milestones.md) item 9 (Copilot's only job is standing in for a checkpoint). Nothing else changes: the checkpoint every two merges, the stand-in, ADR 50's "never idle for the pace".
- **Evidence:** F285 (owner, 2026-11-21): "rather than having factory idle it could improve things", for a Friday when Claude is out until Monday. Since ADR 50, only Claude's real limit (100% of a window, or a rest) stops lead work, so that is exactly when the line goes idle: every developer ticket done, the reviews parked for Claude. Copilot's month is 10% used (2026-11-21), about one credit per job; its stand-in checkpoints ran eight times this month (last: job 2611, 2026-11-21).

## Context
- ADR 38 drops a milestone's last merges from the checkpoint, because the Opus review reads them whole right after. That holds when Claude is there. When it is out, the review waits hours or days, and nobody reads those merges meanwhile.
- Copilot is read-only and weaker than Sonnet: about 20% of the known findings on the bench (F140's notes), with false alarms. Every fix it files is a developer ticket the Opus review later reads.

## Decisions (⚑ = deviates from an earlier decision)
1. ⚑ **A new job, the pre-review,** done by Copilot (`[roles] checkpoint-stand-in`, read-only). It reads one milestone whose tickets are all done and whose review waits for Claude: the card's Expected outcome, Done when and Decisions, its done tickets, and the files they changed since the milestone's start. It checks the code against them, like a checkpoint over the whole milestone.
2. **Only when the line would otherwise idle:** Claude is at its real limit (ADR 50's `_held_at_the_limit`), and nothing else can start (no developer ticket, no queued job Copilot or a developer could take). It goes after every other piece of work, never before.
3. **It may file developer tickets only:** each finding that isn't a nit becomes a fix ticket, as a stand-in checkpoint's do (`fix_tickets`), for a developer. A finding that would need the lead (a protected file, or a fix of a fix) files nothing: it is recorded for the review.
4. **At most three per milestone,** counted from its passed jobs. A milestone gets another only after a new merge since its last one: a pre-review that filed nothing ends them until Claude is back.
5. **Within Copilot's pace:** its month's pace line (`use_reserve=False`), so the room the checkpoint stand-in needs stays.
6. **The review judges it:** its findings are recorded on the milestone like a checkpoint's, so the Opus review rates them (kept, wrong, missed). That is the record of how Copilot does, for the factory reviews.
7. **No re-check by Claude:** its fix tickets' merges are the milestone's, which the review reads whole (ADR 38 item 1 keeps them out of the checkpoint).

## Alternatives turned down
- **The owner's first list** (a checkpoint every two developer tickets, Claude else Copilot; other developer tickets before a review): already what the runner does (ADR 12 item 8, ADR 16 item 9; a review waiting for Claude parks and the queue goes on). Only the idle case was missing.
- **Copilot's checkpoint on the last two merges only:** too narrow; with the review days away, the whole milestone against its Decisions is the useful read.
- **Unlimited rounds:** each round adds developer tickets, and the review must wait for them when Claude returns; three bound that.
- **Sonnet instead:** Claude is out by definition.

## Consequences
- Weekends with Claude out turn into developer fixes. Monday's review reads a milestone that has been looked at once more, plus up to three rounds of small fixes.
- Copilot's false alarms become developer work and lengthen the diff; the review reads it. When Claude returns while pre-review fixes still wait, the review waits for them (about 46 minutes each lately).
- Up to three Copilot credits per finished milestone, inside its pace line.
