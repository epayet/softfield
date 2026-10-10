# Review: F26 numbers next to "Coming" and "Your desk"

- **Status:** reviewed on 2026-10-10 (round 1); waiting for the owner's sign-off.

## Sign-off sheet

1. **What changed**
   - On `/planning`, the two headings now carry a number: "Coming · 2" for what is on its way, "Your desk · 5" for what waits for you.
   - The desk's number is the Planning tab's number: what still waits for you. A card you have already acted on (dashed orange, after Archive, Sign off or Remove seed) stays listed until the runner picks it up, and is counted no more. So the number can be one smaller than the cards you see.
   - With nothing waiting, the heading reads "Your desk" alone, as the tab reads "Planning" alone.
   - The four group headings ("Your answers wanted", …) have no number, as planned.
2. **How to test it yourself**
   1. Open `/planning` on the phone with something on the desk: the heading reads "Your desk · N", and N is the number on the Planning tab.
   2. Plant an idea: after a reload, "Coming · 1" shows above the desk until the runner picks it up.
   3. Archive a thread from the desk: after a reload its card turns dashed, and both the heading and the tab drop by one.
   4. When the desk is empty: "Your desk" with no number, and "Nothing waits for you."
3. **Left for later**
   - The numbers change on a reload, not by themselves. F19 (ready, `f19-01-planning-live`) refreshes both sections every 5 seconds, headings included, so nothing more is needed here.
4. **Decisions waiting for you:** none.
5. **How the work went**
   - [2026-10-09 02:09](../sessions/2026-10-09-0209.md): `f26-01-desk-counts` merged at the first attempt by Qwen, in 41 min (2.2M local tokens), as the last of that run's 22 merges. No direction, no escalation, and no checkpoint after it.
   - Lessons:
     - The ticket pointed at a value to reuse (the tab's number) and at a worked example two sections below in the same file. That is why a two-line change came out right, even though the plan's own description of the number was out of date (see F2 below).
     - "Equal to the tab" is a weak thing to test when both print the same value. The review added the count against the cards listed; lead.md's Known range now says to name what a number is counted from.
6. **What next**
   - **Product:** on hold, as you asked (2026-10-04).
   - **Factory:**
     - Run F19 next among the planning cards: once the desk refreshes itself, these numbers are live, which is what makes them useful from a phone.
     - A two-line card waited two days in the queue at priority 6. I suggest a fast lane: the runner takes a difficulty 1–2 ticket with no dependencies before a long chain's next ticket, when one is ready. It needs an ADR item (it changes the pick order); I'd propose it with F39's limits rather than on its own.
7. **What clogged the factory line**
   - Nothing during the build: one attempt, no failure, no wait for a limit, no stop for you.
   - The wait was before it: the plan was approved on 2026-10-08 at 08:20 and the ticket merged on 2026-10-10 at 02:54, about 42 hours in the queue for 41 minutes of work, behind F9's line tickets. The fast lane above is what would unclog it. (These times are from the commits and the ticket's footer; I couldn't read the metrics database from this job.)

## What was built

- `factory_dashboard/templates/planning.html`: the Coming heading prints `coming.items | length`; the desk heading prints `planning_count` when it isn't zero, the same variable the tab uses (`top_bar` in `factory_dashboard/app.py`).
- Four tests in `tests/factory_dashboard/test_planning.py`, one per Done when. No existing test was changed (the session report lists the file because tests were added to it).

## Findings and resolutions

| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| f26-i-want-to-see-numbers-next-F1 | should-fix | claude | No test counted the desk's number against the cards listed, or covered a card on its way: the desk test compared the heading with the tab, both printed from the same variable, by substring over the whole page. | Added `test_desk_heading_leaves_out_what_is_on_its_way`: exact heading and tab text, equal to the cards listed, then one less after an Archive while the card stays listed. Resolved. |
| f26-i-want-to-see-numbers-next-F2 | nit | claude | D2 says "the sum of the four desk groups' items". The desk has five groups since F31, and cards on their way aren't counted. The code is right (it reuses the tab's number, which matches the Outcome's "how many wait for them"); the doc was stale. | Added an "As built" line to D2 in the milestone doc. Resolved. |

Checked and fine:
- Each Done when has a test with the exact heading text; the empty-desk test builds its own empty database and reads the heading alone.
- The "Didn't go through" cards count on the heading as they do on the tab.
- Coming stays hidden when empty.
- No user-facing strings outside the dashboard, which is English only: no French to check.
- `uv run pytest -q tests/unit tests/integration tests/runner`: 1715 passed, 1 skipped. `tests/factory_dashboard/test_planning.py`: 102 passed. Ruff is clean on the edited file.
- Not checked: no screenshot on a phone (no browser in this job). The change adds a few characters to two headings that already fit.

No checkpoint read this ticket (it was the run's last merge), so there are no checkpoint findings to judge and none marked missed.

**Score: 8 of 10.** The feature is right and small; the tests needed one more case.

## Backlog

Nothing new.

## Workflow observations (Factory)

- **Flow:** one developer ticket, one attempt, no stop, no park, no intervention. Qwen at difficulty 2 on a worked example in the same file is squarely in the known range.
- **Cost of the pass:** 41 minutes and 2.2M local tokens for two template lines and 84 test lines. Most of it is reading `test_planning.py` (over 2,000 lines) and `planning.py`. Fine while the GPU is otherwise idle; it is the argument for the fast lane rather than against delegating.
- **The last merge of a run gets no checkpoint** (as f2-13 did): here the review caught the weak test. For a one-ticket milestone that is acceptable, since the review reads the same diff.
- **Plans age:** D2 was written on 2026-10-07; F31 and the on-its-way rule changed the desk on 2026-10-08. Nothing rechecked the plan before the ticket ran. A ticket that names the value to reuse survives this; one that restates how to compute it would not have.
