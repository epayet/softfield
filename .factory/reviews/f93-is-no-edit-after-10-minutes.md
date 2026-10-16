# Review: F93, developer attempts get 20 minutes before the no-edit stop

- **Status:** round 1 done, ready for your sign-off.

## Sign-off sheet

**Expected:** your note asked whether "no edit after 10 minutes" was too harsh. The logs said yes: from 10 to 13 October, 16 of 29 developer attempts were stopped by it while they were still working, and the ones that did edit made their first edit as late as 9.2 minutes. So the stop moves to 20 minutes, and its words follow the number.
**Done when:** an attempt with no edit is stopped at minute 20 with "stopped: no edit after 20 min" (in its result and its log); one whose first edit comes at minute 19 runs on to its end.

### 1. What changed
- A developer attempt that hasn't edited anything yet is now stopped after 20 minutes, not 10. On the console and the dashboard the reason reads "stopped: no edit after 20 min".
- The other early stop, "stopped: repeating itself", is unchanged, and so is the attempt's whole limit (75 minutes).
- Nothing else for you to see: no page changed. (Claude's 75-minute limit and the runner's recovery after a stop, from the same terminal session, were reviewed and signed off with F17.)

### 2. How to test it yourself
1. On the dashboard, open the next ticket the developer works on and watch its attempt: it is not stopped at minute 10 for "no edit".
2. If an attempt does get stopped for it, its line on the run's page reads "stopped: no edit after 20 min", at about minute 20.
3. Over the next few milestones, look at how many attempts end that way: the number to beat is 16 of 29 (more than half). If it stays above a quarter, the tickets are too big for the developer, and the lead plans smaller ones (D4).

### 3. Left for later
- Nothing new. Whether to skip the direction after two no-edit stops is looked at again once the 20 minutes have run for a while (D3).

### 4. Decisions waiting for you
None. It is a timeout, which `.factory/project.toml` lets the lead tune, so no ADR.

### 5. How the work went
- 2026-10-10: planted by you.
- 2026-10-13: the lead read the 29 attempts' logs and planned one lead ticket (`runner/` is protected).
- 2026-10-16, 09:13: built by the lead in the terminal session that also finished F17 ([session reports](../sessions/2026-10-16-0923.md), [0927](../sessions/2026-10-16-0927.md), [0944](../sessions/2026-10-16-0944.md)); one attempt, no developer tokens.
- 2026-10-16: this review, round 1: one stale test comment fixed, nothing else.
- Lessons:
  - **Measure a stop before tuning it.** The card's "what we know" (16 of 29 stopped, first edits up to 9.2 minutes, none of the stopped ones repeating) made the number obvious and gave a target to check it against.
  - **Words built from the number** (D2) mean the next change is one line; the review's only finding was a comment that still spelled the old number.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:** the periodic factory review (F59) should report the share of attempts stopped for "no edit" per milestone, so D4's check happens without anyone counting by hand. Text ready to paste in the Plant box: "The factory review shows, per milestone, how many developer attempts were stopped with no edit, against F93's 16 of 29. Open questions: from the job rows or the session reports? Flag it on the desk when it is above a quarter?"

### 7. What clogged the factory line
- Nothing on this milestone's own ticket: it took one lead attempt in a terminal session. The hours it was meant to save were the 16 no-edit stops of 10 to 13 October (about 10 minutes each, plus a direction each time, and two tickets the lead had to build). The runner's per-wait hours are in the block below.

## What was built
- **`NO_EDIT_AFTER = 20 * 60.0`** in `runner/local_model.py`, with a comment giving F93's evidence; **`STOP_NO_EDIT`** is now built from it (`f"stopped: no edit after {NO_EDIT_AFTER / 60:.0f} min"`), so no other place in the code spells the minutes.
- **Tests** (`tests/runner/test_local_model.py`): the two no-edit tests renamed for 20 and 19 minutes, their frames run to minute 30, and the stop test checks it still ran at 19.5 and stopped exactly at 20; the log marker is compared to `STOP_NO_EDIT` instead of a pasted string.

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| F1 | nit | claude | `test_opencode_reports_progress_as_it_runs`'s comment said its clock passes "10 minutes", the old stop | Now names `NO_EDIT_AFTER` (`tests/runner/test_local_model.py:120`) |

Read and found sound, no finding:
- **Nothing reads the old words back.** `stop_reason` compares a live attempt's result with `STOP_REASONS`; job rows and session reports already written keep "10 min" and nothing parses them. The dashboard has no copy of the text.
- **The docs' "10 minutes"** in `docs/agents/lead.md` and `docs/task-writing.md` are dated lessons from F6, F8 and f3-07, true when written: left as they are.
- **The milestone's diff also holds F71 D8** (Claude's 75 minutes, `_settling`, the no-decision escalation branch, `stream_session`) and F17's review fixes: the same terminal session's work, already reviewed in [F17's review](f17-tighter-running-and-pause-presence-in.md) (its F1 and F2 fixed there). Not reviewed twice; nothing new found on a re-read.

Edited existing tests: the two no-edit tests in `test_local_model.py` (above). Neither was loosened: the stop test now pins both sides of minute 20 (19.5 passes, 20 stops) where it pinned only the stop.

No checkpoint ran on this milestone (a lead ticket), so there is no checkpoint finding to judge. French: no `coucou/locale/` file changed. Screenshots: no page changed. After the fix: `uv run pytest -q tests/runner tests/factory_dashboard` gave 2314 passed; ruff and mypy are clean on `runner`.

Score: 9/10. A small change on good evidence, with the words tied to the number and tests that pin the boundary. One stale comment.

Stop reason: none; nothing is left for a round 2.

## Factory
- **The flow:** one lead ticket, done in a terminal session with F17's recovery work; no developer attempt, no escalation, no park, no checkpoint. The owner's only part was the plant.
- **Models:** Claude Opus for the plan (2026-10-13), the terminal session and this review; no local tokens. Dollars in the numbers below.
- **What to change:** count the no-edit stops per milestone in the factory review (planted-card text in item 6), so D4 is checked from the data.

## Workflow observations
- This milestone's range includes another milestone's terminal-session work (`bug-01-review-reads-its-own-commits`, known). Here it cost little, since F17's review had already read it.

<!-- runner report -->
<!-- /runner report -->
