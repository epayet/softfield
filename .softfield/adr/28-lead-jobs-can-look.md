# ADR 28: Planning and review jobs can look at the database and the dashboard

- **Status:** Accepted (by the owner, 2026-10-10)
- **Date:** 2026-10-10
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** the tool list of planner and review jobs (`run_planner` in `runner/loop.py`, the review in `runner/milestone.py`): one more command prefix. Nothing in [ADR 20](20-planning-room.md) changes.
- **Evidence:** F95 (2026-10-10): the owner asked why the Overview showed two sign-offs and the desk one; the planner found the cause in the code but couldn't name the stale one. F26's review took its times from commits ("I couldn't read the metrics database from this job"). F94's mock-up used example rows for the same reason.

## Context
- A headless job gets a short tool list: read, search and list files, its edit globs, and a few command prefixes (`git diff`, `git log`, `git show`). Anything else is refused.
- The metrics database is one binary SQLite file, so a job can't read it, and what the owner sees (the desk, Needs you) is worked out by the dashboard's code each time, stored nowhere.
- The owner wants answers "from the code and the queue, not the plan alone" (owner.md, 2026-10-07). A planner job can only do the first half.

## Decisions (⚑ = deviates from an earlier decision)
1. **One new read-only command, `uv run runner look`,** with two forms:
   - `look sql "<one SELECT>"` prints the rows. The database is opened read-only, and SQLite itself is told to allow reads only: a write, an `ATTACH` or a `PRAGMA` that changes anything is refused. Rows and long cells are capped, and the output says when it cut.
   - `look page <address>` prints a dashboard page as plain text (`/`, `/planning`, `/milestones/f95`), or its data as is when the address serves data (the floor's). It asks the dashboard's own code for the page, in the same process, and only ever opens a page: no form is sent, so nothing can be approved or signed off.
2. **No list to keep.** Any page the dashboard has, now or later, can be looked at; nothing is added when a feature is.
3. **It writes nothing.** Unlike the other runner commands, it doesn't apply the owner's requests or sync the cards first.
4. **Who may call it:** planner jobs and review jobs. Not developers' jobs, checkpoints or escalations.
5. **On demand.** Nothing is added to a prompt but one line saying the command exists; a job pays for a look only when it takes one.

## Alternatives turned down
- **The stock `sqlite3` program:** its side commands run a shell and write files even in read-only mode, and the permission rule only checks how a command starts.
- **A copy of the database per job:** read-only already protects the live file; a copy adds a file of the owner's threads to make and clean up.
- **The facts pasted into every prompt:** paid on every reply, needed or not.
- **A browser for the job (a browser MCP):** it would also show how a page looks, but a browser can press buttons (Sign off, Approve), it ties the workflow to one frontier's tooling ([ADR 02](02-software-factory.md) wants it pluggable), and it is far more to set up for headless jobs. See "Later".

## Consequences
- Planner and review jobs can read everything in the metrics database, the owner's planning threads and ratings included. They can't change it. What a job reads goes to Claude like the rest of its work, as the owner's messages on its thread already do.
- A planner can say what is on the owner's desk right now, and a review can take its times and counts from the database.
- A job still can't see how a page looks: an overlap, a colour, a layout on the phone.

## Later
- **Screenshots:** `look page <address> --shot phone` would save a picture of the page (the browser tests already drive a real browser) for the job to read, with no way to click. Wait for a first question about looks that the text can't answer.
