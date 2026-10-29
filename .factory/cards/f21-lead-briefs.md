# Milestone F21: the lead's briefs

> **Status: planned** (2026-10-07, with the owner, in a terminal session). **State:** ready · **Priority:** 5 · **Area:** factory
> The owner planted questions (F12–F19) that went unanswered, then asked whether the lead checks the plan and reads lead.md when it answers. The planner logs of 2026-10-07 say no: neither planner job opened `docs/agents/lead.md`, and only one looked at `.factory/tasks/` and `state.json`. Prompts name lead.md's sections but don't give them.

## Outcome
- A planner job knows where the work stands: what runs now, what goes next in the runner's own order, each card's state and priority, and how long tickets take lately. It answers "when will X be done?" from that, not by luck.
- Every lead job gets the parts of the owner's preferences and lead.md it needs, in its prompt, not as a pointer it may skip.
- `docs/agents/owner.md` holds rules, not stories, so every job reads less.

## Decisions
- **D1 The plan in the planner's prompt:** `planner.prompt` gets a "Where the work stands" block, built by the runner from the same inputs as `dry_run_plan` (`runner/loop.py`): the ticket in flight (`in_flight` in `.factory/var/runs/state.json`), the ready tickets in pick order (`run_order` in `runner/tasks.py`) with their milestone, who does them and what each waits for, every card's state and priority, and the median duration of the last 20 merged tickets (from `jobs`). At most ~40 lines: past 25 ready tickets, a count.
- **D2 Sections, not pointers** (owner, 2026-10-07: "will the benefits be worth the extra cost?" Yes: about 3k tokens, a few percent of a lead ticket, mostly cache reads). The runner pastes, at the very start of each lead prompt, `docs/agents/owner.md` and the `lead.md` sections its role needs:

  | Role (prompt) | lead.md sections |
  |---|---|
  | planner (`PLANNER`, `PLANNER_GENERAL`) | Authority, Plan, Planning room, Tickets |
  | lead ticket (`LEAD_TICKET`) | Your own work, Tickets |
  | escalation (`ESCALATION`), direction (`DIRECTION`) | Known range, Escalations, Your own work |
  | checkpoint (`CHECKPOINT*`), review (`REVIEW`) | Review, Sign-off sheet, Reporting |

  - Sections are found by their `## ` heading. A heading the map names that is missing fails a test, not a run: the job then goes with what was found and a report note.
  - A planner job resuming its thread's session gets none: the session has them.
  - The prompts' "as docs/agents/lead.md says (…)" pointers go: the text is there.
- **D3 Trim owner.md:** the lead rewrites `docs/agents/owner.md` so each preference is one rule with its date, and the story behind it goes (the incident that taught it stays in the milestone or review doc it came from). No rule is dropped or changed in meaning. Target: under 1,200 words (1,380 today). It was 800 until 2026-10-12: f21-03's first run showed that cutting only the stories gives 1,157, and that going lower means dropping or rewording rules, which is the owner's to ask for. The owner reads the diff at F21's review.
  - **As found (2026-10-28):** f21-03 was blocked a second time, changing nothing. owner.md had grown to 1,802 words with the rules of 2026-10-13 and 2026-10-22, and cutting only the stories saves about 50, so no target under the "don't reword a rule" limit can be met. The ticket is set aside in `.factory/tasks/later/`, without a word-count test (a ceiling would block adding preferences); F21 closes on D1 and D2.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | planner-sees-the-plan | L | 5 | – | D1 |
| 02 | sections-in-prompts | L | 4 | – | D2 |
| 03 | trim-owner | L | 2 | – | D3 (set aside 2026-10-28) |

All lead: `runner/` and `docs/agents/` are protected.

## Notes
### From F181: Why is f21-03 blocked? What should I do with it (merged by the lead on 2026-10-29)
Why is f21-03 blocked? What should I do with it

What was said on F181's thread:
The owner asked why f21-03 is blocked and what to do with it. The answer and the replan that sets the ticket aside are already on F21's thread, waiting for the owner's Approve.
