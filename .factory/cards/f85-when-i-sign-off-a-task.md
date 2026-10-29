# Milestone F85: Real before and after pictures of the changed pages when you sign a card off

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-09.

## Notes
when i sign off a task, i want, whenever relevant i would like to see screenshots of before after, in a similar fashion of the mock ups

(2026-10-27, on the thread) will this work for other projects like travel companion. i essentially want screenshots of the product, whether the product is softfield or travel-companion or coucou

## Expected outcome
When a card that changed a page is ripe, in any project, its page shows **Before and after**: real pictures of each page it changed, as the page was before the card's first ticket and as it is now, with the same Before / After switch as the mock-ups, on a phone and on a wide screen. The pictures are of that project's own app: the dashboard for Softfield, Stampu for travel-companion, Coucou's screens for Coucou. A line from the review says whether the after matches the mock-up the owner approved. A card that changed no page shows nothing new.

## Done when
- The runner takes the pictures itself at the review: no job gets a browser ([ADR 28](../adr/28-lead-jobs-can-look.md) stays as it is).
- Each project says how its app is served for pictures, in `[shots]` of its `.factory/project.toml` ([ADR 35](../adr/35-pictures-at-sign-off-in-every-project.md)); Softfield's is set up by this card, and a product is pictured on sample data only.
- The card's page shows them right under "What changed", phone and wide, Before / After; a tap opens a picture at full size.
- The review's "What changed" says in one line whether the after matches the mock-up's Proposed, and what differs.
- The planner names the pages to picture whenever it draws a mock-up, and the setup session sets up `[shots]` for a new project with pages.
- To test: sign off the next Softfield card that changes a page (or F85 itself: its own card page is listed below) and flip Before / After on your phone. Travel-companion and Coucou show theirs once their own card sets up `[shots]` (see "Other projects").

## Before and after
- `/milestones/f85-when-i-sign-off-a-task`

## Plan (lead, 2026-10-27)
- **Today:** the sign-off is read from text ("What changed", "How to test"). The only pictures are the mock-up's, drawn before the work; nobody looks at the built page against them ([F72](f72-i-really-like-the-mock-up.md) "Later", ADR 28 "Later").
- **Proposed ([ADR 35](../adr/35-pictures-at-sign-off-in-every-project.md)):** the planner lists the pages a card changes; at the review the runner starts the project's app twice (the code at the card's start and main now, on the same data) and pictures each page; the review compares the after with the mock-up, and the card's page shows both.
- Mock-up: `.factory/cards/f85-mockup/before-after.html` (real values: F172, Mark a card to use Claude's reserve, ripe now).
- Tickets: `f85-01-pictures-at-the-review` (lead, runner), `f85-02-before-and-after-on-the-card` (lead, dashboard: it serves files from disk), `f85-03-planner-lists-the-pages` (lead, prompts and the setup guide). 02 and 03 wait for 01. All wait for ADR 35.

## Decisions
- **D1: which pages.** A card doc's `## Before and after` section lists the app's addresses, one bullet each, in backticks (`/board`, `/memory/`). The planner writes it whenever it draws a mock-up (F72 D1); a card with no such section gets no pictures ("whenever relevant"). A section, not a header field: the header is rewritten at each state change and sign-off. `runner/shots.py` owns `pages(doc_text) -> list[str]`.
- **D2: who takes them, and when.** The runner, at the review, before each round (`review_milestone`, `runner/milestone.py`), in the card's own project: the *after* from main, the *before* once from `<key>-start` (the tag the review already diffs from) checked out in a temporary git worktree. Both run on one data folder made once by the project's `prepare`, so the only difference is the code. The folder and the worktree are removed when the pictures are done.
- **D3: how, in every project** (ADR 35 items 2 and 3). `[shots]` in `.factory/project.toml` holds `prepare`, `serve` (with `{port}`), `ready` (an address that answers once the app is up) and, optional, `live` (where the owner opens the running app, for D7's links; the pictures never use it). `runner/shots.py` runs `prepare` once, then for each tree runs `serve` there on a free port of 127.0.0.1 with `SOFTFIELD_SHOTS_DATA` set to the data folder, waits for `ready`, and pictures each address in Chromium through Playwright; the browser lets only GET requests to that address through. The server is stopped after. Two widths: phone (390 px) and wide (1440 px), the whole page; Softfield's in the dark theme. A project without `[shots]` gets none, and its review runs as today.
- **D4: Softfield's own `[shots]`.** `prepare` copies the metrics database into the data folder (the review can already read it, ADR 28); `serve` starts the dashboard on that copy (`softfield dashboard --db`, or the module the same way, run from the tree being pictured so the before uses the old code). It is set up and proven by f85-01.
- **D5: where they live.** `<project>/.factory/var/shots/<key>/<when>-<width>-<n>.png` (`when` is `before` or `after`, `width` is `phone` or `wide`, `n` the address's place in the list, from 1), plus `shots.json` there: the addresses in order and, per picture, whether it was taken or why not. Not in git (the folder is ignored); each review round takes the after again, and the before stays as long as the start tag is there.
- **D6: what can go wrong, shown plainly.** An address the old code answers 404 (a new page) gets "This page didn't exist before" instead of a picture. A before the old code can't draw (it won't start, an older schema) gets "The page before couldn't be drawn", with the reason in `shots.json`; the after still shows. A shot failing never stops the review.
- **D7: on the card's page.** A "Before and after" panel right under "What changed" (`factory_dashboard/templates/milestone.html`), only when the card's `shots.json` exists, for any project's card: a Before / After switch and a Phone / Wide switch; on a wide screen Before and After sit side by side and the switch picks phone or wide. Each address is a plate with its address in mono; a tap opens the picture at full size. The address itself is a link that opens the page as it is now in a new tab (owner, 2026-10-27), so the owner can look for themselves: on Softfield, the dashboard's own page; in another project, the address under its `[shots] live` (the app as the owner runs it, say `http://192.168.1.20:8000`). A project without `live` shows the address as plain text, never a link that goes nowhere. Pictures come from `/milestones/{key}/shots/{file}` (with the page's `?project=`), which serves only `.png` files named as D5 says from that project's card folder (anything else is 404). The planned picture is one link away: "The plan's mock-up ›".
- **D8: the review compares.** The review's brief (`REVIEW`, `runner/prompts.py`) gives it the after pictures' paths and the card's mock-up; it opens them with Read and writes one line at the end of "What changed": "Matches the mock-up" or what differs. A clear difference is a should-fix finding like any other. About eight pictures per round for a card with two pages.
- **D9: products on sample data only** (ADR 35 item 4). A product's `prepare` builds its data from the project's own fixtures: no live database, no photo of Mum, no note of the owner's, and no call to a model or another service while pictures are taken. Pages behind a sign-in or a paired device are signed in by the project's sample data, never by a back door in the product.
- **D10: new projects.** The setup guide (`docs/bootstrap.md`) has the setup session fill in `[shots]` for a project with pages, with sample data, and take one picture to prove it.

## Other projects
Their `[shots]` is their own work, on their own board, once this card is built. Text ready to paste into each project's Plant box:
- **travel-companion:** "Set up pictures at sign-off (Softfield ADR 35): a `[shots]` section in .factory/project.toml, a `shots_data` command that builds sample asks, dreams, places and notes from fixtures with no call to the model, and settings that use SOFTFIELD_SHOTS_DATA for the database when it is set; `live` is the address I open Stampu at."
- **coucou:** "Set up pictures at sign-off (Softfield ADR 35): a `[shots]` section in .factory/project.toml serving the public and admin apps on sample data (a paired sample screen, sample photos that aren't Mum's), with no real data and no back door in the device sign-in; `live` is the admin app's address." (Product work is on hold: it can wait on the board.)

## Tickets
| # | id | who | diff | depends | what |
|---|----|-----|------|---------|------|
| 01 | f85-01-pictures-at-the-review | lead | 7 | – | D1–D6: `runner/shots.py` from the project's `[shots]`, called by the review before each round; Softfield's `[shots]` |
| 02 | f85-02-before-and-after-on-the-card | lead | 4 | 01 | D7: the panel and the route serving the pictures, for any project's card |
| 03 | f85-03-planner-lists-the-pages | lead | 2 | 01 | D1 in the planner's brief and `lead.md`; D8 in the review's brief; D10 in the setup guide |

## Later
- `softfield look page <address> --shot` for planner jobs (ADR 28 "Later"): the same script, when a question about looks comes that the text can't answer.
- Pictures in the light theme too, if the owner uses it.
