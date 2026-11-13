# Review: F239, Run, stop and open each product's app from the Projects page

Round 1 of 3, 2026-11-13. Eight tickets: five by the lead (f239-01 to 04, 08), one escalated to the lead (f239-05), two by the local model (f239-06, 07).

## Sign-off sheet

### 1. What changed
- Each product's plate on the Projects page now has an **App** row. Today no product has a Docker Compose stack yet, so each one says "No stack yet: the factory can't run it." with a **Plant a card for a stack** button; Softfield's own plate has no row, as you asked.
- Once a product has a stack (its own card, from that button), the row shows its state in words beside a lamp (Running, Starting, Stopped, Crashed, Update failed, Docker isn't available), **Run** or **Stop** (they act at once, no waiting for the runner), **Open ↗** with its port while it runs, and **Logs**.
- The app always runs main: when main moves, the runner moves the app's own checkout and rebuilds it if it was running, after copying its data folder (the last 3 copies are kept). A failed rebuild leaves the old app running and says "Update failed". Pressing Run also rebuilds, so a stopped app never comes back on an older main.
- A crashed app or a failed update turns its row red, adds a red line to **Needs you** with its Logs, and offers **Plant a card to fix it**, which carries the error and the last 30 log lines for the planner. Stopping the app or running it again clears the line.
- The **Logs** page shows the app's state and its last 200 lines, refreshed every 5 seconds, for all services or one, with Pause.
- `runner/instructions/run-stack.md` is the recipe the stack cards will follow (a fixed port from 8100–8199, data under `APP_DATA`, migrations at start, nothing Softfield-specific).

Matches the mock-up for what the real data shows (every product has no stack yet, so the after pictures show only the "No stack yet" rows, as the mock-up draws them). The Run, Stop, Open and crashed rows and the logs page aren't in the pictures for that reason; the tests draw them.

### 2. How to test it yourself
1. On your phone, open the dashboard's **Projects** page: coaster-ranker, travel-companion and coucou each show "No stack yet" and **Plant a card for a stack**; softfield shows no App row.
2. Press **Plant a card for a stack** on one product (coaster-ranker is the smallest): the button gives way to "On its way", and the card appears on its board at the runner's next pick.
3. When that card is done and merged, its plate shows **Stopped** and **Run**. Press Run: the row shows "starting…" while it builds, then **Running** and **Open ↗ :81NN**. Open it from the phone on the home Wi-Fi.
4. Press **Logs**: lines appear and move every 5 seconds; pick one service in the chooser; press Pause and check they stop.
5. Press **Stop**: the row says Stopped and offers Run again.

### 3. Left for later
- Following main builds inside the runner's loop, and Run builds while the page waits (finding F5, said here only): fine while builds are small.
- No bug tickets were set aside.

### 4. Decisions waiting for you
None. ADR 46 was accepted before the work. One small thing decided in the review and said here: Run is now `docker compose up -d --build` rather than ADR 46 item 6's `up -d` (the same fixed command, with nothing from the page in it), because otherwise a stopped app would come back on an older main.

### 5. How the work went
- 2026-11-12 17:03 and 18:01 ([1703](../sessions/2026-11-12-1703.md), [1801](../sessions/2026-11-12-1801.md)): f239-01 and f239-02 merged by the lead.
- 2026-11-12 18:17 ([1817](../sessions/2026-11-12-1817.md)): f239-03 (parked once for Claude's limit, then merged), f239-04 replan and f239-08 merged by the lead.
- 2026-11-12 20:30 ([2030](../sessions/2026-11-12-2030.md)): f239-05 failed three local attempts (two timeouts, one kept an edit to protected `runner/stacks.py`), escalated and done by the lead.
- 2026-11-13 00:46 ([0046](../sessions/2026-11-13-0046.md)): f239-06 (second attempt) and f239-07 (first attempt) merged by the local model.

Lessons:
- **The replan paid off:** f239-04 found two gaps (services, the failed commit) that developers couldn't fill in protected `runner/`, and f239-08 filled them before anyone started.
- **Green gates aren't the goal:** f239-06 passed every gate with no polling, a dead Pause and a 500 on real Docker data, because its tests only looked for words on the page. Fixed in review with tests that read the poll's markup and Docker's real time format.
- **A protected file kept costing attempts:** f239-05 kept its `runner/stacks.py` edit through three attempts; the developer note 11 now says what to do.

### 6. What next
- **Product:** plant the stack card for coaster-ranker first (smallest, one web service), then travel-companion and coucou. Once coucou runs from the page, Mum's screen and its sender can be checked from the phone without a terminal.
- **Factory:** a developer UI ticket that promises behaviour (polling, a pause) should name the browser test that proves it in `tests:`; f239-06's ticket listed only words to look for. Worth a line in `task-format.md` when the next UI card is planned.

### 7. What clogged the factory line
- **f239-05's three local attempts: about 3 h 42 min** (75.6, 71.7 and 75.0 min) with nothing merged, before a 28-minute escalation. A difficulty-4 ticket across the Projects page, a new partial, the routes module and the CSS was too wide for the local model. Unclog: route a ticket that spans two templates plus a module to the lead at planning (the routing check F84 asked for).
- **f239-06's first attempt: 20 min** stopped with no edit. Unclog: developer note 12 (first edit within ten steps), already added.
- **f239-03 parked once for Claude's usage limit** (a 0.3-minute failed start); it waited for the reserve.

<!-- runner report -->
<!-- /runner report -->

## What was built
- `runner/config.py`: `Run` and `project_run` read `[run]` (`service`, `path`).
- `runner/stacks.py`: the one module that runs Docker. `stack_for`, `start`, `stop`, `state`, `logs`, `services`, `follow_main`, a per-project lock shared by the runner and the dashboard, the update result file and the data copies.
- `runner/loop.py`: `_follow_main` after each job and before each pick; it never raises.
- `factory_dashboard/stacks_routes.py`: `POST /projects/{name}/run` and `/stop` behind the `/requests` guard; `GET /projects/{name}/logs`; `AppRow`, the fix and stack plants.
- `factory_dashboard/projects.py`, `projects.html`, `_partials/app_row.html`, `app_logs.html`, `dashboard.css`: the App row, Needs you lines, the logs page.
- `runner/instructions/run-stack.md`: the recipe for a product's stack.

## Findings
| id | grade | route | what | resolution |
|---|---|---|---|---|
| F1 | blocking | claude | Logs page: no refresh, Pause dead, chooser sent nothing and swapped the whole page into the panel; 500 on real Docker's `CreatedAt` | Fixed: polls itself every 5 s unless paused, GET form chooser, scroll kept at the bottom, render time; 2 tests |
| F2 | should-fix | claude | Run reused an older main's image after main moved while stopped | Fixed: `up -d --build`; test |
| F3 | should-fix | claude | A failed update outlived Stop and Run (row and Needs you stuck) | Fixed: counts only while a container is up; a good start records main as good; 2 tests |
| F4 | should-fix | claude | Needs you drew a card's desk line twice and hid its crash; app line linked to Planning, not red | Fixed: both lines once, right count, logs link, `--fail`; test |
| F5 | nit | report | Builds run inside the runner's loop and the Run request | Said here; fine while builds are small |

Tests read: f239-06 edited `test_stacks_routes.py`'s `Docker` fake (added `config --services`, a fair extension); f239-07 edited `test_projects.py` only by adding tests. Two of those were weak: one asserted only "in all", and `test_needs_you_shows_even_with_no_desk_items` deletes `owner_requests`, which doesn't empty a desk. The new count test covers what they missed. f239-07 also changed `stacks_routes.py` outside its `files:` (two small `AppRow` properties): fine as it is. f239-03's `test_look.py` edit widens the dashboard's allowed POSTs to Run and Stop, as ADR 46 item 6 says. No French in this milestone.

Checkpoints raised nothing. F1 and F4 were plain in the developers' diffs (no `hx-trigger` in a page promised to refresh; an `if`/`elif` over a list holding the same card twice).

## Factory
- **Flow:** no stops for the owner; one park for Claude's limit (f239-03); one escalation (f239-05) after three local attempts.
- **Models:** the lead's five tickets passed first time but one (f239-03 needed a second start after the park). Qwen: f239-05 0/3, f239-06 1/2, f239-07 1/1, but both merged tickets carried a real defect past green gates.
- **What to change:** a UI ticket's promised behaviour (polling, pause, a chooser that sends) needs a test that reads the markup or drives the browser, named in the ticket. Proposed as the factory "What next" above; no ticket now, since the next UI card's planning is where it applies.
- ADR 02's learnings log: F239 shows that the replan step catches protected-module gaps before developers hit them, and that local UI work with only text assertions passes gates while missing its behaviour.
