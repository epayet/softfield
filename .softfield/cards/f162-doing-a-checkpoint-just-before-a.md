# Milestone F162: No checkpoint on merges the milestone's review is about to read

> **State:** done · **Priority:** 3 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-04. Base: git tag `f162-doing-a-checkpoint-just-before-a-start`. Report: [`.softfield/reviews/f162-doing-a-checkpoint-just-before-a.md`](../reviews/f162-doing-a-checkpoint-just-before-a.md).
> Planted by the owner on 2026-10-20.

## Notes
Doing a checkpoint just before a review doesn't sound very useful. There was a milestone at 22/22 tickets done and it did a checkpoint and I suspect a review straight after

## Expected outcome
When a milestone's last ticket merges, its review starts at once: no checkpoint reads merges the review is about to read whole. Other milestones' merges still get theirs.

## Done when
- f162-01 is merged, and the next milestone that finishes on developer merges shows no checkpoint between its last merge and its review on the floor's log.

## Decisions
- D1: [ADR 38](../adr/38-no-checkpoint-the-review-will-read.md), amending ADR 12 item 8. "Covered" means the merge's milestone has its review due (`due_reviews`) or stopped at `restart`; covered merges leave `unchecked` and `recheck`, in one helper in `runner/loop.py` that `note_merge` and `checkpoint` both call.
- D2: one lead ticket (`runner/` is protected), no UI change: the floor already shows what is queued.

## Tickets
- f162-01-no-checkpoint-before-review (lead)
