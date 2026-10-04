# F4 review: always on

- **Status:** done, signed off by the owner on 2026-10-04.
- **Reviewed:** `git diff f4-always-on-start..main`, 2026-10-04, by the lead (headless). The diff also holds F3, which ran interleaved and has its own review ([f3.md](f3.md)). This review read F4's tickets (01–20, 33), their fix tickets (22–38, including the F3 ones filed under F4), and how F3's changes touched F4's outcome.

## Sign-off sheet

### 1. What changed
- **The runner can stay on.** `uv run runner run` now does everything `runner milestone` did: when a milestone's tickets are all done, it reviews it, writes the verdict, and carries on with other milestones' tickets (f4-20; F3's review was the first).
- **Claude's work waits its turn without stopping the line.**
  - After a yes to the 5-hour question, the escalations and checkpoints parked for it go first (f4-01).
  - A new session takes a fresh reading of Claude's windows, with a tiny Haiku call, instead of trusting the last session's (f4-07).
  - A requeued ticket is checked before it is committed (f4-03).
- **Fewer wasted attempts.**
  - The runner formats and autofixes a developer's Python before the gates (f4-11).
  - OpenCode's shell no longer kills `check-all` after 2 minutes (f4-05).
  - A process an agent leaves behind dies with it.
  - A bench copy can't edit your checkout any more (f4-19).
- **Tickets can wait aside.** `tasks/later/` holds tickets the runner never takes; `uv run runner queue <id>` puts one back. A milestone doc may say `After: <key> signed off` (f4-15).
- **The dashboard.**
  - The Tickets page lists the latest work first, with "Last worked", and a "Set aside" panel with each ticket's queue command.
  - Now shows the goal and "read N tokens · M turns".
  - The Queue sits beside Now and refreshes with it.
  - Nothing refreshes while you scroll or have text selected.
  - The Agents page says "before 2 Oct (model not recorded)".
- **Fix tickets land in the right milestone, with real paths** (f4-33).
- Mum sees nothing new: F4 is factory-only.

### 2. How to test it yourself
1. `uv run runner dashboard --host <this machine's Wi-Fi address>`, then open `/tickets`: the most recently worked ticket is first, with "Last worked". The "Set aside" panel lists the tickets in `tasks/later/` with `uv run runner queue <id>`. Its links keep `?project=` (fixed by this review).
2. Select some text in Now or the Queue and wait 10 s: it stays selected. Scroll the page, and the live parts wait 10 s before refreshing.
3. With the runner idle: `uv run runner queue f3-31` moves that ticket to `tasks/ready/` in a commit of its own. With a run live, it refuses and says why.
4. Leave `uv run runner run` going: when a milestone's last ticket merges, its review starts by itself, and the run then goes on with the next milestone's tickets.
5. On your phone, open the Agents page: an agent that ran on several models has a "before 2 Oct (model not recorded)" row for its old jobs.
6. After f4-39 merges: on the Overview, a Next in line ticket that waits says what for ("waits for Claude", "waits for … 's escalation").

### 3. Left for later
- **Not done from F4's outcome:**
  - The allowances at the top (f4-12) and the reserve marks (f4-16) are in `tasks/later/`, since f3-18 and f5-14 cover most of them.
  - Sonnet as the step-up only (f4-13) stays in `later/` until F4's numbers argue for it.
  - "What waits for what" on the Overview reaches you after f4-39 (finding f4-always-on-F1).
- **Backlog:** three nits from this review in `docs/backlog.md` (`[f4-review …]`):
  - the dashboard doesn't show an `After:` hold yet;
  - the Tickets page's milestone link and filter form lose `?project=` (older than F4);
  - two duplicate queue tests.

### 4. Decisions waiting for you
- None new from F4. **[ADR 21](../adr/21-gate-every-test-file.md)** (gate every test file) is still Proposed, from F3's review. It matters for f4-39 too: that ticket lists `test_overview.py`, so while it is ready, the Overview's tests run in no gate.

### 5. How the work went
| Session | F4 merged | Not merged | Local tokens | Claude (token-equivalents) |
|---|---|---|---|---|
| [2026-10-02 23:44](../sessions/2026-10-02-2344.md) | f4-01 | – | 0 | ≈0.2M |
| [2026-10-03 07:17](../sessions/2026-10-03-0717.md) | f4-03, f4-02 (finished by the lead) | – | 41k | ≈0.7M |
| (no report, 2026-10-03 morning) | f4-04, f4-06, f4-08, f4-10 | – | – | – |
| [2026-10-03 18:16](../sessions/2026-10-03-1816.md) | f4-05 | – | 6.2M | ≈1.0M |
| 19:38–20:05, four short runs | f4-07, f4-09, f4-11, f4-15 | – | 0 | ≈1.7M |
| (no report, 2026-10-03 evening) | f4-17, f4-18, f4-22 | f4-23 implemented by the lead; f4-21 blocked, then dropped | – | – |
| [2026-10-03 23:39](../sessions/2026-10-03-2339.md) (12 h) | seven fix tickets (f4-25, 27, 30, 31, 32, 34, 35) | f4-24, f4-28, f4-29, f4-36 implemented by the lead | 22.9M | ≈3.6M |
| [2026-10-04 11:35](../sessions/2026-10-04-1135.md) | f4-37, f4-38, f4-20 | f4-26 (nothing left to do) | 3.0M | ≈1.5M |
| [2026-10-04 14:26](../sessions/2026-10-04-1426.md), [14:37](../sessions/2026-10-04-1437.md) | f4-19, f4-33 | – | 0 | ≈0.3M |

The lessons that mattered:
1. **Lead tickets for the runner went smoothly:** all ten merged first time. Runner work stays with the lead.
2. **Developer tests check presence, not content.** Five of the seven dashboard tickets needed fix tickets for weak or vacuous tests, and some fixes needed their own fixes (f4-31 made the "Set aside" panel follow the state filter; f4-38 undid it). What changed: Known range in lead.md now says to spell out what each assertion must reject.
3. **Tests-only fix tickets can't pass** (f4-24, f4-26, f4-36). What changed: pre-flight now hands them to the lead (F3's review).
4. **The Copilot stand-in found real bugs but filed them badly:** wrong milestone, `coucou/…` paths. What changed: f4-33.
5. **One milestone's plan can quietly undo another's outcome:** f3-05 removed the Queue table that showed what each ticket waits for. No checkpoint reads across milestones; this review caught it (f4-always-on-F1).

### 6. What next
- **Product:**
  - Steering from the phone (F5's board: sign off, queue a `later` ticket, answer the 5-hour question) would turn F4's "always on" into something you can run from the sofa.
  - For Mum, a small product milestone (ADR 10's gallery, or the duck key) is overdue: nothing has changed for her since M4.
- **Factory:**
  - Accept ADR 21 before F5's Overview tickets run.
  - Give dashboard tickets a Done when that names what each assertion must reject, so fixes stop needing fixes.
  - When a plan in one milestone removes a panel or a field, check the other milestones' outcomes that relied on it (a line in the replan's checklist).
  - Tag `<key>-start` at each plan session, so a review reads only its own milestone.

### 7. What clogged the factory line
This headless review can't query the metrics database (its shell is limited to the check commands), so these come from the session reports. The milestone page on the dashboard has the exact hours.
- **Fix-ticket churn:** 12 fix tickets on F4's dashboard work. Five of them ended with the lead: f4-24, f4-28, f4-29 and f4-36 after three attempts each, mostly in the 12-hour night run, and f4-26 at pre-flight. Unclog: Done-when lines that name what an assertion must reject, and the lead writing tests-only fixes directly.
- **Restarts:** most short sessions ended with "the runner needs a fresh process" after a lead ticket changed `runner/`. `runner run` restarts itself now (f46c9d9), so these cost seconds.
- **Waits for Claude's limit:** none recorded in F4's sessions.

## What was built
- **The runner:**
  - `runner/loop.py`:
    - `fresh_reading` (f4-07);
    - `_support_goes_first` (f4-01);
    - `_repair_requeue` (f4-03);
    - `queue_ticket` and `live_run` (f4-09);
    - the formatting step before the gates (f4-11, `gates.autoformat`);
    - `_held` (f4-15);
    - fix tickets in the at-fault milestone with checked paths (f4-33).
  - `runner/milestone.py`: `milestone_after`, `signed_off`, `waits_for` (f4-15).
  - `runner/bench.py`: a copy with its own root commit (f4-19).
  - `runner/local_model.py`: OpenCode's shell timeout (f4-05).
  - `runner/procs.py`: agents die with the runner, and nothing outlives an agent.
  - `runner run` reviews due milestones (f4-20).
- **The dashboard:**
  - `/tickets`: last worked, newest first, the Set aside panel.
  - Now: the goal and tokens.
  - The Queue: in `/live`, beside Now, with `overview.queue`'s reasons.
  - `liveIdle`: no refresh while you scroll or select.
  - The Agents page's model label.

## Findings and resolutions
| Id | Severity | What | Route | Resolution |
|---|---|---|---|---|
| f4-always-on-F1 | should-fix | F4's outcome says the Overview answers "what waits for what". `overview.queue` still works out each ticket's reason (a dependency, an escalation, Claude), but since f3-05 no page shows it. The crate card lists only dependency ids. | developer | **Ticket [f4-39](../../tasks/ready/f4-39-next-in-line-says-why.md):** each Next in line row says what it waits for. |
| f4-always-on-F2 | should-fix | The "Set aside" panel's ticket links drop `?project=` (f4-18), so on a second project they open the default project's ticket, or a 404. | lead | **Fixed:** the links carry `{{ q }}`. The panel test checks the exact `href`. |
| f4-always-on-F3 | nit | `list_later_tickets` still said it filters by state, and `test_later_tickets_respects_state_filter` tested the opposite (C366-2). `agents.py`'s comment had non-ASCII hyphens and a garbled date. | lead | **Fixed:** docstring, test renamed `…_ignore_the_state_filter`, comment rewritten. |
| f4-always-on-F4 | nit | The runner honours `After: <key> signed off`, but the Overview and the floor would still list a held ticket as next in line. No milestone uses `After:` yet. | backlog | Backlog. |
| f4-always-on-F5 | nit | `/tickets`: the milestone link has two `?`, and the filter form drops `?project=` (older than F4). | backlog | Backlog. |
| f4-always-on-F6 | nit | Two queue tests assert the same thing; two tickets tests duplicate the `later_client` setup. | backlog | Backlog. |

`tests/unit`, `tests/integration`, `tests/runner` and `tests/factory_dashboard` all pass (1473 passed, 1 skipped, before the fixes above; `test_tickets.py` and `test_agents.py` after them). `ruff` is clean.

### The checkpoints' findings
- **Confirmed and fixed (20 of 21):**
  - C228-1 by f3-17: the first draw sets the counts without a flash.
  - C228-2 and C228-3 by f4-22 and f4-23.
  - C228-4 by f4-24.
  - C231-1…5 by f4-25…29 (C231-2 by f4-36's escalation).
  - C292-1/2 by f4-31 and f4-32.
  - C334-1 by f4-36.
  - C334-2 and C334-3 by F3's review.
  - C350-1/2/3 by f4-37.
  - C356-1/2 by f4-38.
  - C366-2 by this review.
- **Rejected (1):** C366-1. The "updates between polls" test proves the new ticket reached `/live`: the Queue's count there rises by one. The page lists only the first three rows, so the id can't be checked in it. The extra database check is redundant, not wrong.
- **Missed (1):** F2. f4-18's template was in the diff the checkpoint after f4-17 and f4-18 read, and the link sat beside the main table's, which keeps `{{ q }}`. F1 came from f3-05, finished by the lead, which no checkpoint reads.

### Tests the developers edited
- **f4-25** deleted two tests; f4-36's escalation restored them.
- **f4-30** made the queue tests vacuous; f4-37 repaired them, and they now compare the whole `waits` map.
- **f4-31 and f4-32** rewrote the "Set aside" tests around the state filter. f4-38 reversed the behaviour and fixed the row count, but left a misnamed test (fixed here).
- **f3-18, f3-19, f4-34, f4-35:** F3's review covered them.

### French
Nothing user-facing for Mum changed: the dashboard is the admin side and stays English (ADR 00 A2). No strings in `coucou/locale/` changed.

## Workflow observations (Factory)
- **Flow:**
  - Interleaved with F3 over about 40 hours, with no stop for the owner and no wait for Claude's limit.
  - The Copilot stand-in took three checkpoints while Claude was busy; Sonnet took the rest.
- **Models:**
  - Opus did every lead ticket first time.
  - Qwen passed the small dashboard tickets, but most needed fix tickets for their tests.
  - gpt-oss-120b passed f4-17 in two attempts (5.5 minutes of model time).
- **What to change:**
  - Accept ADR 21.
  - In fix tickets, list the neighbours of the finding's line (F3's lesson again: f4-31 fixed the milestone filter and broke the state one).
  - Have replans check other milestones' outcomes when a plan removes a panel.
- **Stop reason:** none. Round 1 leaves one developer ticket (f4-39); its checkpoint follows it, and round 2 re-reads it.

<!-- runner report -->
<!-- /runner report -->
