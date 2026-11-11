# Milestone F85: Real before and after pictures of the changed pages when you sign a card off

> **State:** ready · **Priority:** 11 · **Area:** factory
> Planted by the owner on 2026-10-09.

## Notes
when i sign off a task, i want, whenever relevant i would like to see screenshots of before after, in a similar fashion of the mock ups

(2026-10-27, on the thread) will this work for other projects like travel companion. i essentially want screenshots of the product, whether the product is softfield or travel-companion or coucou

## Expected outcome
When a card that changed a page is ripe, in any project, its page shows **Before and after**: real pictures of each page it changed, as the page was before the card's first ticket and as it is now, with the same Before / After switch as the mock-ups, on a phone and on a wide screen. The pictures are of that project's own app: the dashboard for Softfield, Stampu for travel-companion, Coucou's screens for Coucou. A line from the review says whether the after matches the mock-up the owner approved. A card that changed no page shows nothing new.

## Done when
- The runner takes the pictures itself at the review: no job gets a browser ([ADR 28](../adr/28-lead-jobs-can-look.md) stays as it is).
- Each project says how its app is served for pictures, in `[shots]` of its `.softfield/project.toml` ([ADR 40](../adr/40-pictures-at-sign-off-in-every-project.md)); Softfield's is set up by this card, and a product is pictured on sample data only.
- The card's page shows them right under "What changed", phone and wide, Before / After; a tap opens a picture at full size.
- The review's "What changed" says in one line whether the after matches the mock-up's Proposed, and what differs.
- The planner names the pages to picture whenever it draws a mock-up, and the setup session sets up `[shots]` for a new project with pages.
- To test: sign off the next Softfield card that changes a page (or F85 itself: its own card page is listed below) and flip Before / After on your phone. Travel-companion and Coucou show theirs once their own card sets up `[shots]` (see "Other projects").

## Before and after
- `/milestones/f85-when-i-sign-off-a-task`

## Plan (lead, 2026-10-27)
- **Today:** the sign-off is read from text ("What changed", "How to test"). The only pictures are the mock-up's, drawn before the work; nobody looks at the built page against them ([F72](f72-i-really-like-the-mock-up.md) "Later", ADR 28 "Later").
- **Proposed ([ADR 40](../adr/40-pictures-at-sign-off-in-every-project.md)):** the planner lists the pages a card changes; at the review the runner starts the project's app twice (the code at the card's start and main now, on the same data) and pictures each page; the review compares the after with the mock-up, and the card's page shows both.
- Mock-up: `.softfield/cards/f85-mockup/before-after.html` (real values: F172, Mark a card to use Claude's reserve, ripe now).
- Tickets: `f85-01-pictures-at-the-review` (lead, runner), `f85-02-before-and-after-on-the-card` (lead, dashboard: it serves files from disk), `f85-03-planner-lists-the-pages` (lead, prompts and the setup guide). 02 and 03 wait for 01. All wait for ADR 40.

## Decisions
- **D1: which pages.** A card doc's `## Before and after` section lists the app's addresses, one bullet each, in backticks (`/board`, `/memory/`). The planner writes it whenever it draws a mock-up (F72 D1); a card with no such section gets no pictures ("whenever relevant"). A section, not a header field: the header is rewritten at each state change and sign-off. `runner/shots.py` owns `pages(doc_text) -> list[str]`.
- **D2: who takes them, and when.** The runner, at the review, before each round (`review_milestone`, `runner/milestone.py`), in the card's own project: the *after* from main, the *before* once from `<key>-start` (the tag the review already diffs from) checked out in a temporary git worktree. Both run on one data folder made once by the project's `prepare`, so the only difference is the code. The folder and the worktree are removed when the pictures are done.
- **D3: how, in every project** (ADR 40 items 2 and 3). `[shots]` in `.softfield/project.toml` holds `prepare`, `serve` (with `{port}`) and, optional, `live` (where the owner opens the running app, for D7's links; the pictures never use it). `runner/shots.py` runs `prepare` once, then for each tree runs `serve` there on a free port of 127.0.0.1 with `SOFTFIELD_SHOTS_DATA` set to the data folder, waits for that port to take a connection (D11), and pictures each address in Chromium through Playwright; the browser lets only GET requests to that address through. The server is stopped after. Two widths: phone (390 px) and wide (1440 px), the whole page; Softfield's in the dark theme. A project without `[shots]` gets none, and its review runs as today.
- **D4: Softfield's own `[shots]`.** `prepare` copies the metrics database into the data folder (the review can already read it, ADR 28); `serve` starts the dashboard on that copy (`softfield dashboard --db`, or the module the same way, run from the tree being pictured so the before uses the old code). It is set up and proven by f85-01.
- **D5: where they live.** `<project>/.softfield/var/shots/<key>/<when>-<width>-<n>.png` (`when` is `before` or `after`, `width` is `phone` or `wide`, `n` the address's place in the list, from 1), plus `shots.json` there: the addresses in order and, per picture, whether it was taken or why not. Not in git (the folder is ignored); each review round takes the after again, and the before stays as long as the start tag is there.
- **D6: what can go wrong, shown plainly.** An address the old code answers 404 (a new page) gets "This page didn't exist before" instead of a picture. A before the old code can't draw (it won't start, an older schema) gets "The page before couldn't be drawn", with the reason in `shots.json`; the after still shows. A shot failing never stops the review.
- **D7: on the card's page.** A "Before and after" panel right under "What changed" (`factory_dashboard/templates/milestone.html`), only when the card's `shots.json` exists, for any project's card: a Before / After switch and a Phone / Wide switch; on a wide screen Before and After sit side by side and the switch picks phone or wide. Each address is a plate with its address in mono; a tap opens the picture at full size. The address itself is a link that opens the page as it is now in a new tab (owner, 2026-10-27), so the owner can look for themselves: on Softfield, the dashboard's own page; in another project, the address under its `[shots] live` (the app as the owner runs it, say `http://192.168.1.20:8000`). A project without `live` shows the address as plain text, never a link that goes nowhere. Pictures come from `/milestones/{key}/shots/{file}` (with the page's `?project=`), which serves only `.png` files named as D5 says from that project's card folder (anything else is 404). The planned picture is one link away: "The plan's mock-up ›".
- **D8: the review compares.** The review's brief (`REVIEW`, `runner/prompts.py`) gives it the after pictures' paths and the card's mock-up; it opens them with Read and writes one line at the end of "What changed": "Matches the mock-up" or what differs. A clear difference is a should-fix finding like any other. About eight pictures per round for a card with two pages.
- **D9: products on sample data only** (ADR 40 item 4). A product's `prepare` builds its data from the project's own fixtures: no live database, no photo of Mum, no note of the owner's, and no call to a model or another service while pictures are taken. Pages behind a sign-in or a paired device are signed in by the project's sample data, never by a back door in the product.
- **D10: new projects.** The setup guide (`runner/instructions/bootstrap.md`) has the setup session fill in `[shots]` for a project with pages, with sample data, and take one picture to prove it.
- **D11: a slow page still gets its picture** (owner, 2026-11-05: "why not just a screenshot anyway?"). The app counts as up once its port takes a connection; each picture then has the browser's 30 s. `ready` goes (ADR 40, Amendments). A reason says what happened in plain words, and quotes the app's output only when the app stopped by itself.
- **D12: a page drawn without its stylesheet is not a picture** (owner, 2026-11-11, coaster-ranker's m1: every picture was plain unstyled HTML, and the panel counted them as taken). While a page loads, the browser notes every stylesheet that fails or answers 400 or more; such a picture is recorded `failed`, with the reason `drawn without its stylesheet: <address> answered <code>` (or `was refused`, for one on another host, ADR 40 item 3). The file is kept beside it for whoever debugs the setup; the panel shows the reason, as for any failed picture. No new state on the page.
- **D13: a card with a changed page gets pictures even when its plan listed none** (owner, 2026-11-11: "there should be at least an after screenshot"). In round 1, when the diff changes what a page shows and the card doc has no `## Before and after`, the review writes the section into the card doc. Right after any round whose list changed, the runner takes the pictures again, the before included: the start tag exists for every card, so a before is there whenever the page was. Cards planned before F85 are the ones this catches.
- **D14: pictures follow their setup until the sign-off.** `shots.json` keeps a fingerprint of the project's `[shots]` and the list it was taken with. At each pick, a ripe card (reviewed, not signed off) whose project's `[shots]` or list no longer matches gets new pictures, with no Claude job. A picture that failed alone is not taken again, so a broken setup can't start an app at every pick; fixing the setup is what brings the pictures back. A list from before this change has no fingerprint and counts as changed, once.

## Other projects
Their `[shots]` is their own work, on their own board, once this card is built. Text ready to paste into each project's Plant box:
- **travel-companion:** "Set up pictures at sign-off (Softfield ADR 40): a `[shots]` section in .softfield/project.toml, a `shots_data` command that builds sample asks, dreams, places and notes from fixtures with no call to the model, and settings that use SOFTFIELD_SHOTS_DATA for the database when it is set; `live` is the address I open Stampu at."
- **coucou:** "Set up pictures at sign-off (Softfield ADR 40): a `[shots]` section in .softfield/project.toml serving the public and admin apps on sample data (a paired sample screen, sample photos that aren't Mum's), with no real data and no back door in the device sign-in; `live` is the admin app's address." (Product work is on hold: it can wait on the board.)

## Tickets
| # | id | who | diff | depends | what |
|---|----|-----|------|---------|------|
| 01 | f85-01-pictures-at-the-review | lead | 7 | – | D1–D6: `runner/shots.py` from the project's `[shots]`, called by the review before each round; Softfield's `[shots]` |
| 02 | f85-02-before-and-after-on-the-card | lead | 4 | 01 | D7: the panel and the route serving the pictures, for any project's card |
| 03 | f85-03-planner-lists-the-pages | lead | 2 | 01 | D1 in the planner's brief and `lead.md`; D8 in the review's brief; D10 in the setup guide |
| 05 | f85-05-fix-slow-page-still-pictured | lead | 3 | – | D11: a slow page gets its picture, and a failed picture says why in plain words |
| 06 | f85-06-fix-unstyled-page-not-a-picture | lead | 3 | – | D12: a page whose stylesheet didn't load is recorded failed, with the reason |
| 07 | f85-07-review-lists-changed-pages | lead | 3 | 06 | D13: the review lists a changed page the plan didn't, and the runner pictures it after that round |
| 08 | f85-08-ripe-pictures-follow-the-setup | lead | 4 | 06 | D14: a ripe card's pictures are taken again when its project's `[shots]` or its list changed |

## Unstyled and missing pictures (2026-11-11)
- **Seen:** coaster-ranker's m1 (Import both lists, rank Orlando coasters by drag, compare the two), ripe: five pages, all pictured as plain HTML without the stylesheet. Its review saw it, fixed coaster-ranker's `[shots]`, and wrote "the next round's pictures will show it", but m1 had one round only, so no new pictures come before sign-off.
- **Seen:** cards reviewed since F85 shipped got no pictures when their plan had no `## Before and after`: F61 (Claude usage page "at this rate", signed off 2026-11-11), F9 (Line polish), F192 (fast lane on the board), and F77, F69, F38 and F193, waiting for sign-off now. All were planned before f85-03 taught the planner to list pages.
- **Fix:** D12 to D14. The cards waiting now keep no pictures: D13 acts at a review round, and they have had theirs.

## Blocked on 2026-10-29
- **What happened:** f85-01 started, read ADR 35 (it must be Accepted), found it still Proposed, and stopped without a change: right to stop. Three files were numbered 35 (`35-no-backlog-file.md`, `35-a-marked-card-goes-first.md`, this card's). The owner's approval at 08:14 ("ADR 35 accepted by the owner", `db23e80`) brought this card's file onto main but set the status of the first `35-*.md` in name order, `35-a-marked-card-goes-first.md`, which was already Accepted: `decide_adr` (`runner/owner.py`) and `_accept_adr` (`runner/requests.py`) both take the first file with the number.
- **Why numbers collide:** each planner drafts on its own branch and takes the next number free on main, so cards planned at the same time pick the same one. F127's branch also has a 35 (`35-project-rules-local-and-updatable.md`) and F140's a 36 (`36-copilot-checks-first-within-its-pace.md`): their approvals would go wrong the same way.
- **Fix (2026-11-02, terminal session):** this card's ADR is ADR 40, Accepted. What.

## F219's After that wasn't drawn (2026-11-05)
- **Seen:** F219's page, the Overview (`/`): Before taken, After "the app didn't answer in 180 s". The app was running: its own start-up line is what the message quoted, on its private port. No other job ran then (07:26 to 07:33), and the owner's `--lan` dashboard plays no part.
- **Cause, most likely:** `_answers` in `runner/shots.py` asks for `ready` (`/`) with a 5 s limit, every 0.2 s after it gives up. `/` took about 4 s here on an idle machine (timed by hand through `softfield look page /`, not in the failed run), and a first request on a just-started app takes longer. Each abandoned request goes on running in the app, so the next is slower still, and none comes back in 5 s. The Before, on the older runner code, answered in time. f85-05 confirms this with a slow test app.

## Later
- `softfield look page <address> --shot` for planner jobs (ADR 28 "Later"): the same script, when a question about looks comes that the text can't answer.
- Pictures in the light theme too, if the owner uses it.
