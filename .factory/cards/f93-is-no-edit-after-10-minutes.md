# Milestone F93: Developer attempts get 20 minutes before the no-edit stop

> **State:** done · **Priority:** 100 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-10-16. Base: git tag `f93-is-no-edit-after-10-minutes-start`. Report: [`.factory/reviews/f93-is-no-edit-after-10-minutes.md`](../reviews/f93-is-no-edit-after-10-minutes.md).
> Planted by the owner on 2026-10-10.

## Notes
is no edit after 10 minutes rule too harsh? look at recent examples where this happened

### From F111: [07:58:52] ── f53-02-parked-review-crate · developer · d3… (merged by the lead on 2026-10-13)
[07:58:52] ── f53-02-parked-review-crate · developer · d3 ──
[07:58:52] A review that waits for Claude shows as waiting in the line's queue, behind the tickets that can run, instead of as number 1 with nothing said.
[07:58:52] ▶ [claude-opus] direction
[08:00:15] ■ [claude-opus] direction done · 1 min · $0.68
[08:00:15]   ↳ [claude-opus] Both attempts stopped with no edit: you read `factory.js`, `conftest.py`, `overview.py` and the test files, and planned the whole change. You already understand it. Read nothing else; every fact you still need is below. Make the first edit within two minutes, in `factory_dashboard/line.py`, and run the tests after each step.

i wonder if 10 minutes timeout is too aggressive

## What we know (lead, 2026-10-13)
From the 29 developer attempts of 10 to 13 October (the local Qwen; `.factory/var/runs/2026101*/*/opencode-*.jsonl`):
- **16 of the 29 were stopped by this rule**, on 9 tickets. f3-08 and f9-25 lost all three attempts to it, and the lead built both.
- **The 13 that did edit made their first edit after 1.6 to 9.2 minutes, 6.3 in the middle; four of them after 8 minutes or more** (f32-01 twice, f17-01, f9-32). Nothing is seen past 10 because the stop is there: the attempts that would have edited at minute 11 or 12 are among the 16.
- **The stopped ones were working, not stuck.** f53-02's first attempt read files for 5 minutes in five steps, then was 5 minutes into its sixth step when it was stopped; its thinking ends on "Now I need to implement this by modifying `_due_reviews`…". Its second was 6 minutes into its third step. None of the 16 was repeating itself (the other stop, `stopped: repeating itself`, catches that within a minute and stays).
- **Why 10 minutes is short here:** each step sends the whole conversation again (67,000 tokens a step in that session), so a step after reading three files takes 1 to 2 minutes before the model writes anything. Ten minutes is five or six steps.
- **Even the best case is close:** under a direction that said "read nothing else, first edit within two minutes", f53-02's third attempt made its first edit at 5.6 minutes; the other directed attempts at 6.2 to 8.2.
- **Where the rule came from** (f2-05): in F1, 6 of 24 failed attempts made no edit in 25 to 30 minutes. That is what it is there to stop, and 20 minutes still stops it.
- Not F71, "Longer timeouts": that card is the whole attempt's limit (60 minutes) and the slow tests; this is the early stop inside an attempt.

## Decisions
- **D1: the stop moves from 10 to 20 minutes** (`NO_EDIT_AFTER` in `runner/local_model.py`), and its words follow: "stopped: no edit after 20 min". Not 15: the slowest first edit seen is 9.2 minutes against a cut at 10, and a single step ran past 6 minutes, so 15 leaves less than one step of room.
  - **The cost:** an attempt that is really going nowhere holds the GPU 10 minutes longer, 30 for a ticket that loses all three.
  - **What it buys:** an attempt saved is 10 minutes not thrown away, and often a direction ($0.68 for f53-02's) and an escalation where Opus builds the ticket.
  - A timeout, not a workflow rule: `.factory/project.toml` says they are tuned freely, so no ADR.
- **D2: the stop's words are built from the number,** so the next change is one number. The number stays a constant in the code, beside the repeat stop's; it moves to `runner.toml` only if it is tuned a third time.
- **D3: no change to directions or to the three attempts.** The F53 review suggested skipping the direction after two no-edit stops. The logs say the opposite: f53-02's and f5-08's directed attempts wrote the whole change. Looked at again once D1 has run for a while.
- **D4: how we will know.** 16 of 29 attempts stopped is the number to beat. The factory's periodic review (F59) reads it from the session reports ("stopped: no edit after 20 min"); if it stays above a quarter, the tickets are too big for the developer, not the stop too short, and that is a planning fix.

## Tickets
| # | Id | Who | Difficulty | What |
|---|----|-----|------------|------|
| 01 | no-edit-stop-at-20 | lead | 1 | D1, D2: the stop at 20 minutes, its words from the number. Lead: `runner/**` is protected |
