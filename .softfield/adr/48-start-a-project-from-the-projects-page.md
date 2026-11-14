# ADR 48: Start a project from the Projects page, set up by a headless lead job

- **Status:** Accepted (by the owner, 2026-11-14)
- **Date:** 2026-11-13
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 30](30-many-projects-one-factory.md) items 7 and 8 (a project is set up in a terminal session), and F236 D1 ("only `softfield create` adds a row") for a project started from the page.
- **Evidence:** F122 (owner, 2026-11-13): "the only thing missing to be able to manage most things from the board itself is being able to start new projects". Run and Stop already work from the page (ADR 46). Today a new project needs a terminal: `softfield init`, a live Claude chat (`runner/instructions/bootstrap.md`), then `softfield doctor`. In November, 36 of 107 planner jobs started within 5 minutes of the owner's message and 38 waited over 2 hours (pauses, the reserve, nights): a chat of one question at a time would take days on the web.

## Decisions (⚑ = deviates from an earlier decision)
1. **The page asks, the runner makes the folder.** "Start a project" sends a `new_project` request (ADR 18: a request row, nothing else). At its next pick the runner makes `<projects root>/<name>`, runs `softfield init` there, saves the owner's words word for word in `.softfield/seed.md`, writes the first card M1 with those words under its Notes, and commits. No Claude is needed for any of it, so the owner's words are on disk before any job runs.
2. **The projects root is one machine setting,** `[projects] root` in `~/.config/softfield/factory.toml`. Without it, the folder every live project already shares (on this machine `~/projects/epayet`), else `~/projects`. No new command: the file is edited by hand, like `[notify]`.
3. ⚑ **The project shows at once, "being set up".** The runner registers it paused `setting up` when it makes the folder, unlike F236's terminal path where only `softfield create` adds a row: here the owner has already given the idea, and the plate is where they follow it.
4. ⚑ **A new job kind, `setup`:** the lead, headless, on Opus, in the claude lane in the planner's place in the order (under the reserve too, like planner jobs, ADR 20 item 2). Its brief is `bootstrap.md` with a section for the page. It runs in the new project's folder **on main** (nothing else touches a project being set up) and may edit any file there and run `uv`, `git` (status, diff, log, add, commit), `softfield check-all`, `softfield doctor` and `ss -ltn`. Never `docker` (ADR 46 item 7), never `softfield accept` or `create`.
5. **One round by design.** The page's form gives what the terminal asks one by one (the idea, a name, what it's built with if the owner has a view, whether it's an app opened in a browser). The setup job does everything in one go, decides what isn't given and says why, and replies on **M1's thread** with ADR 00 in the owner's review format, as an `adr` proposal, plus only the questions it truly can't decide. The owner's message on that thread, while the project is being set up, queues another `setup` job, not a planner.
6. **Approving ADR 00 is the owner's yes** (F236 D4's "Ready to add it?"). It runs `softfield create`'s checks: when they pass, the project goes to the runner, unpaused, and the lead is asked to plan M1 on the same thread, mock-ups included (F72). When they fail, a `setup` job is queued with what failed, twice at most; then the desk says where it stopped.
7. **Docker from day one, when it's an app:** the setup follows `runner/instructions/run-stack.md` (`compose.yaml`, the port, `[run]`) and the skeleton serves one page, so the plate shows Run as soon as the project is in. No job can run Docker, so the stack is first proven when the owner presses Run; a crash offers "Plant a card to fix it" (ADR 46 item 8). The terminal setup gets the same step.

## Alternatives turned down
- **The dashboard makes the folder itself, at once:** saves one wait of minutes, but gives the dashboard write access to the home folder, a bigger exception to ADR 18 than Docker's four fixed commands; and the Claude part waits for the runner anyway.
- **The setup as a live chat on the thread, one question at a time, as in the terminal:** each answer waits for the claude lane; see the evidence.
- **A setup card of its own (M0):** a second thread to follow, and a card to archive. M1's thread runs from the idea to its first plan.
- **A `softfield config` command for the root:** a command for one key, which the file already holds.

## Consequences
- A web-started project exists in the registry before ADR 00 is accepted; the runner gives it only `setup` jobs until it passes.
- The live chat stays in the terminal (`softfield init`), for an existing folder or a long talk.
- Until F121 lands, the setup recommends Python with uv, as `bootstrap.md` does.

## What doesn't change
- The terminal path (`softfield init`, `softfield create`, F236), ADR 00's review format, the checks a project must pass, ADR 46's stacks and who may run Docker.
