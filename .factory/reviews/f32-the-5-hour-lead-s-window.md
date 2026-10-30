# Review: F32, the 5-hour lead's window

- **Status:** review round 2 done (2026-10-30): round 1's one should-fix is confirmed fixed and no new finding; the loop stops here, waiting for the owner's sign-off.

## Sign-off sheet

### 1. What changed
- In the planning room, the lead window's two rows now say when each window resets: "5-hour window 80% · resets at 14:00 · planning may go past the 75% line, the factory stops there", and "week 60% · resets on Nov 1 12:00".
- When a row has no fresh reading, it says why instead of a bare "–": "reset since, no new reading" when the last reading's reset has passed, "no data yet" when there has never been one. The words are the Overview's own, so both pages always agree.

### 2. How to test it yourself
1. On your phone, open the dashboard's planning room.
2. Look at the lead window at the top: the 5-hour row should read its percent, then "resets at HH:MM" (or "resets on <month> <day> HH:MM" if it is tomorrow or later), then the sentence about the 75% line.
3. The week row under it should show its own reset the same way.
4. Open the Overview: its Claude allowance rows should give the same reset times.
5. Optional, after a quiet spell with no Claude job (the 5-hour window passed its reset): the planning room's 5-hour row reads "reset since, no new reading" instead of a percent.

### 3. Left for later
- One gap in the review's new check, in `docs/backlog.md`: a requeued ticket whose branch holds work that no longer merges with main is still reset to main after the check has passed. Not seen yet; a ticket if it shows.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-10: one developer ticket (difficulty 2). Qwen's second attempt had the change right, but the layout gate failed on a stray test file a review had left on main; the third attempt said so and stopped. An Opus escalation requeued the ticket behind the file's removal (f12-03), with a "The branch so far" saying the branch held nearly all of it ([session](../sessions/2026-10-10-0854.md)).
- 2026-10-29: by then the branch held nothing beyond main. Three Qwen attempts read for 20 minutes each looking for the lines the requeue named, made no edit, and the escalation waited an hour for Claude's 5-hour cap; Opus then finished it in 10 minutes ([session](../sessions/2026-10-29-1105.md)).
- Lead vs local: Claude Opus $1.87 over one direction and two escalations; Qwen about 2.5 hours of model and 3.4M tokens over six attempts, nothing merged.
- Lessons:
  - A requeue's "The branch so far" is only true while that branch exists. F17 failed the same way from the same day's requeues, and its lesson stayed a line in `lead.md`. **Changed:** pre-flight now refuses such a ticket when its branch is gone or equals main (this review's F1).
  - A review's stray file on main blocked a finished ticket for 19 days, because the fix ran last. **Already changed:** since F173 a feature ticket runs in its card's place, not by a `priority: 100`.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:** a review's scratch file on main cost this card 19 days; a gate that refuses a review's commit when it leaves an untracked test file behind would stop the cause, if it happens again. And the runner should catch a reset of a requeued ticket's branch at the start of an attempt, not only an empty one (backlog line above), the next time `_start_attempt` changes.

### 7. What clogged the factory line
- **Waiting on f12-03, 10–29 October (about 19 days):** the ticket depended on the stray file's removal, and that fix ran last (`priority: 100`). Unclog: already done, F173 runs a ticket in its card's place.
- **Three no-edit attempts on 29 October (1 hour):** the stale "The branch so far". Unclog: the new pre-flight check refuses that ticket before any attempt.
- **The escalation parked for Claude's 5-hour cap (1 hour, 12:47–13:48 on 29 October):** normal pacing.
- **10 October (1.5 hours):** two Qwen attempts and the direction, where the work was right but the gate failed on main's stray file. Unclog: the same F173 change, so the fix for a broken main runs in its card's place instead of last.

## What was built
- `factory_dashboard/templates/planning.html`: both `#lead-window` rows print the row's `reset_label` or `status` after the percent, joined with " · ", only when one is set. The 75% sentence stays on the 5-hour row. No new words: both come from `WindowAllowance` (`factory_dashboard/overview.py`), where at most one of the two is set.
- `tests/factory_dashboard/test_planning.py`: the 75% line test now asserts the whole row with "resets at 14:00" (the fixture's clock is 12:00); the week row test asserts "resets on <Mon> <d> 12:00"; a new test covers a reset already past and a week with no reading on one tile, and that no "resets" leaks into it; another reads the template and fails if it holds either status sentence.

Tests: two existing tests were edited, both to assert more than before (the whole row on its stripped text, where they had matched a substring of the raw HTML); nothing was weakened. The new tests fail without the template change, except the template text test, which guards against a hard-coded status coming back (the 10 October attempt had added one).

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | No check refused a requeue whose "The branch so far" described a branch that no longer held any work: three attempts read for lines that weren't there | Fixed: `_stale_branch` in `runner/tasks.py`, called from `preflight`: a ticket with a "The branch so far" section whose `task/<id>` is missing or has no diff from main fails pre-flight (`STALE_BRANCH`). One test in `tests/runner/test_tasks.py` (no branch, a branch equal to main, a branch with work). No ready ticket has the section today. `lead.md`'s f32-01 line now points at the check |

The template change itself is right: `reset_label` and `status` are exclusive in `_agent_allowances`, the `if` guards both a missing row and a row with neither, and the Overview's partial shows the same fields. The Overview shows `status` in its warning colour while the planning room keeps it in the tile's muted line; that is consistent with the tile's quiet style and not a finding.

No checkpoint ran (the ticket was finished by the lead), so there are no checkpoint verdicts. Score: 8/10: a small, correct change with tests that pin whole rows; the cost was all in the flow around it, not the work.

After the fix, ruff and mypy pass on the changed files, and `tests/runner/test_tasks.py` (131), the lead window tests and the 29 pre-flight, requeue and escalation tests in `test_loop.py` pass. The full runner and dashboard run was stopped at its 20-minute limit at about 94%, with no failure before it (the four errors at the end are the stop's own, as the run was killed mid-test).

The French: no `coucou/locale/fr/` change in this milestone.

### Round 2 (2026-10-30)
The only fix diff is round 1's own: `_stale_branch` and its test, the `lead.md` line, the backlog line and ADR 02's learnings entry. F1 is resolved. The check calls git only for a ticket with a "The branch so far" section, so `_print_plan` and the other pre-flight callers pay nothing for the rest, and `git diff --quiet` exit 1 (work on the branch) is the only pass, so a missing branch (128) is refused as well. The test covers the four cases: no section, no branch, a branch equal to main, and a branch with a commit. No ready or later ticket has the section. ruff and mypy pass on `runner/tasks.py`, and `tests/runner/test_tasks.py` passes (131). The full runner and dashboard run hit its 20-minute limit at 2,744 passed and none failed (its one error was the stop itself, in `test_runs.py`); the six dashboard test files it hadn't reached, `test_runs.py` included, then passed on their own (196). No new finding; score stays 8/10; no checkpoint ran, so there are no verdicts.

## Backlog
- F1's residual gap (a branch reset at the start of an attempt after a merge conflict), in `docs/backlog.md` under "Waiting for something".

## Factory
- Flow: one developer ticket, six Qwen attempts over two runs nineteen days apart, finished by an Opus escalation. No stops for the owner. One park for Claude's 5-hour cap.
- Models: Qwen got the change right on 10 October (attempt 2) and was blocked by main, then failed three times on 29 October through no fault of its own work: the ticket was stale. Opus: $0.45 direction, $0.61 and $0.81 escalations.
- What to change: the second time (F17, f32-01) a lesson written only as a line in `lead.md` let the same failure through. When an escalation writes "wants a check", the review builds it; this one did.

<!-- runner report -->
<!-- /runner report -->
