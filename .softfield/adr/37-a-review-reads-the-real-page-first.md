# ADR 37: A review reads the real page first

- **Status:** Accepted (by the owner, 2026-10-28)
- **Date:** 2026-10-27
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 28](28-lead-jobs-can-look.md) item 5 for review jobs only; the "Review" section of `runner/instructions/lead.md` and the review job's brief (`REVIEW` in `runner/prompts.py`).
- **Card:** [F144](../cards/f144-a-review-should-open-the-real.md)
- **Evidence:** four milestones in a row where the tests passed on made-up data and the real data showed the bug:
  - F109: the merge tests left a merged card's doc and no milestone row; a real merge does the opposite, where both worst bugs were. Found by reading the 19 real merge headings.
  - F94: the doubled "finished" and "took 142.2 h" came from `softfield look page /away`, not the code or the tests.
  - F30: the leftover "6 points" counter showed only on F95's real thread (`look page /planning/f95`), in a minute.
  - F158 (and F159 before it): the local model's UI passed every test that read the page's text and was broken in the HTML; the review caught it by opening the live page.
  Each of these reviews looked because the reviewer chose to. Nothing asks it to, and a review that doesn't look has nothing to tell it it should have.

## Decisions (⚑ = deviates from an earlier decision)
1. ⚑ **A review that changed a factory page looks at it first.** When the milestone's diff touches `factory_dashboard/` templates, static files or the views behind them, the review opens each page it changed with `softfield look page <address>` on the live database, before reading the tests, and also fetches the raw HTML where text can hide a fault (escaping, a missing attribute). Replaces ADR 28 item 5's "on demand" for this one case; planners stay on demand.
2. **And checks one fixture against a real record.** For each new test file, the review compares one of its fixtures with a real record of the same kind (a card's doc in `.softfield/cards/`, a thread or row through `softfield look sql`), and a fixture that is tidier than the real thing is a should-fix finding on the test.
3. **The report says what it saw.** The review report's findings section names the pages it opened and the record it compared, in one line each, so a review that skipped it shows.
4. **Reviews only.** Checkpoints and developer jobs don't get `look` (ADR 28 item 4 stands).

## Cost and risk
- About one to three page reads per UI milestone: a page is at most 40,000 characters, so a few cents of Opus input at most, against bugs that each cost a fix ticket and a reopened sign-off.
- The live database may not hold the case the milestone added (a new state nobody has reached yet). The review then says so in its line (item 3) and relies on the tests; it doesn't invent data.

## What doesn't change
- Product pages (`coucou/`) aren't served by `look page`; their reviews keep "take screenshots when you have a browser".
- Planner jobs look only when they want to (ADR 28 item 5).
- `look` stays read-only; nothing is added to its command.

## Alternatives turned down
- **Checkpoints look too** (ADR 02's F94 entry suggested it): they run every two developer merges, mostly on Sonnet, and most merges change no page. Four bugs out of four were caught at the review; wait for one that a review catches too late.
- **A rule in the developers' notes** ("test on realistic data"): developers drop instructions from long prompts (`runner/instructions/lead.md`, "Developers' notes"), and this is the reviewer's check to make.
- **Screenshots** (ADR 28 "Later"): would show layout too, but none of the four bugs needed a picture.
