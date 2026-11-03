# F139: Projects keep Softfield's files in .softfield, not .factory

The planning thread behind F139's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-24 00:32

> Plan this card.

## The lead, 2026-10-27 09:06

> I've drafted the plan for F139: the runner moves each project's `.factory` folder to `.softfield` itself, checks the result before committing, and does Softfield first so it restarts on the new code before moving the other projects.
>
> 1. **Worth doing, and best done now**: Calling the folder after the tool makes sense, the way `.github` is named after GitHub. The cost is about two lead tickets. The real risk is to the runner itself, which reads this folder for every ticket, card and log. The folder name appears 1,326 times in 94 files outside it (runner, dashboard, prompts, docs, tests). It is also in 73 ready tickets, 544 job log paths in the database and 25 open branches. Three live projects have the folder today, so it only gets more expensive with every new project.
>    Action: Plan it now. The card's place on the board decides when it runs.
> 2. **The runner does the move, not a ticket**: Editing 1,300 lines by hand in a lead ticket would cost a lot and miss some. Worse: a branch that renamed the folder would be merged by the old runner, which then files the finished ticket into `.factory/tasks/done/` on a main that no longer has that folder. So one ticket builds the move and a second has the runner run it on this machine. The move renames the folder (logs included) and rewrites every tracked mention, ADRs, cards and tickets included. Names like `.card.factory` and `.factory-status` stay as they are.
>    Action: Tickets f139-01-move-home and f139-02-runner-moves-projects (both lead: they change `runner/`).
> 3. **Main is never left half moved**: Before it commits, the move runs every check on the moved project. If one fails, it puts everything back (folder, files, hook path) and the desk tells you which check failed. A project in a half state (both folders exist) is refused and shown on the desk too.
>    Action: Part of f139-01.
> 4. **Open plans and blocked work move too**: The 25 open plan and task branches (F172's plan, F132's blocked ticket, …) each get the same move as one commit, so approving a plan or landing a blocked branch afterwards works as it does today. The `superseded/*` branches stay as they are: they are the archive.
>    Action: Part of f139-01.
> 5. **The database follows, your words don't change**: These database paths are updated: job log paths, the file paths in proposals still waiting on a thread, ticket files and open desk items. Messages on planning threads, yours and mine, are never rewritten.
>    Action: Part of f139-01.
> 6. **Order: Softfield first, then a restart, then the others**: Moving Softfield rewrites the runner's own code. So the runner moves Softfield alone, restarts on the moved code (as after any runner change), and only then moves coucou and travel-companion, each before it is opened. The four forgotten test projects move if they ever come back. You have nothing to do: the next start after F139 lands does it all, in a few minutes.
>    Action: Ticket f139-02.
> 7. **Should anything else lose the word "factory"?**: The folder is the tool's, but the factory is the idea, so I'd keep `factory_dashboard/`, the machine's `~/.config/softfield/factory.toml`, the `factory` area and the page styles. You asked only about the folder. Alternatives: also rename the machine file to `softfield.toml` (a small ticket), or rename the dashboard package too (large, and nothing you see changes).
>    Action: My recommendation: keep them. Nothing to draft unless you choose otherwise.
> 8. **No ADR, no mock-up**: AGENTS.md, the protected paths and the agents' docs change only the folder's name, not a rule, so approving this plan covers it. On screen, only two labels change: the "Set aside" plate on a ticket's page and the proposal's file list. That is wording, so there is no mock-up.
>    Action: Nothing.
>
> Proposals:
> - F139: projects keep Softfield's files in .softfield (plan)
