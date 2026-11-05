# ADR 40: Before and after pictures at sign-off, in every project

- **Status:** Accepted (by the owner, 2026-11-02)
- **Date:** 2026-10-27 (drafted as 35, then 39: other ADRs held those numbers, and the owner's Accepts of 2026-10-29 and 2026-10-31 reached them instead; the runner now accepts the exact file)
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 30](30-many-projects-one-factory.md) item 3 (`.softfield/project.toml` gets a `[shots]` section) and item 7 (the setup session fills it in). [ADR 28](28-lead-jobs-can-look.md) stays as it is: no job gets a browser.
- **Evidence:** F85 (owner, 2026-10-09: "when i sign off a task … i would like to see screenshots of before after, in a similar fashion of the mock ups"; 2026-10-27: "i essentially want screenshots of the product, whether the product is softfield or travel-companion or coucou"). Today a sign-off is read as text only; the mock-up is drawn before the work and nobody checks the built page against it.

## Context
- The three projects serve different apps: Softfield its dashboard (FastAPI, one metrics database, no sign-in); travel-companion (Stampu) a Django app with its own database of your trips and notes; Coucou two Django apps (public and admin) whose screens need a paired device, and photos of Mum.
- The runner can't know how to start each app, or what data it needs, by itself: only the project can say.
- The review already diffs a card from its start tag, `<key>-start`, so the code before the card is always there.

## Decisions (⚑ = deviates from an earlier decision)
1. **The runner takes the pictures, at the review,** before each round: the after from main, the before once, from the start tag checked out in a temporary worktree. Chromium, through Playwright, already installed for the tests. Phone (390 px) and wide (1440 px), the whole page.
2. ⚑ **Each project says how its app is served for pictures,** in `[shots]` of `.softfield/project.toml` (ADR 30 item 3):
   ```toml
   [shots]
   prepare = "uv run python manage.py shots_data"   # fills {data}, a throwaway folder
   serve = "uv run python manage.py runserver 127.0.0.1:{port} --noreload"
   ready = "/"                                       # answers once the app is up
   live = "http://192.168.1.20:8000"                 # optional: where you open the app yourself
   ```
   Both run in the tree being pictured with `SOFTFIELD_SHOTS_DATA={data}` set, so the app's settings point its database and files there. The current `[shots]` commands are used for the before too. A project without `[shots]` gets no pictures; its sign-off is as today. `live` only makes each pictured address a link to the real page, in a new tab; the pictures never touch it. Softfield needs none: its links go to the dashboard itself.
3. **On this machine, and never touching anything.** The app listens on 127.0.0.1 on a free port, only for the pictures, and is stopped after. The browser sends only GET requests to that address: anything else (a form, a request to another host) is refused. The data folder and the worktree are removed after, a failure included.
4. ⚑ **A product is pictured on sample data, never on its live data.** `prepare` makes the data from the project's own fixtures: no photo of Mum, no note of yours, and no call to a model or another service while the pictures are taken. Softfield is the exception: its `prepare` copies the metrics database, which the review can already read (ADR 28).
5. **Which pages:** the card's doc lists them under `## Before and after`; the planner writes the list whenever it draws a mock-up. No list means no pictures.
6. **The review compares the after with the mock-up** you approved and says so in one line of "What changed"; a clear difference is a should-fix finding.
7. **The setup session asks for `[shots]`** (ADR 30 item 7): for a project with pages, it sets up `prepare` with sample data and `serve`, and checks one picture can be taken. Coucou and travel-companion get theirs from a card each, on their own boards.

## Alternatives turned down
- **The runner guessing how to start an app:** every stack differs; a wrong guess draws an error page and calls it the product.
- **Pictures of the live data:** truer, but your private data (Mum's photos, your trip notes) would go into pictures sent to Claude at every review, and a page could change something on load.
- **A browser for the review job (a browser MCP):** turned down in ADR 28: it can press buttons and ties the workflow to one frontier.
- **Taking the before when a card starts:** the runner has no such moment (the start tag is often set at the review), and the data would be days older, so every number would differ as well.

## Consequences
- Every project with pages can show you real pictures at sign-off, once its `[shots]` is set up and its cards list their pages.
- Sample data has to be kept up as the app grows: a page that is empty in the sample shows empty in the picture. The review says so when it sees it.
- A before the old code can't draw (a new page, an older schema) shows a plain sentence, and the after still shows.
- Each review round costs a few seconds per page, and a few cents for the review to look at the after pictures.

## What doesn't change
- What a job may do (ADR 28), the gates, the ticket and card formats (a new optional section in the card doc).
- Nothing is pictured in a project that hasn't set up `[shots]`.

## Amendments
- **`ready` goes (the lead, 2026-11-05, F85):** item 2's `ready` address is removed. The app counts as up once its port takes a connection, and the browser's own limit of 30 s per page decides each picture. F219's After failed with the app running: the Overview took about 4 s on an idle machine, and the `ready` check gave up on it after 5 s and asked again, 180 s long, while the picture itself would have had 30 s. The owner asked "why not just a screenshot anyway?". Only Softfield had set `[shots]`, so nothing else changes.
