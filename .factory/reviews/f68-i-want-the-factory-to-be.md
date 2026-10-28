# Review: F68, the dashboard is called SoftField

- **Status:** review round 2 done: every finding is resolved, waiting for the owner's sign-off.

## Sign-off sheet

### 1. What changed
The dashboard is now called SoftField. Top left of every page there's a small logo (a green sprout growing out of a yellow crate) and the name, "Soft" in yellow and "Field" in green (a deeper amber and green in the light theme, so they stay readable). Tapping the logo or the name takes you back to the Overview, keeping the project you had chosen. The browser tab shows the same logo as its icon, and every page title ends "· SoftField". Behind the scenes nothing was renamed: the database, the Dropbox backups and the `softfield` commands are as they were.

### 2. How to test it yourself
1. On the laptop, open any page (Planning, say) with a project chosen other than the first one. Top left: the sprout-in-a-crate logo, then "SoftField", yellow then green, with the address in small grey beside it.
2. Click the logo or the name: you land on the Overview, same project still selected.
3. Look at the browser tab: the crate-and-sprout icon, and a title ending "· SoftField" (once, not twice; the Projects page too).
4. Press the Light button: the logo and the name change to the light theme's colours and stay readable.
5. On the phone, open the dashboard: the logo, the whole word "SoftField", the status dot and sign, the project picker and the Light button share one row. With a long project name the picker gets narrower; the name doesn't get cut.
6. Tap the logo on the phone from the Board: the Overview opens.

### 3. Left for later
- Home-screen icons (PNG) for adding the dashboard to the phone's home screen: only if you start doing that (the card's "Not here").
- A small gap in f68-08's check (it relies on the fix ticket naming the ticket it fixes, which Claude's checkpoints do by habit): in `docs/backlog.md`, with its fix, should one ever slip past.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-16 ([session](../sessions/2026-10-16-1543.md)): the local model built the brand in two attempts (101 minutes); the checkpoint (Claude) found its tests weak and wrote f68-02, merged the same night.
- 2026-10-17 ([session](../sessions/2026-10-17-0017.md), [session](../sessions/2026-10-17-1300.md)): Copilot, standing in for Claude at checkpoints, filed f68-03 and f68-04 on the "no outside websites" test; both merged first time.
- 2026-10-19 to 2026-10-20 ([session](../sessions/2026-10-19-2316.md), [session](../sessions/2026-10-20-0754.md)): f68-05 and f68-06, more of the same test.
- 2026-10-23 ([session](../sessions/2026-10-23-1549.md)): f68-07, the last of that chain; the 2026-10-27 checkpoint ([session](../sessions/2026-10-27-2319.md)) found it sound.
- Review, 2026-10-28: found and fixed the logo link that never left the page it was on (it only worked from the Overview), the name cut to "SoftFi" on a phone, and the doubled title.
- 2026-10-28 ([session](../sessions/2026-10-28-0516.md)): the lead built f68-08 first time: a fix of a fix now goes to the lead by a check. It already caught one (f164-06). Review round 2 found it sound.
- Lessons:
  - Six checkpoints read the tests and none read the link: the main bug sat in a three-line template change, with a test that asserted the wrong address. Now in `docs/agents/lead.md`: on a page ticket, check each Done when against the template first.
  - Five developer tickets polished one test while the feature it guarded was fine. The rule from F114 ("a fix of a fix is the lead's") was written the same week but only in a doc; f68-08 makes it a check.
  - A phone test named "does not wrap" only measured height; tests are now asked to measure what their name says.

### 6. What next
- **Product:** on hold, as you asked (factory first).
- **Factory:**
  - f68-08 has landed: F114 and F68 together spent about 14 hours of local model on fix-of-a-fix chains in one week, and the next such ticket goes to the lead. Watch the next milestones' fix tickets to confirm the chains stop.
  - Checkpoints (and the Copilot stand-in's prompt) should open the page for a UI ticket and click what the Done when names; a cheap browser step would have caught this milestone's blocking bug on day one. Worth a planted card if you agree: "A checkpoint on a page ticket clicks through its Done when in a browser, and says what it saw."

### 7. What clogged the factory line
- **The fix-ticket chain on one test: about 3.9 hours of local model** (f68-03 to f68-07, 2026-10-17 to 10-23), plus a slot in five runs. The first two were real problems (the check skipped everything after the logo; then a test that copied the check instead of using it). The last three asked for tidier sharing that bought no protection. To unclog it: f68-08 (a fix of a fix goes to the lead).
- **A failed attempt: 48 minutes** (f68-01's first attempt failed its own tests). To unclog it: nothing; the second attempt passed.
- **Waiting on F17: about a week.** F68 was planted 2026-10-09 and waited for F17's top-bar row, which the local model failed six times before the lead built it on 2026-10-16. To unclog it: already in `docs/agents/lead.md` (F14 and F17): top-bar script and browser-test tickets go to the lead.
- No waits for limits or for you on this card.

## What was built
- `factory_dashboard/templates/base.html`: the brand is a link to `/{{ q }}` (the Overview for the chosen project) holding the inline logo (`_partials/logo.svg`), "Soft" and "Field" spans and the host; the title ends "· SoftField"; `<link rel="icon">` to `static/softfield.svg`.
- `factory_dashboard/templates/_partials/logo.svg`: logo A from the mock-up, the crate and sprout carrying classes the CSS colours from the tokens (`--hazard`, `--hazard-ink`, `--good`), `aria-hidden`. `factory_dashboard/static/softfield.svg`: the same shapes in the dark theme's fixed colours, for the tab.
- `factory_dashboard/static/dashboard.css`: `.brand` is a flex link without the old capitals, "Soft" in `--warn-ink`, "Field" in `--good`, underline on hover. Review: on a phone the brand's column keeps its width and the project select takes the squeeze (18 px type, 24 px logo).
- `factory_dashboard/app.py`: `FastAPI(title="softfield")`. `projects.html`, `project.html`: titles (the review removed the doubled "SoftField").

Tests (`tests/factory_dashboard/test_app.py`, `test_projects.py`): the brand's markup, the favicon served as SVG, the logo's computed colours equal each theme's tokens and differ between themes, a 44 px target at 390 px, one row with no layout problems on a phone, no page saying "software-factory", and the "no outside websites" check with its regression. Edited existing tests, reviewed: f68-01 bent the outside-websites check to skip everything after any `xmlns=` (caught by the first checkpoint, fixed by f68-03); its other edits (the brand is an `<a>`, the title's words) are faithful. Review additions: the link's exact address from three pages, every title naming SoftField once, a phone test that checks the whole name shows with a long project name; each fails on the code before the review.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | blocking | claude | The logo and name linked to `?project=…`, which reloads the current page: from Planning or the Board they never reached the Overview; a test asserted that wrong form | Fixed: `href="/{{ q }}"`; test asserts `/?project=other` from Planning, the Board and a project's page |
| F2 | should-fix | claude | Projects and a project's page were titled "… · SoftField · SoftField" | Fixed in both templates; new test over every page's title |
| F3 | should-fix | claude | On a 390 px phone the name was cut to "SoftFi" (1fr column, overflow hidden); the "does not wrap" test only measured height | Fixed: brand column `auto`, select `minmax(0, 1fr)`, smaller type and logo; the test adds a long project name and checks the whole name, 44 px and layout |
| F4 | nit | claude | Dead `.brand svg .stem` rule | Removed |
| F5 | nit | claude | The regression test left a temp database on every run, with an empty `try/finally` and repeated imports | It uses the `client` fixture now |
| F6 | should-fix | local (lead ticket) | Five developer fix tickets in a row on one test: a fix of a fix should go to the lead, by a check | Fixed by f68-08 (round 2 checked it): `fix_ticket` writes `agent: lead` when the ticket at fault has `finding:`; pre-flight escalates a developer ticket whose ticket at fault has one. Tests cover both and the negatives; f164-06 already went to the lead through it |
| F7 | nit | backlog | f68-08's pre-flight finds the ticket at fault only by a `.factory/tasks/done/<id>.md` path in the Context, which a Claude checkpoint writes by habit, not because its prompt asks | `docs/backlog.md`, with its fix (the prompt asks for the "On the merge of" line, and the check reads only that line) |

Round 2 read `git diff ddb3bb6^..main`: round 1's own fixes and f68-08. Every round 1 finding is resolved. The dashboard was untouched since round 1, and no existing test was edited.

Checkpoint verdicts: C1019-1, C1019-2, C1019-3, C1026-1, C1035-1 and C1044-1 confirmed (the host check really skipped the rest of every page after the logo; the light-theme test checked visibility only; the 44 px target had no test; the exemption covered all of w3.org; the regression test copied the check instead of using it). C1080-3, C1099-1 and C1106-2 rejected: from f68-05 on both tests used the same host detector, and the remaining difference (the `@import` line) can't hide a CDN; those three cost two tickets for no protection. Missed by the checkpoints, visible in the diffs they read: F1, F2, F4 (f68-01) and F5 (f68-03). F3 needed a browser.

Score: 6/10 (5 in round 1). The look matches logo A and the card's decisions, the colours follow both themes and are tested against the tokens. But the one thing the owner asked to do with it, click back to the Overview, only worked from the Overview; the name didn't fit on the phone; and six fix tickets went to test plumbing while those slipped through. Round 2 adds a point because f68-08 turns the cause of that chain into a check, and the check works.

Checked and fine: nothing behind the scenes was renamed (D1: the database, backups, bench cache and commands keep "software-factory" or "softfield" as before); `--warn-ink` is the amber in the light theme (D2); no third-party host or `@import` on any page. After the fixes, `tests/runner` and `tests/factory_dashboard` pass. In round 2 the full run took more than the job's 20 minutes and was stopped at about 99%. Nothing had failed up to there, but one `E` printed as it stopped, and its test isn't known. The 54 tests on this milestone's code (brand, titles, outside websites, fix tickets, pre-flight) pass on their own. The runner's gates run the whole suite before any merge. The rest of this diff range belongs to other milestones (F15, F51, F69, F81, F82, F114, F164 and others) and their own reviews.

The French: no `coucou/locale/fr/` change in this milestone.

## Backlog
- F7 (nit): the fix-of-a-fix check depends on the fix ticket naming the ticket at fault. In `docs/backlog.md` under "Waiting for something".

## Factory
- Flow: one feature ticket and six fix tickets, all by the local model; four of the six checkpoints were Copilot standing in for Claude. No stops for the owner, no parks, no limits hit on this card. The card waited about a week on F17.
- Models: Qwen3.6 35B did all the building, about 7.2 hours of model (1.7 on the feature, 5.5 on fixes); its feature code was close but missed the link's leading `/`, and its tests checked presence. The stand-in checkpoints judged each newest test well but kept asking for more on the same one; none opened the page.
- Round 2: f68-08 by the lead (Opus) on the first attempt. Its check refused f164-06 as a developer ticket the same day, so that fix of a fix went to the lead.
- What to change: f68-08 (done); the lead.md Known range line for F68 (check a page ticket's Done when against the template first); a possible browser step for checkpoints on page tickets (in 6, for you to plant if you want it).

<!-- runner report -->
<!-- /runner report -->
