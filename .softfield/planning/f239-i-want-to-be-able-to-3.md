# F239: Run, stop and open each product's app from the Projects page, on Docker Compose

The planning thread behind F239's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-11 02:09

> Plan this card.

## The lead, 2026-11-11 06:43

> I've drafted ADR 46, the card's plan with seven tickets and a mock-up of the Projects page, all on `plan/f239`. The tickets pass pre-flight except for one thing: they need ADR 46 to be Accepted first. I couldn't open the product repos from here, so nothing assumes how their current live folders work.
>
> 1. **Is Docker on this machine?**: This needs Docker Engine with Compose v2 installed, and your user in the docker group, because the dashboard runs as you. I can't check that from here, and I don't install system packages without asking. One thing to know: being in the docker group gives as much power as root on this machine.
>    Action: Tell me whether it's installed. If it isn't, install it yourself (Docker's apt repository: docker-ce and docker-compose-plugin), or say so and the first ticket will check for it and explain what's missing.
> 2. **Run and Stop act at once, without waiting for the runner**: This is easy to build, but it needs a rule change. Today the dashboard's only write is a request row (ADR 18 item 2), and the runner takes requests at its next pick, which can be most of an hour away. I recommend the dashboard runs Docker itself for four fixed things only: run, stop, read the state, read the logs. The project name comes from the registry, nothing you type ever reaches a command, and the same-origin guard as Plant applies. The cost: anyone on your home Wi-Fi can start or stop an app, just as they can already steer the factory.
>    Action: ADR 46 item 6.
> 3. **Always the latest main**: Each product gets a checkout of main just for running, in ~/.local/share/softfield/run/<project>, the same way Softfield's live folder works. After each merge (and at each pick, to catch a commit made by hand), the runner moves that checkout. If the app is running, it rebuilds it with `docker compose up -d --build`. If the build fails, the old app keeps running and the page says 'Update failed' with the build's last lines. A bug that builds fine still reaches the running app: that is what following main means.
>    Action: ADR 46 items 3–4; ticket f239-02.
> 4. **Ports: one fixed port per project rather than smart forwarding**: I recommend each project's compose.yaml publishes its main service on `${APP_PORT:-81NN}`, with a port picked once from 8100–8199 when its stack is set up. A port that changes on every start would break your bookmarks and your phone's links, and a plain `docker compose up` would then differ from what the factory runs. If the port is already in use, Run says so and names it.
>    Action: ADR 46 item 1; the recipe in runner/instructions/run-stack.md (f239-03).
> 5. **Which container is the main one**: A `[run]` table in .softfield/project.toml names it (`service = "web"`, plus `path` if the app doesn't open on `/`), next to `[shots]`. A label inside compose.yaml would put the factory into the project's own files, which ADR 41 rules out. The Open link's port is read from Docker, so it's written in one place only.
>    Action: ADR 46 item 2; ticket f239-01.
> 6. **Live data and dev data never meet**: The running app keeps its SQLite files and uploads in ~/.local/share/softfield/data/<project>, which is outside every git tree. The factory passes that folder as APP_DATA. Agents work in worktrees, where APP_DATA isn't set, so a stray command there only ever touches ./.data or the test fixtures. The products already have live data (Coucou's photos, your trips in Stampu). Each product's own stack card moves it as a copy, and the old files stay until you delete them.
>    Action: ADR 46 item 5; a required step in each product's stack card.
> 7. **Developers on tickets with different stacks**: Simplest answer: agents never run Docker. Tests and gates keep running natively, as they do today, and docker is in no job's commands, so their stacks can't clash with the running app. I've left out a workspace per ticket, like Conductor's, as you suggested.
>    Action: ADR 46 item 7.
> 8. **What the Projects page shows**: Under each product's facts there's an App row: its state in words (Running, Starting, Stopped, Crashed, Update failed), then Run or Stop, Open (on the address your phone used to reach the page) and Logs. Red appears only for a crash or a failed update, always next to the word. A product without a stack gets one button, 'Plant a card for a stack', which plants a card on that project pointing at the recipe. Softfield gets no App row.
>    Action: Mock-up .softfield/cards/f239-mockup/projects-run.html; tickets f239-05 and f239-07.
> 9. **Logs, and seeing that something is wrong**: Each project's app gets a logs page at /projects/<name>/logs. It shows the last 200 lines, refreshes every 5 s while open, can pause, and filters to one service. A crashed app or a failed update also appears in Needs you on the Projects page, and the line goes as soon as the app runs again or you stop it.
>    Action: Tickets f239-06 and f239-07.
> 10. **The plan: 3 lead tickets, a replan, 3 developer tickets**: Lead: f239-01 the [run] table and runner/stacks.py, the one module that runs Docker. f239-02 the runner follows main. f239-03 the Run and Stop routes plus the recipe run-stack.md. Then f239-04, the replan our rules require after a chain of lead tickets. Developers: f239-05 the App row, f239-06 the logs page, f239-07 Needs you. That's about 4 hours of work. Nothing is queued until ADR 46 is Accepted. The card goes where you drag it on the board.
>    Action: Approve the plan once ADR 46 is accepted.
> 11. **The first product to get a stack**: No product has a stack yet, so the buttons only become real after a product's own card. I recommend Coaster Ranker first: it's the smallest and holds no private data, so it's a safe test before Coucou's always-on screen and Stampu's trips. That card is also your real-device check for this milestone.
>    Action: After sign-off, press 'Plant a card for a stack' on Coaster Ranker's row. Or tell me another product to start with.
> 12. **Sign-off pictures won't show a running app**: The review takes pictures of /projects on a copy of the dashboard, where no stack runs. They'll show the plant buttons and Softfield's plate, not a running app. The Running and Crashed rows are only checked by you, on the real page, after point 11.
>    Action: None: the list under Before and after is just /projects.
> 13. **Related: F213, When live can't follow main, say so and why**: F213 is close but not a repeat. It covers Softfield's own live folder. This card reports a failed update for the products' apps (f239-02), and F213 stays as it is.
>    Action: Nothing.
>
> Proposals:
> - ADR 46: Run a project's app from the Projects page, on a Docker Compose stack that follows main (adr)
> - F239: Run each product's app from the Projects page (plan)
> - The Projects page with each product's App row, and the logs page (mockup)

## The owner, 2026-11-11 17:29

> On point 1: Assume it's present to latest update. If it's not, flag it to me when doing the work for me to fix
> On point 3: Will the build handle migrations if relevant to the app?
> On point 8: If it fails, there could be an option to plant a card to look into fixing as well

## The lead, 2026-11-11 18:41

> I've folded your three answers into ADR 46, the plan, the tickets and the mock-up. The tickets pass pre-flight except for one remaining refusal: they wait for ADR 46 to be accepted.
>
> 1. **Docker: assumed installed, and flagged if it isn't**: Agreed. The first ticket (f239-01) checks once that Docker and Compose work on this machine. If they don't, it still lands, because its tests never need Docker, and it ends by saying what's missing. The review then puts that in front of you. This needs one small exception to 'agents never run Docker': that ticket may run the two read-only checks, `docker compose version` and `docker info`, and nothing else. No job may ever start a stack.
>    Action: ADR 46 item 7 and its 'Settled with the owner' section; D9; ticket f239-01 (`commands:`).
> 2. **Migrations during an update**: Not by the build itself: building only makes the image. The migrations have to run when the app starts. The recipe asks each project's main service to migrate before it serves (for a Django app, `migrate` then the server, in the service's command). So every update, and a plain `docker compose up` by hand, migrates. A migration that fails stops the container, and the page shows Crashed with the logs. The risk is a migration that runs fine but damages live data. So before each update the runner copies the data folder, keeps the last 3 copies, and skips the update if the copy fails. With SQLite files that copy takes seconds, and it is how you get back after a bad migration.
>    Action: ADR 46 item 4; D8; tickets f239-02 (the copy) and f239-03 (the recipe).
> 3. **A failed app offers to plant a card to fix it**: Yes. A Crashed or Update failed row gets 'Plant a card to fix it', and so does its line in Needs you. The planted card's text carries the project, the commit, the error and the last 30 log lines, because no planner or developer job can read Docker's logs itself. Without them the card would start blind.
>    Action: ADR 46 item 8; D7; tickets f239-05 and f239-07; mock-up updated.
> 4. **What's left before anything is queued**: The tickets pass pre-flight except that they wait for ADR 46. Accept it from its page, then approve the plan.
>    Action: Accept ADR 46, then approve the plan.
>
> Proposals:
> - ADR 46: Run a project's app from the Projects page, on a Docker Compose stack that follows main (adr)
> - F239: Run each product's app from the Projects page (plan)
> - The Projects page with each product's App row, and the logs page (mockup)
