# Milestone F153: Sonnet does the easier lead tickets, Opus keeps planning and checks

> **State:** ready · **Priority:** 3 · **Area:** factory
> Planted by the owner on 2026-10-20.

## Notes
I wonder if sonnet would be good enough to do the lead tickets. And keep opus for planning, sonnet for execution.

## What we know (2026-10-20, from the metrics database)
- Claude's spend since 2026-10-06 (API-equivalent): planner $194.6 (130 jobs), lead tickets $120.0 (51 passed, 3 failed, $2.35 each, about 22 min), review $56.3, escalation $34.1, direction $26.1, checkpoint on Sonnet $6.7 (34 jobs), probe on Haiku $0.4. Lead tickets are about 27% of the $438; the planner about 44%.
- Opus has done every lead ticket since F1 (ADR 02's Q3: "Opus merged all 28 lead tickets"). Sonnet has never done one: there is no evidence either way on its quality there, only as a developer (3/3 first time, ADR 17) and as the checkpoint (found real bugs, ADR 15).
- Claude's limits still bite: on 2026-10-19 a checkpoint, a review and three planner jobs were parked until 17:00 (`work_queue.not_before`). Opus and Sonnet share the one 5-hour window (ADR 16 item 1).
- How a lead ticket runs today (`run_lead_task`, `_settle_lead_task` in `runner/loop.py`): one attempt on `[roles] lead-ticket`'s first agent (`claude-opus` in `~/.config/softfield/factory.toml`); `check-all` fails → blocked, and the lead looks at it (ADR 29). Its merge is never checkpointed: `note_merge` returns early for anything but a developer's ticket, so the only review is the milestone review on Opus.
- `router.route` gives any non-developer role its first candidate; `call_claude` already takes a `routed` agent. `jobs.model` records the exact model (ADR 16 item 5), so the trial can be read straight from the database.
- Lead tickets' difficulty (1–10) is mostly 3–5 (F12, F14, F15, F101, F109, F110, F114: 34 tickets, 12 at 3 or below, 11 at 4).

## Decisions (draft, ADR 32)
- **D1. Sonnet takes the lead tickets of difficulty 4 or below; Opus keeps 5 and up.** `[roles] lead-ticket = ["claude-sonnet", "claude-opus"]`, and a new `lead_first_up_to = 4` in `[claude]` of factory.toml (`Config.lead_first_up_to`, default 0). The first agent the role lists takes a lead ticket whose difficulty is at most that number; the second takes the rest, and a ticket with no difficulty. With the default 0, or one agent listed, every lead ticket goes to the last agent listed (one agent: that one), so today's config behaves as today. The router decides, in `runner/router.py` (`route` for role `lead-ticket`, with the ticket), with one reason line: "claude-sonnet, a lead ticket of difficulty 3 (the first agent up to 4)".
- **D2. No checkpoint on lead tickets, Sonnet's included** (owner, 2026-10-20: "no checkpoint needed"). A lead merge adds nothing to `state.unchecked`, as today; the milestone review is its one review.
- **D3. A Sonnet lead ticket whose `check-all` fails gets one Opus attempt on the same branch** before it is blocked: the step-up, as for developers (ADR 15 item 7). Opus's session starts fresh with the ticket and `check-all.txt` to read. Fails again → blocked, and ADR 29's look follows.
- **D4. Every job records the agent that did it.** `record_ticket(merged_by=…)`, and the "merged" line (`_merged_line`) name the routed agent, not `cfg.agent_for(role)`. The commit trailer stays `agent=claude-headless` (`CLAUDE_HEADLESS_AGENT`), as today.
- **D5. Planning, reviews, escalations and directions stay on Opus**, as the owner asked.
- **D6. The trial is read at the next factory review**, after about 15 Sonnet lead tickets: first-time pass rate, the milestone reviews' findings in Sonnet's lead work against Opus's, dollars per ticket for each model (Sonnet's including its Opus step-ups), and the 5-hour window. Then: widen (all lead tickets), keep, or go back (`lead_first_up_to = 0`, a config change).
- **D7. The switch is two lines of the machine's config, set once f153-01 and f153-02 are on main:** `lead-ticket = ["claude-sonnet", "claude-opus"]` under `[roles]` and `lead_first_up_to = 4` under `[claude]` in `~/.config/softfield/factory.toml`. A headless job can't write outside the repo, so the lead sets them in the next terminal session (or the owner does). Until then nothing changes, and going back is the same two lines.
