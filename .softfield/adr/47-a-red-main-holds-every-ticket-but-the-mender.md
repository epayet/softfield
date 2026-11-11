# ADR 47: While main fails its tests, only the ticket that mends it runs

- **Status:** Accepted (by the owner, 2026-11-11)
- **Date:** 2026-11-11
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 29](29-the-lead-looks-at-a-blocked-ticket.md) item 7 ("the runner takes no other lead ticket": developer tickets went on).
- **Evidence:** [F202](../cards/f202-while-main-is-red-hold-tickets.md), from the F80 review. Two red mains so far. f80-01 (2026-10-27): 72 minutes of Qwen and $1.56 of Opus on work that was right, failing only on main's own broken test.

## Context
- When main fails a check, `waits_for_main` (`runner/loop.py`) holds the lead's tickets and the developer tickets already waiting on their branch (f80-02). Every other developer ticket still starts.
- A branch cut from a main that fails `tests` fails `all-tests` too. So each of those tickets pays a whole model run (Qwen's, up to an hour) only to end up waiting on its branch. Nothing is lost but the time and the machine, and the line is busy with work that can't merge.
- Each such wait also writes the red main's list of failing checks as `["tests"]` alone. If main also failed a lead ticket's `layout`, the runner calls main mended as soon as `tests` pass, and the next lead ticket finds `layout` broken again.
- The ticket that would mend main can itself fail a check main fails (its fix is incomplete). Today it then waits for main like the others, and main waits for it: nothing moves until the owner steps in.

## Decisions (⚑ = deviates from an earlier decision)
1. ⚑ **While main fails `tests`, every ready ticket waits but the mender.** The lead's and the developers' alike. While main fails only checks that judge a diff alone (`layout`, for one), developer tickets go on as today: their own branch can pass.
2. **A red main's failing checks add up.** A new failure on main adds its checks to the list, never replaces it, and main is mended only when it passes all of them.
3. **The mender never waits for main.** If it fails a check main fails, the attempt counts as failed as any other would (its fix didn't work), so it goes on to its next attempt, escalation or block, and the lead looks at it (item 2 of ADR 29).
4. **The mender is looked for again at each pick** while none is ready: a repair ticket queued after main went red is found as soon as it is ready, from the files the failing checks name, as today.
5. **The owner's item says it:** "no other ticket runs until main passes", and with no mender, "nothing would mend it yet".

## What doesn't change
- Main is checked again on each commit that could change a check (`_look_at_main`), and the owner's item clears once it passes.
- No check is skipped: a ticket merges only when all its gates pass.
- A developer ticket waiting on its branch runs only its gates again once main passes, with no new attempt (f80-02).

## Cost and risk
- One lead ticket, about $1.50 (a lead ticket's average since mid-October is $1.37; this one is small and tested).
- **The risk is a stopped line:** with no mender, nothing runs until main is fixed. Today the line runs on, but only to fill branches that wait anyway. The owner's item says so (item 5), and the idle line already counts the tickets waiting for main.

## Alternatives turned down
- **Keep developer tickets going:** the cost F202 is about, one model run each for nothing.
- **Hold only Qwen's tickets:** a cloud developer's run costs money instead of time, and fails the same way.
