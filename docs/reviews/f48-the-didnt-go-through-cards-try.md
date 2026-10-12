# Review: F48 Try again plants a note, once

- **Status:** reviewed on 2026-10-13 (round 1); waiting for the owner's sign-off.

## Sign-off sheet

### 1. What changed
- **A taken name never refuses a note.** A note whose first six words match a card's is no longer "a card already":
  - the same words again: the runner answers "planted already" and names the card; nothing is written and nothing lands on your desk;
  - other words: the note gets its own card, named with `-2` (then `-3`).
- **One card per note under "Didn't go through".** Try again then Plant (or Send, on a thread) takes the refused card off the desk the moment the retry is sent. If the retry is refused too, only the new card shows.
- **Dismiss is as it was:** the card goes at once, and the runner records it at its next pick.
- **The phone gets new CSS and scripts without clearing its cache.** Every dashboard file's link carries a version made from the file's content, so a changed file is a new address.

### 2. How to test it yourself
1. On your phone, open `/planning` and plant a note that starts with the same six words as a card you have, with different words after. After the runner's pick: a second card exists, its file name ending in `-2`, and nothing shows under "Didn't go through".
2. Plant the very same note again. After the pick: no new card, nothing on the desk. If you stay on the page, the line under the Plant buttons reads "planted already: docs/milestones/…".
3. If a note is ever refused: press **Try again** on its card (your words go back in the box), then **Plant**. The card leaves the desk at once; reload, and it stays gone.
4. For a refused message: **Try again** opens its thread with your words in the reply box; send it, go back to `/planning`: its card is gone.
5. The cache: nothing to do by hand. After the next merge that changes how a page looks, reload on the phone: the change shows. (To check now: view a page's source; each `/static/…` address ends in `?v=` and ten characters.)

### 3. Left for later
- "Your desk · N" doesn't drop by itself when a card leaves after Try again or Dismiss; a reload fixes it. F19 (ready, `f19-01-planning-live`) refreshes the desk every 5 seconds, so nothing more is planned here.
- Three nits in the backlog: "planted already" names the card's file where a link would be kinder; "the same words" is judged a little loosely; the version cache trusts the file's time alone.

### 4. Decisions waiting for you
None.

### 5. How the work went
- [2026-10-09 02:09](../sessions/2026-10-09-0209.md): `f48-02-static-versions` merged at the first attempt by Qwen (35 min, 1.4M local tokens). A checkpoint read it and found nothing.
- [2026-10-10 08:54](../sessions/2026-10-10-0854.md) and [19:10](../sessions/2026-10-10-1910.md): `f48-01-retry-plants-once` (lead ticket) waited for Claude's weekly reserve.
- [2026-10-12, lead in a terminal](../sessions/2026-10-12-lead.md): f48-01 had been built headless but was blocked by a red main (a scratch test file the F12 review left). The file was removed and the branch landed through `check-all`, unchanged.
- Lessons:
  - **A local model tests what it built, not what the ticket's Done when lists.** f48-02 had five Done-when lines and tests for two. The checkpoint read "tests check `?v=`" and passed it. The review added the three missing. Proposed fix: the checkpoint prompt lists the ticket's Done-when lines and asks for the test behind each (a prompt change, one lead ticket, not written yet: it fits with F65's prompt ticket, `f65-02-feedback-prompt`).
  - **A red main cost this card two days**, as it did F21 and F31. F106's plan (the runner notices a red main) is the fix; it is approved work, not a new decision.
  - **The headless lead ticket was right the first time** at difficulty 5 across the runner and the dashboard: its tests cover each Done when, the edge values of `again`, and three real-browser cases. Nothing to change.

### 6. What next
- **Product:** on hold, as you asked (2026-10-04).
- **Factory:**
  - Run F19 (planning refreshes itself) soon: F26's numbers and this card's "leaves at once" both stop one step short of live without it.
  - Put "each Done-when line has a test" into the checkpoint prompt (above). It is the third review in a row (F26, F12, F48) where the review, not the checkpoint, found the missing test.

### 7. What clogged the factory line
I couldn't read the metrics database from this job, so these times are from the commits and session reports.
- **The weekly reserve, about 2.5 days:** f48-01 was ready on 2026-10-08 and waited until the week reset on 2026-10-12 at 17:00. Unclog: planning and small lead tickets already run under the reserve (ADR 20 item 2); a difficulty-5 lead ticket that fixes something you reported could too. I'd raise it with F39's limits rather than alone.
- **A red main, about 6 hours on this card** (blocked 2026-10-12 until landed at 22:36), and four tickets in all. Unclog: F106 D5.
- **The build itself:** 35 min of Qwen for f48-02, one headless Opus job for f48-01. No failed attempt, no stop for you.

## What was built
- `runner/requests.py` `_plant`: a taken slug loops to the first free `-2`, `-3`, …; when the taken card's doc holds the note's title and thoughts (`planner.holds`, whitespace collapsed, a cut title's ellipsis left out), it returns `planted already: <path>` and writes nothing.
- `factory_dashboard/planning.py`: `_retried` reads `again` from every plant, message and send-back value; `_refused` leaves those requests out; a thread's reply box gets the hidden `again` only while the refused message hasn't been retried.
- `planning.html`, `thread.html`: the hidden `again`, filled by Try again, cleared after a send or when the box is emptied; the plant form removes the retried card (and its group when it was the last).
- `factory_dashboard/app.py`: `static(path)`, a Jinja global; the five templates with `/static/` links use it.

## Findings and resolutions

| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| f48-the-didnt-go-through-cards-try-F1 | should-fix | claude | f48-02's tests covered two of its five Done-when lines. Nothing checked that the version comes from the content, that a rewritten file gets a new one, that a missing file fails the render, or that the versioned address serves the file; the no-bare-link test read five named templates, not the folder. | Added `test_a_static_links_version_follows_the_files_content` and widened the template test to every `*.html`, partials included (`tests/factory_dashboard/test_app.py`). Resolved. |
| f48-the-didnt-go-through-cards-try-F2 | nit | backlog | `planner.holds` looks for the note's words anywhere in the card's doc, as a substring: a short note ("ok") under a taken title reads as planted already. | Backlog: match within `## Notes`, on whole lines. |
| f48-the-didnt-go-through-cards-try-F3 | nit | backlog | The Outcome says "planted already with a link to the card"; the result is a file path in plain text, seen only if the owner is still on the page at the pick. | Backlog: render a `planted…` result as a link to the card's page. |
| f48-the-didnt-go-through-cards-try-F4 | nit | backlog | `static` keeps a hash while the file's `st_mtime` is unchanged: two writes within the clock's grain, or a restore that keeps the time, would serve the old version. | Backlog: key on `st_mtime_ns` and size. |

Tests the tickets changed, read one by one:
- f48-02 loosened two exact matches in `test_app.py` to "`?v=` and hex follows": right, the address changed.
- f48-01 dropped the "is a card already" refusal case and turned a second approval of a seed into "planted already", with a check that no commit was made: both are D1.

Checked and fine:
- `again` is the desk's alone: an id that is later, another project's, not a number, or in a `dismiss` hides nothing (each has a test); the runner applies a value carrying it like any other.
- A retry dismissed keeps the note it stood for off the desk; two same notes at one pick plant once.
- No user-facing strings outside the dashboard, which is English only: no French to check.
- `uv run pytest -q tests/unit tests/integration tests/runner`: 1800 passed, 1 skipped. The plant, retry and dismiss tests in `test_planning.py` (40, in a real browser) and the static tests pass; ruff is clean on the edited file.
- Not checked: no screenshot on a phone (no browser tool in this job). The page gains two hidden inputs and nothing visible.

Checkpoint: one read f48-02 on 2026-10-09 and reported nothing, so F1 is marked **missed**. No checkpoint read f48-01 (landed by hand).

**Score: 8 of 10.** Both halves do what the card asked, and f48-01's tests are thorough; f48-02 shipped with most of its Done when unproven.

## Backlog
F2, F3 and F4 added to `docs/backlog.md`.

## Stop reason
Clean after round 1: one finding fixed in the review, three nits in the backlog, no ADR.

## Workflow observations (Factory)
- **Flow:** two tickets, both first time (Qwen at difficulty 2, a headless lead job at 5). No escalation, no direction, no stop for the owner. The start tag is five days and 222 files old, so the review read the two tickets' commits rather than the milestone diff, as F31's did. Fix: tag a card's start when its first ticket is picked, not when it is planned (a small lead ticket on `runner/milestone.py`, not written yet: plant it if you agree).
- **Models:** Qwen's code for `static` was correct and close to the ticket's wording; its tests were presence checks, the known pattern (F4, F26). The headless Opus ticket needed no rework.
- **The wait, not the work, was the cost:** about an hour of building, four days from plan to landed. Both causes (the reserve, a red main) have owners: F39 and F106.
