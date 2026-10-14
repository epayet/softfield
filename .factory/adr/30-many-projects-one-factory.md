# ADR 30: Many projects, one factory (Softfield)

- **Status:** Accepted (by the owner, 2026-10-14)
- **Date:** 2026-10-14
- **Deciders:** project owner (accepts), Claude (drafts)
- **Supersedes:** [ADR 02](02-software-factory.md) §4.2 and §4.3 (one extracted package, a per-project `factory.toml`); the rest of ADR 02 stays a draft.
- **Amends:** [ADR 19](19-feature-board.md) 2b (a card's area becomes its project); [ADR 13](13-factory-dashboard.md) item 1 (one metrics DB for every project, now used that way); `.factory/protected-paths.txt` and every fixed path in `runner/` (they move under `.factory/`).
- **Evidence:** the owner's terminal session of 2026-10-14. Of 69 ready tickets, all are factory tickets; product work has been on hold since 2026-10-04, yet the factory still lives inside Coucou's repo, is named after it (`_repo()` exits with "run this inside the coucou repository"), and runs from the checkout its jobs switch branches in.

## Context
- **The owner wants to run several projects with one factory:** Coucou, the factory itself (named **Softfield**), and new ones, started from scratch or adopted from an existing repo. Once the board can be edited (F15), they want to plan, steer and sign off any of them from the dashboard alone.
- **The data is ready, the code is not.** The metrics DB already has `projects` and a `project_id` on most tables, and every dashboard page takes `?project=`. But the runner works on the one repo it is started in, takes its name from the folder, and hard-codes Coucou's commands and paths (`runner/checks.py`, `runner/gates.py`, `runner/i18n.py`, `runner/prompts.py`, `.factory/tasks/`, `.factory/cards/` and others).
- **The factory runs from its own work tree.** When a job checks out `task/<id>` on a factory ticket, the running runner and dashboard read files from that branch; `_runner_code` restarts the runner when `runner/` changes under it.

## Decisions (⚑ = deviates from an earlier decision)
1. ⚑ **Two repos.** `~/projects/epayet/softfield` holds the factory: `runner/`, `factory_dashboard/`, their tests, the factory ADRs, the generic workflow docs and the factory's cards and tickets. Coucou keeps the product. The split keeps history (`git filter-repo`). The Python packages keep their names (`runner`, `factory_dashboard`), so the ready tickets stay valid; only the command is new (item 5).
2. ⚑ **One layout in every project: `.factory/`.** Not configurable.
   ```
   .factory/
     project.toml          name, description, main branch, check commands, test dirs,
                           dependency files and dirs, layout pairs
     project.md            the rules that hold for this repo only
     protected-paths.txt
     seed.md               the owner's first idea, word for word
     adr/  cards/  .factory/tasks/{ready,later,done,blocked,escalated}/
     planning/  reviews/  sessions/
     var/                  not in git: runs/, state.json
   AGENTS.md, CLAUDE.md    short pointers (item 4)
   ```
   Coucou's `.factory/tasks/`, `.factory/cards/`, `.factory/adr/`, `.factory/planning/`, `.factory/reviews/`, `.factory/sessions/` and `.factory/` move there; `docs/original-brief.md` becomes its `seed.md`.
3. ⚑ **Machine settings and project settings split.** `~/.config/softfield/factory.toml` holds what belongs to the machine: agents, roles, Claude's reserves, the local model, the metrics DB and its backup. `.factory/project.toml` holds the project's own settings. The runner's checks and gates run the project's commands; Coucou's translations check becomes one of Coucou's commands.
4. **Rules are global unless a repo needs its own.** The generic docs (`lead.md`, `task-writing.md`, `task-format.md`, `workflow.md`, AGENTS.md's general rules) live in Softfield; the owner's workflow preferences move to `~/.config/softfield/owner.md`. A project's `AGENTS.md` and `CLAUDE.md` only point at them, plus `.factory/project.md` for what holds in that repo alone (for Coucou: French, Mum, Preact, no CDNs, never logging a note, the worked developer examples). Per-project overrides of a global rule wait for a real need. No project template: the lead sets each project up from its ADR 00 (item 7).
5. ⚑ **Softfield runs from its latest main, not from a work tree.** `~/.local/share/softfield/live` is a worktree of Softfield's `main`, installed once with `uv tool install -e`. After a merge into Softfield's main, the runner fast-forwards `live` and starts itself again; the dashboard reloads. Jobs never work in `live`. This replaces `_runner_code`. One command drives it all: `softfield run`, `softfield dashboard [--lan]`, `softfield status`, `softfield accept N`, `softfield doctor`, `softfield init`, and `softfield service install` to start the runner and the dashboard with the machine.
6. ⚑ **One runner for every project, by the owner's order.** Projects get a `priority` and a `paused` switch. At each pick:
   1. the owner's requests and planner jobs, from any project;
   2. then the highest project with a ticket it can run; when it has none, the next one (strict order, falling through).

   Claude's allowance, the agents and the global pause stay the machine's. A project's run state lives in its `.factory/var/`. A **Projects** page on the dashboard ranks them by drag and one send (F15's reorder, with a project), shows what runs now across all of them, and sums "Needs you"; each project keeps its own planning desk and board.
7. **`softfield init` sets up the folder it is run in,** new or existing.
   - **The command:** `git init` when needed; the `.factory/` skeleton with the default protected paths (item 8); the pointer files; `.gitignore` lines; the project registered in the DB. Then it opens an interactive Claude session in that folder with the setup prompt. Trusting the folder happens there, in the terminal, not from the web.
   - **A new project:** Claude asks for the idea (saved word for word in `seed.md`), the technologies and the constraints, drafts **ADR 00 "Initial decisions"**, and sets up the stack and its checks.
   - **An existing project:** Claude looks through the repo (stack, layout, tests, linters, the sensitive code), drafts **ADR 00 "How things are"**, and fills in the checks until they pass on `main`.
   - **Either way:** it writes `project.md` and the protected paths, plants the first card with ADR 00 attached, and stops when `softfield doctor` passes.
8. **`softfield doctor` says when the web can take over.** It passes when: `project.toml` is valid and its checks pass on a clean `main`; `protected-paths.txt` exists; a new project has its `seed.md`; `.factory/adr/00-*.md` is Proposed; the project is registered; the first card is planted with ADR 00 attached (accepted from its thread, `accept_adr`); everything is committed. Then it prints the project's dashboard link.
9. **Protected paths.** Every project starts with Softfield's defaults: `.factory/**`, `AGENTS.md`, `CLAUDE.md`, dependency manifests and lockfiles, CI config, migrations. At setup the lead adds the repo's sensitive code (security, privacy, data loss, deploy, settings), each with a one-line reason in ADR 00. Later the lead adds a path when new code falls in the owner's critical list and says so in the review report; removing a path needs the owner.
10. **Coucou afterwards** is a project like any other: the product, its ADRs (00, 03–06, 08–11), cards m0–m4, its reviews and checks, ranked below Softfield with an empty queue until the owner plants something. Softfield's own ADRs keep their numbers.

## Order of work
Done by the lead in terminal sessions, not as tickets, because it changes how the runner itself works. The runner stays off from B until C is verified.
- **A.** This ADR. f19-02 is parked on its branch; it and the rest of F15 and F19 resume afterwards, in Softfield.
- **B.** The runner reads `.factory/` and the split config, still in this repo. Check: the dry-run queue is the same before and after, check-all passes, one real ticket merges.
- **C.** The split, `live`, the `softfield` command, and the DB moving the factory's rows to the project `softfield` (backed up first; both repos tagged before). The factory's files leave Coucou in an ordinary commit. Check: both suites pass, the dashboard shows two projects, a Softfield merge updates `live`.
- **D.** One runner for many projects, `softfield init` and `softfield doctor`. Check: init on an empty folder and on a small existing repo; both reach the dashboard; the order falls through.
- **Then, as tickets:** the Projects page (mock-up first), and later "New project" from the web, which the runner would carry out under `~/projects`.

## Settled with the owner (2026-10-14, terminal session)
- One fixed `.factory/` layout, with Coucou moved into it.
- Global rules, a short `project.md` per repo, no project template.
- Strict priority, falling through.
- `init` takes no path, keeps the seed, and ends at `softfield doctor`.
- The work happens in terminal sessions now; the unfinished board doesn't block it.
- **Coucou's history is kept:** the factory's files leave Coucou in an ordinary commit, with no history rewrite.
- **Backups:** neither repo has a remote. A full copy of the repo and a consistent copy of the metrics DB are in `~/backups/` (`coucou-before-split-2026-10-14/` and `factory-metrics-before-split-2026-10-14.sqlite`), taken before session B. The owner adds a git remote to each repo once the split is done.

## Alternatives turned down
- **Split first, make the runner generic after:** both projects would break at once. Making it generic inside one repo first lets the dry run compare before and after.
- **Configurable paths, keeping Coucou's `docs/` layout:** every path becomes a setting, for one project's sake.
- **Copying the rules into each project:** copies drift; a lesson learned in one project wouldn't reach the others.
- **Shares between projects** (say 70/30): the owner wants the top project's work first.
- **Setting up projects from the web first:** the web would create folders in the owner's home and need Claude trusted there; the terminal does both naturally.
- **A desktop client:** a new app to build and maintain, for what the command and the phone dashboard already cover.

## Consequences
- Two repos to keep; Softfield is installed once and every project uses the same one.
- Almost every path in the runner changes once (session B): the biggest risk of this ADR, handled by the dry-run comparison and the runner being off.
- A Softfield merge restarts the runner; a broken merge can still stop it, but a broken branch can't.
- Tickets, cards and reports of the factory leave Coucou's history going forward (they stay in its past history).

## What doesn't change
- The ticket and card formats, the gates, the agents and their ratings, the planning room and the board.
- One metrics DB for every project, backed up daily.
- Nothing merges or queues without the owner.
