# Review: F85, real before and after pictures when you sign a card off

## Sign-off sheet

### 1. What changed
When a card that changed a page is ready for your sign-off, its page now shows a **Before and after** panel right under "What changed". It holds real pictures of each page the card changed, as the page was when the card started and as it is now, on a phone and on a wide screen.

- On a phone, the Before / After switch flips between the two. On a wide screen they sit side by side.
- The Phone / Wide switch picks the size, and a tap opens a picture at full size.
- The address above each picture opens the page as it is now, in a new tab.
- "The plan's mock-up ›" takes you to the mock-up you approved.
- A page that didn't exist before says so, and a picture that couldn't be taken says why.

The runner takes the pictures itself before each review round, on a copy of the factory's data, so nothing real is touched. The review now opens the after pictures and says in one line whether they match the mock-up. New projects with pages are asked to set this up. Softfield has it now; travel-companion and Coucou get theirs from a card each (their text is in the card's "Other projects").

Differs from the mock-up: F85's own after picture can't show the panel, because the pictures are taken before the card's sheet exists and the panel shows only with a sheet, so its Before and After look the same. Reading its code against the mock-up's Proposed, the panel matches, except the words on each address, which read "the page as it is now" where the mock-up says "the live page".

### 2. How to test it yourself
1. On your phone, open F85's page from the board. "Before and after" is under "What changed", with one page listed.
2. Press Before, then After, then Wide, then Phone: the picture changes each time. F85's own Before and After look alike (see above), so the real test is step 5.
3. Tap a picture: it opens at full size.
4. Tap the address above it: the page opens as it is now, in a new tab.
5. Sign off the next Softfield card that changes a page and has a mock-up, and do the same there: Before and After should now differ, and "What changed" ends with the line on the mock-up.
6. On a computer, open a card's page with pictures: Before and After sit side by side, and there is no Before / After switch.

### 3. Left for later
- `bug-58`: a card's "What it's about" shows its doc's Markdown marks as written, like `[ADR 40](../adr/40-….md)`; you can see it in F85's pictures. It's set aside on the board as a seed.
- Pictures in the light theme, and pictures for planner jobs, stay in the card's "Later".

### 4. Decisions waiting for you
None. [ADR 40](../adr/40-pictures-at-sign-off-in-every-project.md) was accepted on 2026-11-02.

### 5. How the work went
- 2026-10-29 (run 20261029-222125): `f85-01` started, found its ADR still Proposed, and stopped without a change: right to stop. The approval had reached another file with the same number. A terminal session fixed that on 2026-11-02, and the ADR is now ADR 40.
- 2026-11-03 16:39 ([session](../sessions/2026-11-03-1639.md)): `f85-01` (the pictures) parked for a Claude limit, then built by the lead in 17 minutes; 0 local tokens on it.
- 2026-11-03 20:12 ([session](../sessions/2026-11-03-2012.md)): `f85-02` (the panel, 14 minutes) and `f85-03` (planner, review and setup words, 6 minutes), built by the lead first time; 0 local tokens.
- Lessons:
  - **The review was never given the mock-up.** The brief looked for the mock-up under the card's full name, while mock-ups go by the short one, so every card would have read "mock-up: none". The test used a card named `f1`, where both names are the same. Fixed in this review, with a test that tells them apart.
  - **A card reviewing itself found that bug.** The brief said "none" while the card's doc named its mock-up. It is worth running a new review feature on its own card.
  - **A ticket's "in Chromium" line reached main with no browser test.** The switches were untested until this review added two tests. They worked first time, but nothing had shown that.

### 6. What next
- **Product:** on hold, as you asked (factory first). When you lift the hold, travel-companion's `[shots]` card is the one you'd enjoy: its text is ready in F85's "Other projects".
- **Factory:** the Done when lines of a lead ticket are read by nobody but its author before the review, since lead tickets get no checkpoint here. I'd have the review's brief ask for each Done when line to be matched to a test. Text ready to paste in the Plant box: "The review checks every Done when line of its card's tickets against a test or a picture, and lists the ones with neither (F85: 'in Chromium' reached main untested)."

### 7. What clogged the factory line
- **About 4 days waiting for the ADR's approval to land** (2026-10-29 to 2026-11-02): the owner's Accept reached another ADR with the same number, twice. The runner now accepts the exact file, so this is already unclogged.
- **About 3 hours 10 minutes parked for a Claude limit** (`f85-01`, 16:40 to 19:51 on 2026-11-03): the ticket was the lead's by design, so it had to wait. Nothing to unclog, unless you mark the card to use Claude's reserve.
- **Two runner restarts** after `runner/` changed: the designed stop, a few minutes each. Nothing to unclog.

## What was built
- `runner/shots.py` (f85-01): the list of pages from the card's `## Before and after`; one data folder from the project's `prepare`; the app served from main and from a temporary worktree of the start tag; Chromium in a process of its own, with only GET requests to that address let through; `shots.json` saying what was taken and why not. `review_milestone` calls it before each round, and nothing in it can stop a review.
- `runner/config.py` and `.softfield/project.toml`: `[shots]`, and Softfield's own (a copy of the metrics database, ADR 40 item 4).
- `factory_dashboard/milestones.py`, `milestone.html`, `dashboard.css` (f85-02): the panel and the route that serves only named pictures of a card the project has.
- `runner/prompts.py`, `lead.md`, `bootstrap.md`, `review_pictures` (f85-03): the planner lists the pages, the review compares, the setup session sets up `[shots]`.

Tests read closely. Existing tests a developer edited: one, `test_look.py`'s address values, which gained `file` for the new route: an honest change. `test_shots.py` is strong: a real server and real worktree, plus real Chromium against a page that POSTs, submits a form and reaches for another host. No leftover process, worktree or folder, a failure included.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | blocking | claude | The review's brief looked for the mock-up under the full key, so every card read "mock-up: none" (ticket f85-03) | Fixed: the short key; the test now uses a full key |
| F2 | should-fix | claude | "The plan's mock-up ›" read only the thread's latest proposals, so it vanished on F85's own page and on 5 of the 53 threads with a mock-up (f85-02) | Fixed: the latest mock-up on the thread, with a test |
| F3 | should-fix | claude | f85-02's "in Chromium" Done when had no test, and nothing tested that a card without a sheet shows no panel | Fixed: two browser tests with the layout check, and one for the unsigned card |
| F4 | should-fix | claude | A `project.toml` that doesn't parse gave a 500 on a card's page with pictures: `project_shots` raised what the page doesn't catch (f85-01) | Fixed: it raises `ConfigError`, with tests in both places |
| F5 | should-fix | claude | The setup guide never named `$SOFTFIELD_SHOTS_DATA` or `live`, and sat inside "Protected paths" (f85-03) | Fixed: its own step, naming both |
| F6 | nit | claude | The panel's captions dropped the mock-up's "at the card's start" and "main now" (f85-02) | Fixed, and tested |
| F7 | nit | later | A card's "What it's about" shows Markdown marks as written (older code, seen in the pictures) | `bug-58` |
| F8 | nit | report | A redirect from the app to another port of 127.0.0.1 would pass the browser's rule, against ADR 40 item 3: routes aren't run again on a redirect, and the name rule excludes 127.0.0.1. Read from the code, not run. It needs the project's own app to redirect, and only a GET could get through | Suggested fix if a project ever needs it: the guard fetches with redirects off and fulfils the answer |
| F9 | nit | report | Small tidying in `milestones.py`: `_is_factory` repeats the check in `_factory_project`; `suffix = q if q else ""` does nothing; an address with `#` gets its `?project=` after the fragment; one redundant assertion in `test_app.py` | Suggested fix: tidy them when that code is next touched |
| F10 | nit | claude | f85-01 changed one space on `max_attempts` in `project.toml`, out of line with its neighbours | Fixed |

No checkpoint ran (three lead tickets), so there are no checkpoint verdicts. Score: 7/10. The picture-taking is careful and well tested, and each decision is followed. But the comparison the card promised couldn't have worked on any real card, and a fixture hid it.

Checked and fine: the route refuses other names, `..`, other cards and symlinks; `p.say | safe` only ever holds the page's fixed sentences; a reason is escaped; an address becomes a link only to `live` or the dashboard; both trees share one data folder; the worktree and data are removed after a failure. The ticket said Before shows first on a phone, while the mock-up you approved shows After first: built as the mock-up, which I kept.

After the fixes, the whole runner and dashboard suite passes (3,014 tests, on six workers), and mypy and ruff pass on the changed code. A first run on one worker reached its time limit, and my rewording of the setup guide failed one test there; that's fixed too. Round 2 still has to read these fixes.

The French: no `coucou/locale/fr/` change in this milestone.

## Factory
- **Flow:** three lead tickets, all merged. One park for a Claude limit, the ADR's blocked wait, no stops for the owner in this run, and the designed restarts for `runner/` changes.
- **Models:** Opus built f85-01, Sonnet f85-02 and f85-03; no local model, by design: protected runner code and a route that serves files from disk. Sonnet's two tickets are where F1, F2, F3, F5 and F6 came from, while Opus's had F4 and F10, the smaller ones. It's a small sample, but f85-03's bug was a one-word path rule its test couldn't see.
- **What to change:** a lead ticket has no checkpoint, so its Done when lines reach the review unchecked (see "What next"). Also, `lead.md`'s "update Known range above" points at a section that's no longer there; it should go when `lead.md` is next edited.

<!-- runner report -->
<!-- /runner report -->
