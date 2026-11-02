# ADR 32: Sonnet does the easier lead tickets, Opus steps in when it fails

- **Status:** Accepted (by the owner, 2026-10-20)
- **Date:** 2026-10-20
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 12](12-junior-feedback-and-checkpoints.md) item 9 (a lead ticket gets one attempt, then is blocked) and the lead-ticket rows of `[roles]` ([ADR 14](14-developers-and-agents.md) item 2): until now every lead ticket ran on Opus.
- **Evidence:** F153, the owner (2026-10-20): "I wonder if sonnet would be good enough to do the lead tickets. And keep opus for planning, sonnet for execution." Since 2026-10-06, lead tickets cost $120 of Claude's $438 (51 passed, 3 failed, $2.35 each); the planner $195. On 2026-10-19 five Claude jobs were parked until 17:00 at the 5-hour window, which Opus and Sonnet share. Sonnet has never done a lead ticket; as a developer it went 3/3 first time (ADR 17), and as the checkpoint it finds real bugs (ADR 15).

## Context
- A lead ticket is the lead's own work: protected paths, security, anything test-first. Today it is one Opus attempt; `check-all` fails → blocked, and the lead looks at it (ADR 29). Its merge is never checkpointed; only the milestone review (Opus) reads it.
- Lead tickets are written for a fresh session with no memory of the plan (lead.md, "Your list is tickets too"): goal, files, Decisions in the card doc, acceptance criteria. Much of the judgement is already in the ticket, which is what makes the question fair.
- Each job records its exact model (`jobs.model`, ADR 16 item 5), so the results of each model can be read apart.

## Decisions (draft; ⚑ = deviates from an earlier decision)
1. ⚑ **Sonnet takes the lead tickets of difficulty 4 or below; Opus keeps 5 and up, and any ticket with no difficulty.** `[roles] lead-ticket` lists two agents, Sonnet then Opus; `[claude] lead_first_up_to = 4` says where the first stops. With the setting absent (0), or one agent listed, nothing changes.
2. **No checkpoint on lead tickets, whoever wrote them,** as today. The milestone review (Opus) is the one review of Sonnet's lead work, as it is of Opus's.
3. ⚑ **A Sonnet lead ticket that fails `check-all` gets one Opus attempt on its branch** before it is blocked, the step-up developers already have (ADR 15 item 7). Fails again → blocked, and ADR 29's look follows.
4. **Every lead merge names the agent that did it,** in the ticket's record and the run's report, so the board and the metrics show "claude-sonnet" where Sonnet worked.
5. **Opus keeps planning, reviews, escalations and directions,** as the owner asked; the planner rule of 2026-10-07 ("Planning is worth Opus") stands.
6. **A trial, read at the next factory review** after about 15 Sonnet lead tickets: first-time pass rate for each model, the milestone reviews' findings in Sonnet's lead work against Opus's, dollars per ticket for each (Sonnet's including its Opus step-ups), and how often Claude was parked. Then widen to every lead ticket, keep, or go back (`lead_first_up_to = 0`).

## Consequences
- **Cost:** two lead tickets (f153-01, f153-02) on Opus, about $5. On the trial, a Sonnet ticket should cost well under Opus's $2.35; each failure adds an Opus step-up, so the real saving is what item 6 measures, not a list price.
- **Risk:** Sonnet writes protected code, and a flaw that passes `check-all` is first seen at the milestone review, after later tickets may have built on it. Item 6 compares the reviews' findings, and the trial stops there if Sonnet's lead work shows more of them.
- **Risk:** more parked work if Sonnet's attempts are longer. They count in the same 5-hour window; item 6 reads it.

## Unchanged
- Who plans (Opus), the queue order, `check-all` as the only merge gate, checkpoints for developers' merges only, developers' routing, the Copilot stand-in, ADR 29's look at a blocked ticket.

## Settled with the owner
1. **Where Sonnet stops: difficulty 4** (owner, 2026-10-20, agreed as recommended): item 1.
2. **No checkpoint on Sonnet's lead merges** (owner, 2026-10-20: "no checkpoint needed"). The first draft sent them to an Opus checkpoint; the milestone review stays the one check, as for Opus's lead tickets: item 2.
