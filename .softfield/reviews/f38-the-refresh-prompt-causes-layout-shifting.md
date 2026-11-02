# Review: F38, the new-version notice becomes a tag on the top bar

- **Status:** review round 1 done, waiting for the owner's sign-off.

## Sign-off sheet

### 1. What changed
When the dashboard's code changes, the "New version of the dashboard: refresh" bar no longer appears above the page and pushes everything down. Instead a small yellow "↻ New version" tag hangs on the right end of the top bar's hazard stripe; nothing under it moves, and tapping it loads the new version. A page you aren't looking at (another tab, a locked phone) loads the new version by itself, unless you had text half typed: then it waits and shows the tag.

### 2. How to test it yourself
1. On the laptop, open the Planning page and leave it in front. After the next merge that touches the dashboard, within about 10 s a yellow "↻ New version" tag shows on the right of the striped line under the top bar. The page under it doesn't jump.
2. Tap the tag: the page reloads and the tag is gone.
3. On the phone, open the Overview, lock the phone, and wait for a dashboard merge. Unlock: the page loads the new version straight away (a short reload), with no tag left to tap.
4. Repeat 3 with a few words typed in a plant or reply box before locking: on unlock, nothing reloads, your words are still there, and the tag shows within 10 s.

### 3. Left for later
Nothing from this card. One small point, accepted as is: while the tag shows, its tap area (44 px, for a finger) overlaps the bottom edge of the Light/Night button and the top of the last tab on the phone. A tap there loads the new version, which is what the tag offers anyway.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-26 22:52 ([session](../sessions/2026-10-26-2252.md)): the local model tried twice (about an hour) and stopped blocked. Its work was fine; every ticket's tests were red because another ticket (bug-03) named a card you had removed (F113) as an example.
- 2026-10-27 19:02: the escalation, parked about 18 hours for Claude's usage limit, built the ticket in 6 minutes for $1.40, pointed bug-03 at a card that stays, and added the lesson to `docs/task-writing.md` (a ticket never names a planted card as an example).
- Review, 2026-10-28: one gap found and fixed (step 3 above: a locked phone didn't reload on unlock).
- Lessons: a ticket naming a removable card turned every gate red for an unrelated developer; reloading "while hidden" doesn't happen on a phone, because a phone runs nothing while hidden.

### 6. What next
- **Product:** on hold, as you asked (factory first).
- **Factory:** when you remove or merge a card, the runner could look for tickets that name its file and send them to the lead at once, instead of letting every developer's tests go red (it cost f38 an hour and two attempts). It's worth a planted card if it happens again; for now the rule in `docs/task-writing.md` covers it.

### 7. What clogged the factory line
- **Claude's usage limit: about 18 hours.** The escalation waited from 00:53 to 19:02 on 2026-10-27, with 30 planner jobs parked beside it in the same run. To unclog it: nothing new; the reserve rules (ADR 20) already put escalations ahead of planners once the window resets.
- **Failed attempts: about 1 hour.** Two local attempts (42 and 19 minutes) failed on a test that wasn't theirs (bug-03 naming the removed F113). To unclog it: the task-writing rule added by the escalation; a check at card removal if it recurs (see 6).

## What was built
- `factory_dashboard/app.py`: `/version` now returns `NEW_VERSION` as a link with class `version-tag` and `href=""` (reloads the page it is on), "↻ New version", with a title explaining it. The poll and its 10 s rhythm are unchanged (D3).
- `factory_dashboard/templates/base.html`: the poller moved from `<main>` into a `.bar-stripe` wrapper around the hazard stripe (D1). A hidden page reloads when the tag arrives or on a later `visibilitychange`, only if `liveIdle()` is true (D2). Review addition: coming back to a page asks `/version` at once and reloads if there is a new version and nothing would be lost.
- `factory_dashboard/static/dashboard.css`: `.new-version` is gone; `.version-tag` is absolute over the stripe's right end, a 44 px tap with a 24 px hazard-yellow plate with a cut corner drawn by `::before` (so the clip-path doesn't shrink the tap). Themed from the tokens (`--hazard`, `--hazard-ink`, `--display`, `--mono`), no animation.

Tests (`tests/factory_dashboard/test_app.py`): the existing `test_a_page_says_when_a_new_version_is_available` was edited and is stricter than before (the exact poller back, then the exact tag shape and no `hx-get`). New: the poller sits on the stripe and not in `<main>`; `.new-version` gone from the CSS; at 1024 px and on the phone, swapping the tag in leaves the header, `<main>`, the top row and the tabs exactly where they were, with the tag at the stripe's right end, a 44 px tap and a 24 px plate; a hidden page doesn't reload over unsent text, and does once the text is gone. Review addition: `test_a_page_coming_back_loads_the_new_version_at_once`, which fails without the fix.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | A page left on a locked phone didn't load the new version on return: phones run no timers for a hidden page, so the "reload while hidden" never ran, and the card's second Done when held on a desktop browser only | Fixed: on `visibilitychange` to visible, the page fetches `/version` once and reloads if a new version is out and `liveIdle()` allows; else the next poll shows the tag. New test, checked to fail without the change |

No checkpoint read this ticket (it was built by the escalation), so there are no checkpoint verdicts. Score: 8/10: a clean change that matches the mock-up and every decision, with tests that measure the layout rather than guess at it; one Done when didn't hold on the phone, the device the owner uses most.

Checked and fine: the edited existing test is stricter, not looser; `liveIdle()` guards both reload paths, so unsent words are never lost; the bug-03 and `docs/task-writing.md` edits in the escalation are right. After the fix, all 1700 runner tests and 1021 dashboard tests pass, and ruff passes. The rest of this diff range (F59, F80, F81, F82, F84, F142, F164, F173 and the F136/F139/F143 plans) belongs to other milestones and their own reviews.

The French: no `coucou/locale/fr/` change in this milestone.

## Backlog
Nothing new.

## Factory
- Flow: one ticket; the local model failed twice on someone else's red test and blocked with `needs-file`, which was the right call; the escalation sat parked for Claude's limit about 18 hours, then passed first time. No stops for the owner.
- Models: the local Qwen3.6 35B used 6.6M input tokens over two attempts for nothing merged; Claude Opus built it for $1.40 and fixed the cause.
- What to change: the root cause (a ticket naming a planted card as its example) is now a line in `docs/task-writing.md`. If it recurs, make it a check: removing a card lists the tickets that name its path, for the lead.

<!-- runner report -->
<!-- /runner report -->
