# Review: F152, a done card says where its review is, and set aside says it won't run

- **Status:** round 1 done, nothing open; waiting for the owner's sign-off.

## Sign-off sheet

### 1. What changed
- A growing card whose tickets are all done no longer just sits there: on the board and on its page it says which step its review is at: "Review next", "Review running" (and who reads it), or "Review stopped" with the reason and a pointer to Needs you (f152-01, merged on 21 Oct).
- A set-aside count now reads "N set aside, won't run", so you know there's nothing to do about it.
- A mock-up the lead draws always reaches you. If the lead's reply forgets to list a mock-up it drew, the runner lists it itself on the thread, with the page's title and a note "Listed by the runner" (f152-02). This is what went wrong on F152's own first reply.

### 2. How to test it yourself
1. On your phone, open the board and find a growing card with every ticket done (this one, F152, while its sign-off waits): it should read "Review next" or "Review running", not nothing.
2. Open F5's card: its count should say "1 set aside, won't run".
3. Plant a small idea that changes a page, and send the lead a message on its thread. When the reply comes back, the mock-up should show among the proposals, even if the lead only listed the plan. If the runner added it, its key point reads "Listed by the runner".

### 3. Left for later
Nothing new. The slow full test run in review jobs is already in `docs/backlog.md` (from F88).

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-21: f152-01 (developer ticket, dashboard). The local model failed twice and timed out once; Claude gave a direction, then escalated and finished it.
- 2026-10-29 04:34 ([session](../sessions/2026-10-29-0434.md)): f152-02 (lead ticket, `runner/`) merged on its first attempt, in about 5 minutes.
- Lesson: f152-02 was right as a lead ticket, but its tests only covered the new function, not the git step that feeds it. The review found two edge cases there (below) and fixed them.
- Lesson: in a lead ticket, a "Done when" about what git returns ("a removed one is not listed") needs a test that runs git, not one that hands the function a list.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:** the lead ticket ran on Sonnet, but `runner/` is protected code, and CLAUDE.md puts protected code on Opus. Sonnet did fine here, so I'd keep it for lead tickets of difficulty 4 or less and add a ticket only if a protected-code finding comes back. I'll keep watching this in later reviews.

### 7. What clogged the factory line
Most of the time went into f152-01 on 21 Oct: about 3.5 hours of local attempts (one failed run of 20 minutes, one 1.5-hour timeout, then a last attempt of 1.5 hours) before Claude's escalation finished it in 40 minutes. That was a four-file dashboard ticket with a template, CSS and two test files. **To unclog it:** split UI tickets of that size into a logic part (`board.py` with its tests) and a template part, or send them straight to the lead when they touch both templates and CSS. f152-02 itself cost nothing extra.

## What was built (this round's commit, f152-02)
- `runner/planner.py`: `is_mockup_file` (an `.html` file directly in a card's `-mockup/` folder) and `with_mockups`, which adds a `mockup` proposal for each page the job drew that no proposal names.
- `runner/loop.py`: `_commit_drafts` returns the mock-up pages its commit added or changed; `run_planner` passes them to `with_mockups`. A reply with no block (a note) now keeps those proposals.
- `tests/runner/test_planner.py`: four new tests. No existing test was edited.

## Findings and resolutions
All three were fixed by the lead in this review (each under 10 lines). They are protected `runner/` code, so they weren't sent to a developer.
- **F1 (should-fix, fixed):** the diff read in `_commit_drafts` used git's default output. A moved mock-up showed up as a rename and was skipped. A non-ASCII file name came back quoted, so reading it raised an error inside `run_planner`'s `finally` and the lead's reply was lost. Now it uses `-z --no-renames`, like `planner.py`'s own branch diff (`runner/loop.py:4249`).
- **F2 (should-fix, fixed):** two cards' mock-ups with the same file name (`a.html`) got the same proposal id. Ids now count each other (`runner/planner.py:838`), and a new test covers it.
- **F3 (should-fix, fixed):** nothing ran the planner job itself, so the "changed is listed, removed is not" part of Done when was untested. Added `test_a_mockup_a_planner_job_drew_without_listing_it_reaches_the_reply` in `tests/runner/test_loop.py`: two jobs on `plan/f7` that add, change, delete and already list mock-ups.
- No checkpoint findings to judge. No checkpoint ran on this lead ticket, so nothing counts as missed.
- No French to check, since nothing in `coucou/` changed.
- Score: 7/10. The feature is right and small. Its tests stopped at the function and left out the git step that can break.

## Backlog
Nothing added.

## Workflow observations
- The planner's own prompt could also ask for every drawn mock-up to be listed, but the runner's safety net is enough. It doesn't need both.
- The full `tests/runner tests/factory_dashboard` run again took longer than one command may run. In the background it was stopped at its 10-minute limit, at about 90%, with no failure before then; one `F` was printed as it was killed. I then ran the files it hadn't finished in the foreground: `test_planner.py` and `test_loop.py` (543 passed), the last dashboard files and `test_prompts.py` (271 + 225 passed). So everything passed, but in pieces, not in one run. The fix is the backlog item from F88's review: give review jobs a faster check or a longer limit.

<!-- runner report -->
<!-- /runner report -->
