# Milestone F177: Planner replies: record their real cost, start cold threads fresh

> **State:** ready · **Priority:** 2 · **Area:** factory
> Planted by the owner on 2026-10-27.

## Notes
Planner replies cost half of Claude's week (19 Oct: $150 of $305, $2.58 a reply): find what makes a reply cost that much and cut it, keeping planning on Opus

### From F189: I just talked somewhere about adding new logic to use… (merged by the lead on 2026-10-29)
I just talked somewhere about adding new logic to use --resume Claude if under 5 minutes but not if longer and send the whole thread as new chat instead. Actually, why not --resume all the time? Why the extra logic? Claude might change the cache time over time

## Plan (lead, 2026-10-27)
- **Expected outcome:** the dashboard shows what each Claude job really cost, and a planner reply on a thread the owner comes back to hours later costs about half what it does now. Planning stays on Opus.
- **Done when:** a resumed job's cost is its own, past rows included; every planner reply starts a fresh session with the thread's history.

### What was found (from `jobs` and the logs under `.softfield/var/runs/`)
- **Half of the $150 was never spent.** `claude -p --resume` reports `total_cost_usd` for the whole session so far, and `run_claude` (`runner/claude.py`) stores it as the job's own cost. Every thread's recorded costs only climb (0.92 → 1.10 → 1.18 → 1.26 for replies of 6, 1 and 1 steps); f172's fourth reply recorded $14.02, of which $5.22 was its own. Week of 19 Oct, own costs: planner $71.36 of $227 (31%, $1.32 a reply), not $149.76 of $305 (49%). The other roles were right: they don't resume, except after a usage limit.
- **What a reply really pays for.** Opus's price, fitted to three fresh replies' `modelUsage`, is about $0.20 per 1M tokens read from the cache, $8 per 1M written to it and $20 per 1M written out. A fresh reply (36 tool calls on average) spends about a third on each: rereading its context every turn, writing what it reads into the cache, and its own output (tickets, mock-ups).
- **The expensive case: a cold resume.** The prompt cache lives about an hour (a resume after 25 minutes read 97k tokens from it and wrote 8k). The owner usually answers hours later, so a resume first writes the whole earlier session back into the cache: 239k tokens, $1.92, before f172's reply did anything. Since 13 Oct: 35 cold resumes, $1.65 each ($57.63); 12 warm ones, $0.45 each; 86 first replies, $1.25 each.

### Decisions
- **D1. A job's cost is its own.** When a Claude job resumes a session, its `cost_usd` is the result's `total_cost_usd` minus the `cost_usd` of the session's earlier jobs (summed, since they are own costs too). Past rows are fixed once, by a new step at the end of `MIGRATIONS` (`runner/metrics.py`), in each session's order: own = recorded − the previous recorded value of the same session. `runner/backfill.py` subtracts the same way. Tokens are unchanged (the result's `usage` is already per job).
- **D2. A planner job always starts a fresh session** (revised 2026-10-29 with the owner, from F189: no timer tied to the cache's lifetime). `run_planner` (`runner/loop.py`) never resumes the thread's session: every reply gets the thread's history (`planner.history`, the path a new thread takes today). The thread keeps recording its last session. A session cut off by a usage limit still resumes as now (`state.interrupted`). Why not always resume: since 13 Oct, 57 cold resumes cost $1.62 each ($92, 42% of the planner's own spend), each first writing the whole old session back into the cache; only 13 replies came within the hour ($0.46 each), so the 55-minute rule first drafted would have saved about $3 more over two weeks than always fresh, for a timer that breaks if the cache's lifetime changes.
  - **What carries over** (2026-10-30, the owner asked whether losing the earlier investigation hurts the answer): the card's doc. The planner's brief tells it to keep what it found and what it ruled out (facts, files, numbers) in the doc under the plan, as this doc's "What was found" does, and to check the code again before relying on it. A cold follow-up came 64 hours after the last reply on average, while main took about 300 commits over the same span, so what an old session remembers reading is often out of date; cold follow-ups already made 18 tool calls each while carrying their full context.

### Tickets
| # | id | agent | what |
|---|----|-------|------|
| 01 | f177-01-own-cost-per-job | lead | D1: the meter |
| 02 | f177-02-planner-resumes-only-warm | lead | D2: every reply starts fresh (the id keeps its first name) |

Both touch `runner/`, which is protected, so both are the lead's. 02 doesn't wait for 01, but 01 goes first on the board's order so 02's saving can be measured on true numbers.
