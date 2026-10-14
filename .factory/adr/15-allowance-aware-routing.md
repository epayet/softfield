# ADR 15: Spend the cloud allowances first, paced; local is the floor

- **Status:** Accepted (by the owner, 2026-10-01)
- **Date:** 2026-10-01
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 14](14-developers-and-agents.md) items 3, 6 and 9; `docs/workflow.md`'s reset of the branch at attempt 3, which ADR 12 item 6's direction relies on
- **Shaped with the owner:** in the f1 mid-milestone review, 2026-10-01, item by item. The owner chose the four numbers below.

## Context

**The owner's priority has changed:** getting things done comes before learning about the local models. M1–M4 and f1 (17 developer tickets) already give enough evidence about them.

**Unused allowance is lost.** Claude Pro has a 5-hour rolling window and a weekly one. Copilot Free has a monthly one, and Ollama Cloud has its plan's. Today the factory spends Claude only on lead work and uses local for everything else, even on a Sunday evening with the week's Claude allowance untouched.

**Evidence from f1** (metrics database, 2026-10-01):
- **Developer tickets:** 11 of 17 merged at the first attempt.
- **Support cost:** $10 of headless Claude in all (directions, escalations, checkpoints), and **$8.06 of it on the 6 tickets that failed**. A first-time pass costs about $0.17 (its share of checkpoints).
- **f1-34:** spent $2.40 on 6 attempts and 2 escalations to land a 57-line fix. Every retry and requeue started again from main, though attempt 3's work was nearly right.
- **The lead's own tickets:** cost $2.9 per 1,000 lines (f1-04–06: $9.13 for 3,155 lines).
- **Checkpoints on Sonnet:** $0.24 each, and they found 4 real bugs.
- **A limit pause idled the GPU too:** f1-03, 2026-09-30 18:39, 15 min.
- **A Ctrl-C left a dirty main:** the next run refused to start (2026-10-01, the interrupted review).
- **Claude Code reports its allowance in headless runs** (probed 2026-10-01 with Claude Code 2.1.286, `claude -p … --output-format stream-json --verbose`). The stream has a `rate_limit_event`:
  ```json
  {"type": "rate_limit_event", "rate_limit_info": {"status": "allowed_warning",
   "rateLimitType": "seven_day", "utilization": 0.79, "resetsAt": 1791216000,
   "surpassedThreshold": 0.75, "isUsingOverage": false,
   "unifiedWindows": {"five_hour": {"utilization": 0.07, "resetsAt": 1790883600},
                      "seven_day": {"utilization": 0.79, "resetsAt": 1791216000}}}}
  ```
  These are real numbers, from our own jobs, without touching the OAuth token. That day the week stood at 79% used, with the reset on Monday 5 October at 17:00 BST.

## Decisions (⚑ = deviates from an earlier decision)

### A. Allowances
1. **One rule for every agent,** a pure function (`runner/allowance.py`): "may agent A take a job of expected cost `c` now?" Each agent has one or more **windows**, each with a kind, a capacity, its usage and its reset.
   - **Fixed windows** (Claude's week, Copilot's month, Ollama's plan) are **paced**:
     - **Spread:** yes if `used + c ≤ (capacity − reserve) × elapsed / length`.
     - **Sweep:** in the **last 10%** of the window (about 17 h of a week, 3 days of a month), yes while `used + c ≤ capacity − reserve`.
   - **Rolling windows** (Claude's 5 h) are a **cap**, not a pace: yes while `used + c ≤ capacity`. They refill by themselves.
   - **Several windows:** all must say yes.
   - **Local:** has no window, so it always says yes. It is the floor.
   - **`c`:** the median cost of that agent's past jobs at that difficulty, in tokens or requests.
2. **⚑ Windows and capacities are learned, not maintained** (amends ADR 14 item 3).
   - **A window's kind and length** come from the resets seen: hours away means rolling; days means weekly or monthly. Claude names its windows.
   - **A refusal** sets the capacity at the usage it came at, so a lowered limit is found at once.
   - **During the sweep,** an agent may go past its learned capacity until refused. A refused call costs nothing, so a raised limit (Copilot 50 → 200) is found within one window.
   - **Unknown capacity** (Ollama today): used until refused. Then it is skipped until the reset, or, with no reset given, for 1 h and then until the next window. It never keeps failing.
   - Config values only seed a new agent.
3. **Readings:**
   - **Claude:** headless jobs switch to `--output-format stream-json --verbose`. The adapter records each `rate_limit_event`'s `unifiedWindows` as `usage_events` readings (window, utilization, reset). Capacity is then 100% of each window, and usage is the fraction reported. Fallback: our own spend per window, calibrated by refusals.
   - **Ollama:** our own token counts.
   - **Copilot:** our own request counts.
4. **Claude's reserve: 30% of the weekly window,** kept for the lead's support roles: reviews, escalations, directions, checkpoints, and the owner's planning sessions. Lead tickets and developer work share the rest. So early in the week developer work is modest, and on a Sunday evening with the week unused Claude takes developer tickets.
5. **Dipping into the reserve asks the owner.**
   - **When it asks:** the runnable work is blocked only because Claude is down to its reserve. That means a lead ticket, or a developer ticket no other agent may take. Work that doesn't need the lead runs first, so the question comes only when nothing else can run.
   - **On the console:** the runner asks `Claude is at its reserve (N% left of the week, resets <time>). Use it for the rest of this run? [y/N]`, and waits for an answer until the week resets; then the reserve no longer applies and the ticket runs. (Amended by the owner, 2026-10-01: it waited 10 minutes and asked first, so a late yes was lost while f1-48 could have run.)
   - **A yes holds for the rest of the running command,** including the runner's own restarts after a runner change. It isn't stored: after a Ctrl-C and a rerun, if the allowance is still low, it asks again.
   - **No answer, or no:** the ticket is parked (item 10), other permitted work goes on, and the question becomes a **Needs you** item on the dashboard. Rerunning the command asks again.
   - **Later:** the dashboard may ask too (`docs/roadmap.md`).

### B. Who does a ticket
6. **⚑ Cloud first** (amends ADR 14 item 9). A developer ticket is assigned **when it's picked**, not when it's planned: to the best-rated agent that covers its difficulty and that the allowance rule permits; else local.
   - Claude Sonnet and Opus may be developers.
   - Protected code, tickets, ADRs and the final review stay with the lead (ADR 14 item 11, unchanged).
7. **⚑ Step up, and build on the work** (amends the reset at attempt 3 in `docs/workflow.md`, for every agent).
   - **Who goes next:** after a failed attempt, the next goes to the cheapest permitted agent rated **at least 2 points above** the one that failed. Otherwise the same agent retries with the gate output, and then the lead finishes. This isn't a fixed ladder; with today's ratings it works out as local → Sonnet → Opus.
   - **From where:** the next attempt **continues on the branch**. It resets to main only when the work is judged unusable: a direction or escalation says so, or the attempt timed out before its first edit.
   - **Ollama is not a rung:** its large models aren't clearly stronger than the local Qwen at agentic coding. It is one more developer while it has allowance, until the bench says otherwise.
8. **A new escalation outcome, `finish`:** the lead continues on `task/<id>`, the gates and `check-all` must pass, and the merge credits both agents.
9. **⚑ One capacity rating per agent** (amends ADR 14 item 6).
   - Coding results and review verdicts (confirmed, rejected, missed) move the same Elo rating.
   - **A reviewer is always a different model from the author,** compared by model, not harness: Opus through Copilot is still Opus.
   - The lead's own work isn't reviewed by itself.
   - When Sonnet develops, the checkpoint goes to another model.

### C. Resilience
10. **The GPU never idles while a cloud agent waits.**
    - A job stopped by a limit, or waiting on the reserve, is **parked**: its wip committed to its branch, its session id and reset in `state.json`.
    - The queue goes on with permitted agents (local at worst), and a parked job resumes first after its reset.
11. **Recovery after an interruption** (Ctrl-C, crash or reboot).
    - The runner writes the in-flight job (kind, ticket, branch, agent, session id) to `state.json` when it starts.
    - The next `runner milestone` resumes it on a dirty tree instead of refusing:
      - **a Claude job:** its changes are committed to its branch and its session resumed
      - **a local attempt:** counted as timed out
      - **its row:** marked interrupted
12. **Errors are classified once, for every agent.** Each adapter returns `limit(window, resets_at)`, `transient` or `failure`. The loop owns waiting, parking and retrying, with the policy already on main for Claude (`c2e7428`):
    - **A limit:** wait for its reset; with no reset given, retry every 15 min.
    - **A transient error:** retry after 1, 5 and 15 min, then fail.

### D. Seeing it
13. **Dashboard: who did the work.**
    - **Ticket page:** each agent's part (attempted, reviewed, finished, merged), with lines and dollars.
    - **Milestone page and Overview:** the share of work by agent as a stacked bar, and each window's allowance before and after the milestone on a timeline.
14. **Console:** every line names its agent in brackets (`[claude-opus]`, `[local-qwen3.6]`), including parking, step-ups and the reserve question. f1-42 builds the base.

### E. Later (`docs/roadmap.md`, not built in f1)
- Running a cloud job and a local job at the same time, in worktrees.
- **A monthly "offers watch":** a lead job with web search that checks each plan's limits, its privacy and training terms, and new free tiers. It writes a dated note and proposes changes, never applies them.
- **A one-off free-tier survey:** GitHub Models, Groq, Cerebras, Mistral, Gemini CLI, OpenRouter's `:free` models and Qwen Code, each checked for training on data, retention, limits and headless use.

## Consequences
- **f1 grows by about 6 lead tickets and 1 developer ticket,** placed by `depends_on` (`.factory/cards/f1.md`, Tickets).
  - f1-20, f1-24 and f1-25 are amended to follow items 6–9 and 12.
  - f1-30 is replaced by item 13.
- **No cloud developer goes live** until the allowance rule and Claude's readings are merged: without them the pacing is blind.
- **Risk:** with cloud first, Claude's weekly allowance runs out sooner. The 30% reserve and the reserve question (item 5) protect the lead's work.
