# ADR 16: Keep Claude's 5-hour window for the lead and the owner; Copilot steps in; name milestones

- **Status:** Accepted (by the owner, 2026-10-02)
- **Date:** 2026-10-02
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 14](14-developers-and-agents.md) item 12; [ADR 15](15-allowance-aware-routing.md) items 1, 4, 5 and 6; `runner/instructions/task-format.md` (milestone keys); the lead's replans (lead.md, a trial in F1)
- **Evidence:** [`.softfield/reviews/factory-f1.md`](../reviews/factory-f1.md); the owner's notes after F1 (2026-10-02). The owner chose the 25%, the 50%, the non-blocking question and items 8–10 (2026-10-02).

## Context
- **F1 stopped on Claude's 5-hour window, never on the week.** The week peaked at 20%. The 5-hour window refused Opus four times, for ≈11 h of waiting, and the GPU idled with it.
- **The last stop came from developer work on Claude.** At 05:26 the router gave f1-28, f1-31 and f1-52 to Sonnet because "week 16% used, under its pace line". Only the week is paced. The 5-hour window is a plain cap (`runner/allowance.py`), and Sonnet and Opus share it: its reading went from 22% at 05:04 to 100% at 06:12, and lead ticket f1-53 was parked mid-work. The owner couldn't plan either until 09:50.
- **The owner's yes to the reserve was meant for the week.** It lifts only the week's 30% (`at_reserve` in `runner/loop.py`), but nothing kept any of the 5-hour window back.
- **Checkpoints skip the allowance** (`router._reviewer`). Checkpoints and escalations hit by a limit sleep inside `call_claude`, which holds up the whole queue, while lead tickets and directions park.
- **`claude-sonnet` names no version.** The exact model (`claude-opus-5-5`) is only in each job's raw log, so a new Sonnet can't be compared with the old one.
- **Milestone keys say nothing:** the owner can't tell what `f2` is from its key, and types it in commands.
- **Replans earned their cost in F1:** $5.6 (7% of lead spend) for a gate blind spot (f1-33) and three wrong facts that tickets would have trusted.

## Decisions (⚑ = deviates from an earlier decision)
1. **⚑ The owner's share of the 5-hour window: 25%** (amends ADR 15 item 1). Unattended jobs, of every role, stop at 75% of Claude's 5-hour window. The last 25% is for the owner's interactive sessions.
   - A job that would pass 75% is parked like one at a limit (ADR 15 item 10) until the window has room again, and other agents go on.
   - Claude's windows stay one account: readings from Opus and Sonnet count for both, as they already do (`agent_windows`).
2. **⚑ Lead work first** (amends ADR 15 item 6). Claude takes a developer ticket only when no lead work is ready (a lead ticket, a direction, an escalation, a checkpoint, a review) and the 5-hour window is under **50%**, so a lead job that follows has room. Otherwise a developer ticket goes to the next permitted agent: Ollama Cloud, then local.
3. **⚑ Two questions, one per window, never blocking** (amends ADR 15 item 5; the owner, 2026-10-02: "if I reply then go, otherwise wait; it shouldn't be blocking if I'm not around").
   - The week's reserve question stays. Passing 75% of the 5-hour window asks its own: `Claude's 5-hour window is at 76% (resets 14:50), kept for you. Use it for this run? [y/N]`. A yes to one doesn't answer the other.
   - Asked only when nothing else can run. A yes lets the waiting work go at once and lasts for the command. No answer: the work stays parked until the window resets, then goes on by itself; the question also shows as a Needs-you item. The runner never stops for it.
4. **Support roles go through the allowance and park** (amends ADR 15 item 4's "support roles may always use the reserve" only for the 5-hour window). Checkpoints and escalations check the 5-hour window like the others, and park instead of sleeping when it's full or refused, so other agents keep working.
5. **Every job records its exact model:** a `jobs.model` column, from the harness's own report (Claude's stream, OpenCode's model id). The agent id stays the role's handle (`claude-sonnet`); pages and reports can split an agent's results by model.
6. **⚑ Named milestones** (amends `runner/instructions/task-format.md`).
   - A key is `<series><n>-<slug>`: `f2-cloud-first`, `m5-history`. The slug is a few words, short enough to type.
   - The command takes the full key or its short form (`f2`, or `5` for `m5`).
   - Ticket ids stay short, `<series><n>-<nn>-<slug>` (`f2-03-runner-status`). Frontmatter's `milestone:` takes either form. Docs are `.softfield/cards/<full key>.md` and `.softfield/reviews/<full key>.md`.
   - Existing milestones keep their keys (`m1`–`m4`, `f1`).
7. **⚑ Replans become standard at joints** (ends the F1 trial). A plan adds a replan lead ticket after any chain of three or more lead tickets whose results later tickets rely on (a schema, a probe, a new module's functions). They are not added at fixed intervals.

8. **Local still takes hard tickets when no cloud developer may** (ADR 15 item 10 unchanged; the owner, 2026-10-02). F1's local model passed 0 of 3 difficulty 5–6 tickets first time, but the GPU never idles: F2's f2-05 cuts its stuck attempts, and the step-up lifts a failed attempt to a stronger agent when one is permitted.

9. **⚑ Copilot steps in when Claude can't** (the owner, 2026-10-02; amends ADR 14 item 12 for this case). When a checkpoint is due and Claude is past 75% of its 5-hour window (or refused), Copilot does the checkpoint for real: its findings become fix tickets as Claude's would. This "emergency use" may go past Copilot's monthly pace line, up to the month's capacity (ADR 15 item 1's sweep rule doesn't hold it back); its normal use stays paced. Copilot can't review code its own model wrote, but its model is unknown (`auto`), so it isn't used on merges by a Copilot-run developer (there are none today).
10. **⚑ The bench replaces shadowing** (amends ADR 14 item 12; the owner, 2026-10-02). An agent earns a role from bench results, not from two milestones of shadowing.
    - `runner bench` gains a review mode: it replays past checkpoints (their merges) for an agent and scores its findings against the ones already known (F1's checkpoints, M3's and M4's review findings). A finding nobody knew about is listed for the lead to judge, not scored.
    - `[roles] checkpoint-shadow` is emptied; the shadow's code stays, unused. The Agents page's eligibility reads bench results.
    - **Copilot reviews, it doesn't develop:** its wrapper is read-only (a CLI with edit rights would also have git and GitHub's API), 200 credits a month go further on reviews, and its model is unknown. Developing stays with local, Ollama Cloud and Sonnet.
    - Copilot's normal use is then its bench replays, paced over its month; the 3-a-day cap only ever applied to `runner copilot-review`, the probe command headless jobs use.

## Consequences
- Unattended runs use at most 75% of each 5-hour window, about 4 of every 5 hours of Claude. Overnight, that may mean one more park per night. The owner can always plan.
- Sonnet does less developer work while lead tickets are queued. Ollama Cloud picks that up once F2 has benched it.
- A one-time migration adds `jobs.model`; earlier jobs keep it empty, except where backfill can read it from the log.

## Alternatives considered
- **A reserve of the 5-hour window only while the owner is at the keyboard:** the runner can't tell.
- **Sonnet never as a developer:** it passed 3/3 at ≈$0.40 a ticket; that's worth keeping when no lead work waits.
- **A separate allowance per Claude model:** the readings show one account window.
