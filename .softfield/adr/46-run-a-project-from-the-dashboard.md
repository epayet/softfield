# ADR 46: Run a project's app from the Projects page, on a Docker Compose stack that follows main

- **Status:** Accepted (by the owner, 2026-11-11)
- **Date:** 2026-11-11
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 18](18-dashboard-writes.md) item 2 (the dashboard's only write is a request row) and [ADR 30](30-many-projects-one-factory.md) item 3 (`.softfield/project.toml` gets a `[run]` table).
- **Evidence:** F239 (owner, 2026-11-10): "a run button and then a stop button … ideally without waiting for the runner"; every project has a Docker Compose stack, runs main, follows it, a link to the app, logs in the UI, ports and data handled with care, not factory-specific. Today only Softfield follows main (`update_live` in `runner/loop.py`, ADR 30 item 5); each product's own way of running is by hand and differs. A request reaches the runner only at its next pick, up to most of an hour away.

## Decisions (⚑ = deviates from an earlier decision)
1. **A project's stack is plain Docker Compose,** owned by the project and usable without the factory: `compose.yaml` at its root, `docker compose up -d`, `stop`, `down` work in any clone. What it must have is written once in `runner/instructions/run-stack.md`:
   - the main service publishes its web port on one fixed host port per project, `${APP_PORT:-81NN}`, chosen at setup from 8100–8199 and unused by the other projects;
   - its lasting data (SQLite files, uploads) lives under `${APP_DATA:-./.data}`, a bind mount, with `.data/` in `.gitignore`;
   - `restart: unless-stopped`, so a running app comes back after a reboot until it is stopped.
2. ⚑ **`[run]` in `.softfield/project.toml`** names the main service and, if it isn't `/`, the page to open: `service = "web"`, `path = "/"`. Nothing in `compose.yaml` mentions Softfield (ADR 41). The link's port is read from Docker (the service's published port), so it is written in one place only.
3. **The factory runs main, and only main,** from a checkout of its own, `~/.local/share/softfield/run/<project>`: a detached worktree of the project's main, like Softfield's `live`. Its Compose project name is the project's name, so it never meets a `docker compose up` in a clone or a worktree.
4. **It follows main.** When a merge moves main (and at each pick, for a commit made by hand), the runner moves the checkout; if the app is running, it runs `docker compose up -d --build`. A failed build leaves the old containers running and shows "update failed" with the build's last lines.
   - **Migrations run when the app starts:** the recipe asks each main service to run its own migrations before it serves (for Django, `migrate` then the server, in the service's command), so a plain `docker compose up` migrates too. A failed migration stops the container, which shows as Crashed with its logs.
   - **A copy of the data before each update:** before a rebuild, the runner copies the project's data folder to `~/.local/share/softfield/data/<project>.before-<commit>` and keeps the last 3, so a bad migration on live data can be undone by hand.
5. **Live data and dev data never meet.** The running app gets `APP_DATA=~/.local/share/softfield/data/<project>`, outside every git tree. Agents work in worktrees, where `APP_DATA` is unset, so they only ever see `./.data` or the test fixtures. Moving a project's existing data there is a step of that project's own stack card, as a copy: the old files stay until the owner removes them.
6. ⚑ **The dashboard runs Docker itself for these, and nothing else:** Run (`up -d`), Stop (`stop`), the state (`ps`) and the logs (`logs --tail`). Each is a fixed command in `runner/stacks.py`, on a project taken from the registry, with no text from the request in it, behind the same guard as `/requests` (ADR 18 item 3). Every other write still goes through a request row. Anyone on the home Wi-Fi can start or stop an app, as they can already steer the factory.
7. **Agents never run a stack.** Developer and lead jobs and the gates keep running the tests natively; no job may run `docker compose`. The one exception is f239-01's check that Docker is there (`docker compose version`, `docker info`): if it isn't, the ticket still lands (its tests never need Docker) and its result says so for the owner to fix. A card that wants a stack-based test asks for an ADR of its own.
8. **The Projects page shows each project's app:** its state in words (Running, Starting, Stopped, Crashed, Update failed), Run or Stop, Open (the main service's address, on the host the page was opened from), and Logs. A project without `[run]` gets one button, "Plant a card for a stack", which plants a card on that project pointing at `run-stack.md`. A crashed app or a failed update gets "Plant a card to fix it", which plants a card on that project with the state, the commit and the last 30 log lines in its text, since no job can read the logs itself. Softfield gets neither: it runs from `live`, with its own commands.
9. **Logs:** a page per project with the last 200 lines, refreshed every 5 s while it is open, one service or all. A crashed app (it exited, or Docker restarts it again and again) is a "Needs you" line on the Projects page, cleared when it runs again or is stopped.

## Settled with the owner (2026-11-11)
- Docker Engine and Compose are assumed installed and up to date; if not, the work flags it to the owner (item 7).
- Migrations run with the app's start, with a copy of the data before each update (item 4).
- A failed app offers to plant a card to fix it (item 8).

## Alternatives turned down
- **Run and Stop as requests the runner takes:** no new power for the dashboard, but a press waits for the next pick, up to most of an hour: the owner asked for better.
- **A free port picked at each start:** no clashes to plan, but the address changes each time, bookmarks and the owner's phone break, and a plain `docker compose up` wouldn't match the factory.
- **A label in `compose.yaml` naming the main service:** one file instead of two, but it puts the factory in the project's own files (ADR 41).
- **A named Docker volume for the data:** cleaner Compose, but the data hides in Docker's folder, harder to find, copy or back up than a plain folder.
- **A workspace per ticket with its own stack (as some tools do):** not needed while agents test natively.

## Consequences
- Docker Engine with Compose v2 has to be on the machine, and the dashboard's user able to use it (the `docker` group). Being in that group is as strong as root on this machine; the dashboard already runs as the owner.
- Each product needs a card of its own for its stack (Coucou, Travel Companion, Coaster Ranker); until then its plate shows the plant button.
- A running app uses memory and CPU beside the local model; Stop frees it.

## What doesn't change
- How Softfield runs itself (`live`, `softfield` commands), and the review's pictures (`[shots]`, ADR 40), which still serve a throwaway copy on sample data.
- The gates, the job permissions, and every other dashboard write.
