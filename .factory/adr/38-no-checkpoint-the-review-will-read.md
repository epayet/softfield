# ADR 38: No checkpoint on merges the milestone's review is about to read

- **Status:** Accepted (by the owner, 2026-10-29)
- **Date:** 2026-10-27
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 12](12-junior-feedback-and-checkpoints.md) item 8 ("a checkpoint every 2 merges"). Nothing else in ADR 12, nor the review loop, changes.
- **Evidence:** F162 (owner, 2026-10-20): "a milestone at 22/22 tickets done did a checkpoint and a review straight after". The metrics agree. From 2026-10-15 to 2026-10-23, about a dozen checkpoints ran on a milestone's last merges and its review started right after, often within seconds: f1 (jobs 923 → 925), F95 (950 → 951), F23 (970 → 971), m1-first-suggestions (1146 → 1147, and 1142 between its two rounds), F8 (1238 → 1239), F5 (1285 → 1287), F6 (1296 → 1298), F142 (1342 → 1344). Each cost $0.13–0.30 and about a minute. The review then judged their findings; it reads the same diffs anyway, whole, on Opus.

## Context
- A checkpoint (Sonnet) reads the last two developer merges so a problem is caught before the next tickets build on it. That is its whole value: a later ticket in the same milestone.
- When a merge is its milestone's last, no later ticket of that milestone follows. The review is due (`due_reviews`), waits for the checkpoint (`_queue_due_review`), then reads the whole milestone diff and judges the checkpoint's findings.
- The same holds between review rounds: a review that wrote fix tickets stops as `restart`, and its next round reads exactly those fix merges.
- A checkpoint's merges can span milestones (f8 review): one merge may be another milestone's, still mid-build, which does gain from it.

## Decisions (⚑ = deviates from an earlier decision)
1. ⚑ **A merge the review will read leaves the checkpoint's list.** A merge counts as covered when its ticket's milestone has every ticket done and its review is due, or its review stopped at `restart` (fix tickets, next round to come). Covered merges are dropped from `unchecked` and from `recheck` (a stand-in's batch).
2. **The count goes on with what is left.** A checkpoint is queued only when the uncovered merges still reach `checkpoint_every`; other milestones' merges keep their checkpoint.
3. **A checkpoint already queued drops them too,** when it starts: when nothing is left, its row is finished with no job, and the review goes ahead.
4. **The run's log says so,** one line ("no checkpoint: F23's review reads f23-04, f23-05"), so a skipped checkpoint is never silent.

## Alternatives turned down
- **Skip the review instead, on a small milestone:** the review is the one place the whole milestone is read, rated and signed off from; the checkpoint is the cheaper one to lose.
- **Keep the checkpoint but let it write no fix ticket:** still pays for a read the review repeats.
- **Leave it:** about $2–3 a week, but a step the owner reads as waste on every milestone's last line.

## Consequences
- The review starts as soon as a milestone's last ticket merges. About a dozen checkpoints fewer a week, roughly $2–3 and a minute each.
- A fix the checkpoint would have queued before the review now comes from the review's first round: the same work, from Opus instead of Sonnet.
- Fewer samples for the checkpoint's rating and its shadow (ADR 14 item 12): only the last batch of each milestone, which the review judged anyway.
