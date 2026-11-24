# Milestone F284: Run and Stop show what the app is doing, with its logs on its plate

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-21.

## Notes
I find the docker run buttons a bit unresponsive. If I click run it says starting and if I refresh the page it's gone and I have to click run again. I find it difficult to know if it's doing things. The logs get me to a different page rather than show there directly. There's been a few times where I thought it was doing nothing but it was actually doing something. I had to click pause resume a few times  on the log page and eventually it works

## Goal
Pressing Run or Stop on a project's app always shows what the app is doing, until it is done: through a page refresh, a dashboard reload and a long image build, on the Projects page itself, with its logs one tap away in the plate.

## What happens today
Read in the code on 2026-11-23 (`factory_dashboard/stacks_routes.py`, `runner/stacks.py`, `_partials/app_row.html`):
- **Run waits for the whole start in one request.** `run_app` calls `stacks.start`, which runs `docker compose up -d --build` to the end (up to 15 minutes, `DOCKER_TIMEOUT`). "starting…" is only the browser waiting for that answer (`.htmx-request`); nothing on the server knows a start is under way.
- **A refresh forgets it.** The page draws the row from `docker compose ps`; while the image builds no container exists yet, so the row says Stopped and offers Run again. A second Run waits up to 60 s for the first one's lock, then says "busy", or runs `up` again.
- **The dashboard reloads after every Softfield merge** (`update_live`, about every 46 minutes lately): a press caught by a reload loses its answer and the row stays on "starting…".
- **The build's output goes nowhere.** `start` captures it and keeps only the last lines of a failure. The logs page shows `docker compose logs`, the containers' own output, which is empty until they start: the app looked idle while it was building.
- **Pause and Resume on the logs page only stop and restart its 5-second refresh**; they can't start anything. The lines appeared once the build finished, which happened to follow the presses.
- **The row never refreshes itself**: after a press it shows the answer to that press; after that, only a reload of the page.

## Decisions
- **D1. Run and Stop answer at once.** The routes start the command in a process of its own (its own session, so a dashboard reload doesn't end it) and answer the row straight away, already in its busy state. The command, the lock and the Compose calls stay in `runner/stacks.py` (F239 D1); the route only names the project, as today.
- **D2. What the app is doing is written down.** While it holds the project's lock, a command writes `~/.local/share/softfield/run/<project>.doing.json`: `{"doing": "start" | "stop" | "update", "since": <ISO time>, "pid": <int>, "commit": <short main commit or "">}`, and removes it when it ends. `follow_main` writes `update` the same way. A record whose `pid` is no longer alive counts as absent.
- **D3. Two new words.** `state` reads the record first: `doing` start gives `STARTING`, stop gives `STOPPING` ("stopping"), update gives `UPDATING` ("updating"), each with `since` and, in `detail`, the build's last line. Otherwise `ps` decides, as today.
- **D4. The build is kept.** `start` and `follow_main` stream `up --build`'s output into `run/<project>.build.log` (replaced at each start, so it holds the last one). `stacks.build_lines(stack, lines=40) -> str` reads its end.
- **D5. A press while busy changes nothing.** Run or Stop on a busy app answers the busy row, unchanged, without starting anything; the row offers neither while busy.
- **D6. The row keeps up by itself while busy:** `GET /projects/{name}/app` (no guard: it reads) answers the row; a busy row asks for it every 5 s (`[window.liveIdle()]`, as the other live parts), and stops once it is settled. A busy row shows the word with a pulsing hazard lamp, the dashed hazard edge of "on its way", what is happening in words ("Building the image · 1 min 40 s", "Stopping", "Updating to main a1b2c3d"), and the build's last line.
- **D7. Logs open in the plate.** Logs becomes a toggle: under the row, the last 40 lines in a 12-line box, refreshed every 5 s while open; while the app is busy or its last start failed, the box shows the build's lines under a "Build" label, then the app's. "All lines" leads to the logs page, which stays. Closed again, it stops asking.
- **D8. The logs page says the same:** the busy word and time, the build's lines while busy, and "No lines yet: the app hasn't started" instead of an empty box.
- The picture to build: `.softfield/cards/f284-mockup/app-row.html`.

## Tickets
- f284-01 (lead): the record, the two words, the build log and the detached start and stop in `runner/stacks.py`; Run and Stop answer at once (D1 to D5).
- f284-02 (developer): the busy row and its own refresh (D6).
- f284-03 (developer): logs in the plate, and the logs page's build lines (D7, D8).

## Before and after
- `/projects`
- `/projects/duck-ascii-test/logs`
