# Review: F79, a retry after a timeout names the files on its branch

- **Status:** done, signed off by the owner on 2026-10-13.

## Sign-off sheet

**Expected:** your question was "when a task times out on the first attempt, is the second attempt starting from scratch?". The answer was no for the code, yes for the conversation, with one gap: a developer on OpenCode can't run `git diff`, so its new session didn't know which files its timed-out attempt had changed. The plan closes that gap.
**Done when:** after a timed-out attempt whose work was kept, the next prompt says it ran out of time and lists the files changed against main; after a timeout before the first edit it lists none and says the branch was reset; a retry after an ordinary gate failure is unchanged.

### 1. What changed
- A developer whose attempt ran out of time now starts its next attempt with one more line, right after "Your previous attempt ran out of time. Keep what works and finish the smallest remaining piece first":
  `Files changed on this branch so far: coucou/progress.py, tests/unit/test_progress.py`
- Nothing else moves: the work stays on the branch as before, an attempt that timed out before its first edit still starts again from main with no list, and a retry after a failed gate reads as it did.
- The same line shows after an interruption (the runner stopped mid-attempt) and on a last attempt with the lead's direction, when the attempt before timed out.
- You won't see it on the dashboard. It is in the prompt the developer gets.

### 2. How to test it yourself
It only shows when a developer attempt times out with edits on its branch, so:
1. The quick check: `uv run pytest -q tests/runner/test_loop.py -k "retry_after_a"` plays the three cases (timed out with work kept, timed out before the first edit, a plain gate failure).
2. On the real thing: the next time the overview shows a ticket at "attempt 2" after "timed out", open that run's page and attempt 2's log, and look for "Files changed on this branch so far:" under "ran out of time". I didn't check in a browser that the page shows the prompt; if it doesn't, the same text is in the run's folder under `var/runs/`.

### 3. Left for later
- Your open question from 2026-10-10: also let OpenCode developers run `git diff`? My recommendation stays "not yet": it reverses the prompt's "never run git", widens the allowed commands (a security change), and a full diff costs the local model context. Fix if it turns out to be needed: a draft ADR, once a few timed-out retries have run with the new line and still lose time rediscovering their work.
- Backlog (f79-F3): this review was handed three other milestones' work to read, because it reads everything committed since F79 started. Fix: name the milestone's own merges in the round-1 prompt, as later rounds already do.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-13 09:32 ([session](../sessions/2026-10-13-0932.md)): `f79-01-timeout-retry-lists-files` merged at its first attempt, a headless lead job (`runner/` is protected), 24 minutes. No local tokens. The runner stopped after it for a fresh process, as it does when `runner/` changes.
- 2026-10-13 11:30 ([session](../sessions/2026-10-13-1130-lead.md)): your terminal session on F107, mock-ups and the board. Not F79's work, but its two commits are in this review's diff (see Workflow observations).
- 2026-10-13: this review, round 1. Two small fixes by the review, one backlog line.
- Lessons:
  - A planted question got its answer from the code, and the answer found a real gap. The gap became one 16-line ticket with three tests. That is the right size for a question.
  - The ticket said "follow `EARLIER`", so the new line copied its words, "Files it changed". But the list is the branch against main, so it also holds the files of attempts before the one that timed out. The review reworded it. When a ticket says "follow that", it should say whether the words carry over or only the mechanism.
  - The ticket's `files:` didn't list `docs/workflow.md`, which describes the retry prompt line by line, so the doc fell behind. A ticket that changes a prompt lists the doc that describes it.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - Watch whether the line helps: compare how long a retry after a timeout takes to its first edit, before and after 2026-10-13. If it doesn't drop, the `git diff` question comes back as a draft ADR.
  - The session that built this took 24 minutes for a 16-line change. Most of it was probably `check-all`: your terminal session the same morning measured 18 minutes for it, and paid that for one attribute. I didn't measure the split for this job. F71's slow-tests study is the fix; it deserves to go ahead of more runner tickets.
  - Point a round-1 review at its own merges (backlog, f79-F3): this one read about 830 lines that belong to F49, F104 and F109.

### 7. What clogged the factory line
- **F79 itself:** nothing. One attempt, no limit wait, no stop for you. The card was planted on 2026-10-09, answered the same day, and its ticket merged on 2026-10-13: it waited its turn behind F5 and F6 work, your priority order.
- **Inside its 24 minutes:** probably mostly `check-all` (the browser tests), which the 11:30 session measured at 18 minutes; not measured for this job. What would unclog it: F71.
- **The review:** two full runs of the three test folders, 3 min 40 each, and three other milestones' code to read. What would unclog it: f79-F3.
- I couldn't read hours from the metrics database in this job (a headless review has no query command); the figures are from the session reports. The fix is already in the backlog (f53-review: a "where the hours went" block in `runner report`).

## What was built
- **The prompt** (`runner/prompts.py`): `TIMED_OUT_FILES`, one line added after `TIMED_OUT`.
- **The loop** (`runner/loop.py`): `_prompt` takes `kept`, the files to list, and adds the line only when the attempt before timed out and the branch wasn't reset. `run_task` passes `s.git.changed_files(MAIN)` in that case, the same call a requeued ticket's first attempt uses for `EARLIER`.
- **Tests** (`tests/runner/test_loop.py`): three, through `runner run` with the fake model: the list after a timeout with work kept (two files, comma-separated, exact line), no list after a timeout before the first edit, no list after a plain gate failure. The first fails without the change.

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| F1 | nit | claude | The line read "Files it changed:", "it" being the timed-out attempt. The list is `main...HEAD`: after a gate failure then a timeout it also names the first attempt's files, and it names deleted files too | Fixed: "Files changed on this branch so far:", which is what the list is and echoes `KEPT` ("Your work so far is still on this branch") |
| F2 | should-fix | claude | `docs/workflow.md` describes attempt 2's prompt ("After a timeout it also says the attempt ran out of time") and wasn't updated | Fixed: it now says the prompt lists the files changed on the branch so far |
| F3 | nit | backlog | The round-1 diff `git diff <start>..main` held two commits of a terminal session for F49, F104 and F109, about 830 of its 890 lines | `docs/backlog.md` |

Read and found sound, no finding:
- The interrupted path (`cut_off`) and the directed last attempt go through the same two lines of `_prompt`, so they get the list with no code of their own. Neither has a test of its own for the list; the three tests cover the condition (`timed_out and not reset`) from both sides.
- An attempt that times out with no edit of its own, on a branch that holds earlier attempts' work, is reset to main (`pending = "timeout"`), so no list is shown for work that is gone.
- After `_catch_up` merges main into the branch, the list still holds only the ticket's files: `changed_files` compares from the merge base.

Edited existing tests: none in F79's own commit (50 lines added to `tests/runner/test_loop.py`, none removed); the review changed one constant in the new tests for F1. The terminal session's commit edited three existing tests, each read: two planner tests in `test_loop.py` gained the second reply f49-03 now causes and a stricter thread check, and `test_planning.py`'s frame pattern follows `sandbox="allow-scripts"`. Nothing weakened.

The other milestones' code in the diff (f49-03, f109-02, f104-01) was read and gave no finding. F104's frame change is a security decision (D1 in its doc, taken with you in that session): the frame's origin stays its own and the Chromium test checks it can't read the page around it.

No checkpoint ran on this ticket (a lead ticket), so there are no checkpoint findings to judge. French: nothing to check, no user-facing string and no `coucou/locale/` file changed. Screenshots: no new screen. After the fixes, `uv run pytest -q tests/unit tests/integration tests/runner` gave 1818 passed, 1 skipped; ruff is clean on the two edited files.

Score: 9/10. Small, correct, built on the call the requeue path already uses, with tests for all three Done-when lines. It lost a point for wording that said slightly more than the list is and for the doc left behind.

Stop reason: none; nothing is left for a round 2.

## Factory
- **The flow:** one lead ticket, one attempt, no stop, no park, no intervention from you. The runner restarted after the merge, as it must when `runner/` changes.
- **Models:** Claude Opus only; see the numbers below. No developer work, so "Known range" in `docs/agents/lead.md` has nothing new.
- **What to change:**
  - A round-1 review names its own merges when other commits sit in its range (f79-F3, backlog).
  - A lead ticket still gets no checkpoint, so its review is its only reader (F41, F55 and F53 said the same). Here both findings were small enough that it didn't matter.

## Workflow observations
- The start tag was one commit before the ticket's merge, as it should be. The diff grew afterwards: a terminal session committed between the merge and the review, and round 1 has no way to tell those commits from the milestone's.
- Whether the new line saves time isn't known yet. The numbers that would say (time to first edit on a retry after a timeout) are in the metrics database's jobs, and no report shows them.

<!-- runner report -->
<!-- /runner report -->
