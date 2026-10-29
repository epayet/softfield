# Milestone F163: A browser check for htmx parts: swap, then post again

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-21.

## Notes
Give developers a browser-level check for htmx parts: render the part, apply the swap and post
again. Two of M1's blockers would have failed it. -- from travel companion m1

## What we know (2026-10-27)
- **One of M1's two blockers, not two.** Travel companion's M1 review (`travel-companion/.factory/reviews/m1-first-suggestions.md`): F1 (Undo answered the chips without their row's id, so a second Undo did nothing) fails a swap-then-post-again check. F2 (Try again woke the worker inside its transaction) is a commit race between two threads: no browser test sees it.
- **It kept coming back after M1,** in four of Travel companion's five later reviews, each found by the review, never by a test:
  - F1 review, F1 (blocking): the row swapped in after a restamp had no chips; the tests read only the page.
  - F3 review, F1: Forget then Undo; "the tests checked each response on its own, not the page after two swaps".
  - F4 review, F1–F2: a count line that never showed (the form's `oninput` misses boxes outside it); three fix rounds, about an hour, and the bug stayed. "What happens in the browser (events, swaps) can't be checked by a Django test."
  - F6 review: f6-02b met every Done-when line by string and broke the form's values; "a UI ticket needs one test that reads the form off the rendered page and posts it back".
- **Developer notes 2, 3 and 5** in `travel-companion/docs/agents/developer.md` already ask for "test the answer after a swap, and after a second one". F1, F3, F4 and F6 came after them: a note the developer can't run doesn't hold.
- **Travel companion has no browser test.** Its tests use Django's test client only (`tests/test_views.py`, pytest-django); Playwright is not in its `pyproject.toml`. Its pages use htmx 2 (`stampu/static/vendor/htmx.min.js`) and one script (`stampu/static/notes.js`).
- **Softfield already has the pattern:** a browser test that loads the page from the app's test client and serves `/static/` from disk with `page.route`, no server and no port (`docs/agents/developer.md`, "Factory line"; `tests/factory_dashboard/test_line.py`). Chromium for Playwright is already on this machine for Softfield's suite.
- **The other "Factory" lines of that review** (the checkpoint reading `hx-target`/`hx-swap` against what the view answers; a page ticket naming the second click) are about Softfield's own briefs: `CHECKPOINT` in `runner/prompts.py` and `docs/task-writing.md` say nothing of a second request.

## Decisions
- **D1: the check is a real browser, not a swap simulator.** A Python helper that applies `hx-target`/`hx-swap` to the test client's HTML would catch M1's F1, the F1 and F3 reviews' and F6's, but not F4's (a script's event). Playwright runs the real htmx and the real scripts, and costs about a second a test.
- **D2: no server.** Each request the page makes goes to Django's test client through `page.route` and is answered from it, as Softfield's dashboard tests do with FastAPI's: no port, no thread, the test's own database. Django refuses database calls inside Playwright's event loop: the fixture sets `DJANGO_ALLOW_ASYNC_UNSAFE` for the browser tests only.
- **D3: it is built in Travel companion, by its lead, on its own board.** The fixture, the first test (Undo two chips) and the worked example live in that repo; this job can't queue a ticket there. A new kind of work, so the lead builds the first one and adds it to that project's worked examples (`docs/agents/lead.md`, "Plan"). The owner plants it on Travel companion's board (text in this card's thread).
- **D4: not a factory feature for every project yet.** One project uses htmx with Django; shipping a fixture from `runner/templates/` for every new project waits for a second one (low ceremony).
- **D5: Softfield's share is the briefs (f163-01):** a page ticket's Done when names the second request and asks for the browser test where the project has one (`docs/task-writing.md`); the checkpoint reads each `hx-target`/`hx-swap` a diff adds against what its view answers, and looks for a test that makes the request twice (`CHECKPOINT` in `runner/prompts.py`). Both help every project, Travel companion first.

## Tickets
| # | Id | Who | Difficulty | What |
|---|----|-----|------------|------|
| 01 | second-request-in-briefs | lead | 2 | The ticket-writing line and the checkpoint's line on the second request (D5) |
