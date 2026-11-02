# Review: F21, the lead's briefs

- **Status:** done, signed off by the owner on 2026-11-02.

## Sign-off sheet

### 1. What changed
- When you ask a question in the planning room ("when will the board be done?"), the lead now gets, at the top of its job, where the work stands: what is running now, the ready tickets in the exact order the runner will take them (with what each waits for, and who does it), every card with its state and place, and how long a ticket takes lately (the median of the last 20 merged). It answers from that instead of guessing.
- Every lead job (planner, lead ticket, escalation, direction, checkpoint, review) now starts with the parts of `docs/agents/lead.md` its role needs, pasted in, instead of a pointer it could skip. Your preferences (`owner.md`) reach each job through CLAUDE.md, once; the review stopped the runner pasting them a second time.
- `owner.md` was not trimmed: that part is set aside (see 3).

### 2. How to test it yourself
1. On the planning room, open a card that has ready tickets and plant or send a question: "When will this card be done, and what runs before it?"
2. The lead's reply should name the ticket running now, the tickets ahead in the same order as the overview's Next in line, and give an estimate in minutes or hours from "about N minutes a ticket".
3. Ask on a card that waits for another card's ticket: the reply should say what it waits for.
4. Optional: open the latest planner log in the run's folder; it starts with "From docs/agents/lead.md, the sections this job needs" and "Where the work stands".

### 3. Left for later
- **f21-03, trim owner.md**, is set aside in `.softfield/tasks/later/`. Your preferences grew to about 1,800 words with the rules of 13 and 22 October, and cutting only the stories saves about 50 words; going further means rewording rules, which only you can ask for. If you want a shorter `owner.md`, say so on F21's thread and the lead will propose a rewrite for you to read.
- Nothing else.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-10: f21-01 and f21-02 waited for Claude's reserve (1% of the week left) ([session](../sessions/2026-10-10-0854.md)).
- 2026-10-12: both lead tickets done by Claude Opus at the first attempt ($1.73 and $2.31), but blocked by a stray test file on main failing the layout gate; they landed from their branches in a terminal session the same evening ([session](../sessions/2026-10-12-lead.md)). f21-03 ran ($0.92) and changed nothing on purpose: the 800-word target couldn't be met without dropping rules.
- 2026-10-28: f21-03 ran again on Sonnet ($0.21), changed nothing again, and was set aside ([session](../sessions/2026-10-28-0900.md)). 0 local tokens: everything was protected runner code.
- 2026-10-29: the review was parked three times for Claude's 5-hour cap, then ran: round 1 fixed two findings itself; round 2 checked them and found only one nit, for the backlog.
- Lessons: a word-count target on a document whose rules keep growing can't hold (the ticket now has no ceiling test); a file left on main by a review blocked four finished tickets for two days (fixed then by running f12-03 first); a brief that pastes a doc must check what the agent already loads (this review's F1).

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:** watch the next few planner replies to "when will X be done?": if the estimates are still off, the block could add each card's count of tickets left and a per-card estimate, instead of one median for all. And the brief now costs about 1–2k tokens per new lead job (lead.md's sections only); if `lead.md` keeps growing, a test that keeps each role's brief under a size would catch it before it costs.

### 7. What clogged the factory line
- **Claude's weekly reserve, 10–12 October (about two days):** f21-01 and f21-02 waited for the week to reset. Unclog: nothing to change; this is what the reserve is for, and you can turn it on from the desk.
- **The layout gate on main, 12 October:** one stray test file failed every ticket's check, so two finished F21 tickets were blocked until a terminal session. The cause was a fix ticket (f12-03) with `priority: 100`, so it ran last; since F173 a feature ticket can't carry its own priority and runs in its card's place, so that cause is gone.
- **f21-03, two runs ($1.13) that changed nothing:** the target was impossible by design. Now set aside.
- **The review, parked three times on 29 October** for Claude's 5-hour window over its 75% cap: normal pacing.

## What was built
- **D1, Where the work stands** (f21-01): `loop.work_stands` builds it from the dry run's own inputs (`_dispatch_tickets`, so the order is the runner's), `loop.ticket_minutes` reads the last 20 done tickets' jobs from the metrics database, and `planner.where_it_stands` writes at most about 40 lines (past 25 ready tickets, a count). `run_planner` adds it to every planner prompt, new or resumed; a failure to build it is a report note, never a lost answer.
- **D2, Sections, not pointers** (f21-02): `prompts.SECTIONS` maps each lead role to its lead.md headings; `prompts.brief` pastes owner.md and those sections first, the same text for every job of a role (prompt cache). `call_claude` adds it to new sessions only; a resumed one has it. A missing heading is one report note, and a test against the real lead.md fails at commit if a heading is renamed. The prompts' pointers to lead.md went.
- **D3** set aside (see 3).

Tests: the commits only added tests (none edited): the block's order, waits, cards, median and 25-ticket cap; `ticket_minutes` (other projects, unmerged tickets and running jobs left out, the last 20); the brief per role, resumed sessions, missing headings, the real lead.md. They check content, not presence. Checked and fine: a ticket in flight is listed once; the median is at least 1 minute; `sections` keeps `###` subsections inside their section; lead.md has no fenced `## ` line that could be taken for a heading.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | owner.md reached every new headless lead job twice: CLAUDE.md imports it (since 2026-10-07) and the brief pasted it again, about 2.5k tokens a job | Fixed: `claude.imports` reads CLAUDE.md's `@` imports; `_brief` leaves owner.md out when it is already loaded (still pasted for another project's repo or the shared docs). Two tests |
| F2 | nit | claude | The block didn't say when a ticket runs early for another (F173 D7, merged after F21), so its place looked wrong for its priority | Fixed: `ReadyTicket.early`, "early for <id>, which waits for it". One test |
| F3 | nit | backlog | Round 2: `work_stands` passes `early_for` by position right after `waits` (both `str \| None`, so mypy can't catch a swap), and no `work_stands` test has a pulled-ahead ticket | Right today; in `docs/backlog.md`: pass both by name and test it when `ReadyTicket` next changes |

Round 2 re-read the fixes. F1 holds: only an `@docs/agents/owner.md` line of its own counts (the test checks that an inline mention still gets the paste), the shared docs (ADR 30) still get it pasted, and a repo without owner.md isn't reported as missing. This review's own prompt shows it live: lead.md's sections, and owner.md once, through CLAUDE.md. F2 holds: the field is the dry run's own `early_for`. Neither fix edited an existing test.

No checkpoint ran (all lead tickets), so there are no checkpoint verdicts. Score: 7/10: both decisions are built as planned, with clear, thorough tests; the brief duplicated what CLAUDE.md already loads, which the ticket's author could have seen in CLAUDE.md.

After the fixes, ruff, mypy and the 1,740 runner and 1,102 dashboard tests pass (round 1). Round 2 re-ran them on a slow machine: every runner test passed (the full run was stopped at its 20-minute limit at about 95%, with no failure before it), and all 1,102 dashboard tests passed on their own in 16 minutes.

The French: no `coucou/locale/fr/` change in this milestone.

## Backlog
- F3 (nit, round 2), in `docs/backlog.md` under "Waiting for something".

## Factory
- Flow: three lead tickets, all first attempt on Claude; two blocked by a broken main (not their work) and landed by hand; one set aside as impossible. No stops for the owner. The review waited for the 5-hour cap three times.
- Models: Claude Opus built D1 and D2 ($4.04); Opus and Sonnet ran f21-03 for nothing ($1.13). The local model had no part (protected code).
- What to change: when a plan pastes text into prompts, the ticket should name what the agent already loads by itself (CLAUDE.md and its imports). Added to the finding; once is not a pattern yet.

<!-- runner report -->
<!-- /runner report -->
