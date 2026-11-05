# Milestone F208: Let a local attempt finish its step before the no-edit stop

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-11-03.

## Notes
there's been a few 'no edits after 20 minutes' failed attempts, i suspect that the local models sometimes need mor etime legitly as the project becomes more complex

## What we know (lead, 2026-11-03)
From the jobs table since F93 moved the stop to 20 minutes (16 October), LM Studio's logs and the attempts' streams.
- **64 attempts were stopped at 20 minutes. 39 of them came on 29 and 30 October, when the model ran at 1.7 tokens a second** (usually 21 to 30), and read prompts at 73 tokens a second (usually about 250). No limit saves those: a first step took over 5 minutes. Directions and escalations from 29 October to 04:00 on the 30th came to 26 jobs and $27.64. It looks like the slowness the owner saw with the KV cache in system memory (2 tokens a second, F195), though these logs don't show that setting; the speed has been normal since 2 November.
- **The other 25 are about 13% of about 190 attempts**, under the quarter F93 D4 set as the line for "the tickets are too big".
- **Today's two were cut in the middle of one long thought, not while reading.** f170-05's attempt 1 spent 15.5 minutes on one step at 23.5 tokens a second, about 21,000 tokens, with no tool call. f170-04's attempt 3 spent 14 minutes the same way, reaching 129,335 of 130,304 tokens of context when it was cut. f59-01 did the same on 27 October (15 minutes on its last step).
- **Nobody can tell what those thoughts were.** A thought is only saved when its step ends: `thinking-3.md` of f170-04 stops at the step before. The repeat stop reads the same saved text, so it can't see a thought in progress either, and it has stopped nothing since 16 October.
- **The same ticket can go either way.** f170-05's attempt 2 started the same way, made its third step in 3 seconds instead of 15 minutes, had its first edit at 10.8 minutes and passed at 42.
- **The owner's hunch holds for reading.** Three files (`planning.py`, 710 lines; `test_planning.py`, 2,044; `planning.html`) are 40,000 tokens, 160 seconds in one step; f170-04 read 61,000 tokens in one step, 4 minutes. Today's first edits came at 8.5, 10.8 and 12 minutes, against a middle of 6.3 in October. That still leaves room under 20.
- **Other stops read until the clock ran out,** like f81-03 and f81-08 on 28 October: 7 to 10 steps in 20 minutes, several of them re-reading 40,000 tokens or more because LM Studio's prompt cache missed (`f_keep = 0.094`). Why it missed isn't known yet.

## Decisions
- **D1: at minute 20 with no edit, the attempt finishes the step it is on, and no later than minute 35.** If that step ends with no edit, it is stopped at the next check. Instead of moving the number again (F93 moved it from 10): a flat 30 gives an attempt that is only reading 10 more minutes, while this gives it one more step, and a long thought the room it needs. 35 is today's thoughts (begun around minute 5, 15 minutes long at the cut) with as long again. A real runaway costs 15 more minutes of the GPU at most, 45 for a ticket that loses all three attempts.
  - A timeout, not a workflow rule (F93 D1): no ADR.
  - The words stay "stopped: no edit after 20 min": still true, and `stop_reason` compares them.
- **D2: a stopped attempt keeps its thinking,** in `thinking-N.md` next to its log, whether or not a direction follows. With D1 a long thought now ends and is saved, so the next review can read whether it was planning or going round in circles.
- **D3: how we will know.** At the factory's periodic review (F59): how many attempts edited or passed after minute 20, and what the saved long thoughts say. If nearly none did, D1 goes back to a plain stop at 20; if the thoughts go round in circles, that is a new card.
- **D4: not here.** The 1.7 tokens a second cost the most and nothing told the owner for two days: a warning for that belongs with F195, I've reduced the context window, whose subject is why the local model fails. The prompt cache misses go there too.

## Tickets
| # | Id | Who | Difficulty | What |
|---|----|-----|------------|------|
| 01 | finish-the-step | lead | 3 | D1, D2: the step in hand finishes, up to minute 35; a stopped attempt keeps its thinking. Lead: `runner/**` is protected |
