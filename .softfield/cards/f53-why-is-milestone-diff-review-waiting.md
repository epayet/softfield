# Milestone F53: a review waiting for Claude doesn't stop the line

> **State:** done · **Priority:** 1 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-10-13. Base: git tag `f53-why-is-milestone-diff-review-waiting-start`. Report: [`.softfield/reviews/f53-why-is-milestone-diff-review-waiting.md`](../reviews/f53-why-is-milestone-diff-review-waiting.md).
> Planted by the owner on 2026-10-08.

## Notes
wasn't copilot supposed to be able to do that? example: [09:09:36] ── f20-data-safety review · round 1/3 ──
[09:09:36] The whole milestone diff.
[09:09:36] ▶ [runner] e2e tests
[09:10:56] ■ [runner] e2e tests passed · 1 min
[09:10:56] ⏸ [runner] the review waits for Claude (claude: 5-hour window 80% used, over its cap of 75%) · resumes 12:41 (in 3 h 30)

From the code (2026-10-08):
- **Copilot was only ever the checkpoint's stand-in** (ADR 16 item 9, `[roles] checkpoint-stand-in` in `.softfield/project.toml`): a read-only look at two merges, whose findings Claude re-checks later (f8-08). The milestone review is `[roles] review = ["claude-opus"]`, and no decision gave it a stand-in.
- **The real cost was the idle line.** `review_milestone` in `runner/milestone.py` calls `wait_for_room` ("nothing else runs: it waits rather than parks"), so the whole runner slept from 09:10 to 12:41. No commit landed in between, while about 40 developer tickets sat in `.softfield/tasks/ready/` (f22-01, f32-01, f50-01…) and the local model could have taken them. Checkpoints, escalations and planner jobs already park their queue row and let the line go on (ADR 16 item 4, `_park_support`); the review is the one support job that still sleeps.
- The 1-minute e2e run before the wait was wasted too: it runs again when the round starts.

### Who looks at the code (asked by the owner, 2026-10-09)
- **Gates** (every ticket, no AI): tests, lint, types. A ticket that fails them doesn't merge.
- **Checkpoint** (every 2 developer merges): Claude Sonnet reads those two merges and files fix tickets. When Claude has no room, Copilot does it instead, read-only, and Claude checks the same merges again once it has room (f8-08). With Copilot's month used up, the checkpoint just waits for Claude and the merges stay unchecked until then.
- **Review** (once per milestone, when all its tickets are merged): Claude Opus reads the whole milestone's diff, runs e2e, writes `.softfield/reviews/<key>.md` with the sign-off sheet and files fix tickets, for up to 3 rounds. Only Claude does it.
- **Sign-off** (the owner): after the review.

## Expected outcome
A review Claude can't take now waits in the queue, like a parked checkpoint, and developer tickets run meanwhile. It goes first again as soon as Claude has room.

## Done when
- With Claude over its 75% (switch off), a due review's row parks until the window resets, the console and the queue say "the review of f20-data-safety waits for Claude … resumes 12:41", and the next developer ticket starts at once.
- The check comes before the e2e run, so a parked review doesn't run e2e for nothing.
- When the reset passes, the review is the next pick (before any ticket, as ADR 22 settled), and it starts at the round it was at: a parked round 2 doesn't redo round 1, and the milestone stays due (no review stop recorded, no verdict printed).
- Turning the 5-hour switch on while it waits ends the wait at the next pick, as today.
- A review parked between rounds re-reads only its own milestone's fix tickets, not the other milestones' merges that landed while it waited.

## Decisions
- **D1 Park the review, don't sleep** (applies ADR 16 item 4 to the review). Same path as a checkpoint: `park_row` with the hold's `until`, back to the queue. ADR 22's settled point "a due review keeps its place" still holds: it is first whenever Claude can take it; only the time Claude can't is given to the developers.
- **D2 No Copilot stand-in for the review.** The review is the gate before the owner's sign-off: Opus reads the whole milestone diff, runs checks, writes `.softfield/reviews/<key>.md` and its sign-off sheet (which F50 D1 makes the "ripe" signal) and files fix tickets. Copilot is read-only, can't write the report, scored 2 of 5 on F2's checkpoint bench, and has 200 credits a month that a whole-milestone diff would eat. A stand-in review would still need Claude's full review after it, so it saves nothing. With D1 the wait costs only the review's own delay, which the owner's sign-off absorbs anyway.
- **D3 One review per milestone, back to back; no combined review** (asked by the owner, 2026-10-10). When several reviews are due as Claude comes back, they run one after the other, oldest milestone first, as the queue already does. One combined review was weighed and not kept: the report, sign-off sheet, score, fix tickets and rounds are all per milestone; a combined diff is bigger (F6's review alone hit the 30-minute limit twice) and one failure would hold every sign-off; and it wouldn't remove the unrelated merges, since most of them belong to milestones still being built. What it would add, seeing clashes between milestones, is better served by each review's first round already reading main as it stands.

## Tickets
1. `f53-01-park-the-review` (lead, `runner/` is protected): D1.
