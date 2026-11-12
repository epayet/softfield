# Milestone F239: Run, stop and open each product's app from the Projects page, on Docker Compose

> **State:** ready · **Priority:** 0 · **Area:** factory · **Fast lane:** yes
> Planted by the owner on 2026-11-10.

## Notes
I want to be able to run projects directly from the projects page with a run button and then a stop button (ideally without waiting for the runner to pick things up, but that can wait if it's harder to do). For this, I imagine that every project has a docker compose stack. The projects that have a web interface will have a link to the app once it's running, all apps run locally on the machine. If a project has multiple web apps available, the factory needs to know somehow which container is the main one, either through docker compose config file if that's doable of a local project softfield config file for the project. I expect that the run button runs the latest main at all time, and gets updated every time the main gets updated automatically. I believe that most projects have a similar mechanism at the moment with a live folder, we can keep something like that if it makes sense or something else if docker makes it easier. I believe it's currently bespoke per project, so something a bit more structured could make sense. Again, it shouldn't be factory specific, anyone just running the project speratetely should be able to with regular docker compose up stop down commands. Projects currently don't have docker setups so to be able to have the run buttons I'll have to plant a card but the factory should be aware of what needs to be done to achieve it. Run buttons should only appear for those who have docker stacks. Those who don't can be suggested a button to plant the card to plan getting the stack.  The factory itself will never have those buttons as an exception, as it's running with separate global commands. The port allocation will have to be careful, either making use of free ports for new projects hardcoded or smart port forwarding. We'll have to be careful with Devs working on tickets using different docker stacks. The SQLite db files might have to be mounted or moved to different places? Production databases and dev databases should not be mixed, especially with less intelligent  agent Devs. There should be an ability to see the docker logs through UI, either live logs or latest snapshot. It should be clear when there is an issue. I'm taking the conductor app as an inspiration here where there a conductor setup script for each project, we might not need one here. There is a whole git workspace management there as well that I don't think we need just yet

## Goal
Each product's app runs from the Projects page: Run, Stop, Open and Logs, always on main's latest commit, on a plain Docker Compose stack anyone can also run by hand. Softfield's part is the runner, the dashboard and the recipe; each product gets its stack from a card of its own.

## Decisions
The joints are in [ADR 46](../adr/46-run-a-project-from-the-dashboard.md) (Proposed); nothing is queued before it is Accepted.
- **D1. One module owns every Docker call:** `runner/stacks.py`. The runner and the dashboard both import it; nothing else runs `docker`. Every call goes through one function, `_docker(args, cwd, env)`, which the tests replace: no test starts Docker.
- **D2. Its functions:** `stack_for(repo) -> Stack | None` (from `[run]`, None without it or for Softfield itself), `state(stack) -> StackState` (`word`: running, starting, stopped, crashed, update failed; `url_port`; `since`; `detail`), `start(stack)`, `stop(stack)`, `logs(stack, service=None, lines=200) -> str`, `follow_main(stack) -> bool`. Commands always carry `-p <project>` and run in the checkout, with `APP_DATA` set (ADR 46 items 3 and 5).
- **D3. Where things live:** the checkout `~/.local/share/softfield/run/<project>`, the data `~/.local/share/softfield/data/<project>`, the last update's result `~/.local/share/softfield/run/<project>.json` (`{"commit", "ok", "at", "tail"}`): `state` reads it for "update failed". A lock file beside it keeps the runner and the dashboard from running two Compose commands at once on one project.
- **D4. `[run]`:** `project_run(repo) -> Run | None` in `runner/config.py`, beside `project_shots`: `service` required, `path` default `/`.
- **D5. The dashboard's routes:** `POST /projects/{name}/run` and `POST /projects/{name}/stop`, guarded by `from_the_dashboard` in `factory_dashboard/requests.py`; a name not in the registry, or one without `[run]`, answers 404. They answer with the plate's app row, re-drawn. `GET /projects/{name}/logs` is the logs page; `?service=` picks one.
- **D6. The page:** as in the mock-up, `.softfield/cards/f239-mockup/projects-run.html`. The app row sits under each plate's facts; Run is the hazard `btn go`, Stop a plain button; a crashed app's row and its Needs you line use `--fail`, words always beside the colour.
- **D7. The plant buttons** send a `plant` request for that project:
  - no stack: "Give <project> a Docker Compose stack the Projects page can run (ADR 46; what it needs: runner/instructions/run-stack.md)";
  - crashed or update failed: "<project>'s app <crashed | didn't update> at <time> on main <commit>: find out why and fix it", then `state`'s detail and the last 30 log lines in a fenced block (the planner can't run Docker, so the plant carries what it needs).
- **D8. Before each rebuild** `follow_main` copies the data folder to `~/.local/share/softfield/data/<project>.before-<short commit>` and keeps the 3 newest (ADR 46 item 4). The copy failing stops the rebuild: the app keeps running on the old commit and shows update failed.
- **D9. Docker on the machine** is assumed. f239-01 checks it (`docker compose version`, `docker info`); if it fails, the ticket still lands, and its last message says what is missing, for the review to put in front of the owner.

## Tickets
- f239-01 (lead): `[run]` and `runner/stacks.py`.
- f239-02 (lead): the runner follows main.
- f239-03 (lead): Run and Stop routes, and `run-stack.md`.
- f239-04 (lead): replan (ADR 16 item 7).
- f239-05 (developer): the app row on the Projects page.
- f239-06 (developer): the logs page.
- f239-07 (developer): a crashed app in Needs you.

After sign-off: each product plants its stack card from its own plate (Coucou, Travel Companion, Coaster Ranker).

## Before and after
- `/projects`
