# F280: The factory's instructions name no project: no Mum, no Coucou paths

The planning thread behind F280's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-20 08:22

> A lot of the factory assume things are for mum but that was a coucou specific. I just made a new project and the review suggestion cards said mum will like that. There's probably an instruction leak

## The lead, 2026-11-20 08:25

> I found the leak and drafted one lead ticket that fixes it and adds a test so it can't come back. Nothing is queued until you approve.
>
> 1. **Where Mum comes from**: The instructions every project's lead reads say Mum twice. In `runner/instructions/lead.md`, the sign-off sheet asks for "what the owner and Mum will notice" (item 1) and "what Mum or the owner would enjoy next" (item 6). The database shows 7 sign-off sheets outside Coucou that picked it up: travel-companion's F1, F2, F5, F8 and F11, coaster-ranker's M1, and today wardrobe-teller's M1 ("does it suit the day for Mum").
>    Action: Ticket f280-01 rewrites both items.
> 2. **The leak is wider than Mum**: Other parts of the instructions also assume Coucou. task-writing.md has a whole JavaScript section about Coucou's folders, its Preact and its French files, plus two lessons about French. task-format.md has example paths in coucou/ and a rule that every ticket with user-facing text lists Coucou's .po files. The review asks the lead to "check the French in coucou/locale/fr/". The lead's findings examples, a gate hint and docs/workflow.md name coucou/ too. The new projects' leads have probably been told to check French they don't have.
>    Action: The same ticket cleans all of them. Old lessons keep their ticket names (m4-06), because those are history, not rules.
> 3. **Who a project is for comes from the project itself**: Each project already has its own `.softfield/project.md` for product taste, and every job there gets it in its system prompt. The sign-off sheet will speak of "the people the project is for", as that file names them, and of you when it names nobody. Setting up a new project will also ask who it's for. Your existing projects (wardrobe-teller, travel-companion, coaster-ranker) don't name anyone yet, so their sheets will speak to you until one line is added there.
>    Action: Ticket. To get it right sooner, plant on each project: "Name who this project is for in .softfield/project.md."
> 4. **A test keeps it out**: The ticket starts with a test that reads every instruction file, the prompts, the gate hints and the workflow doc, and fails on "coucou" or "Mum". The leak happened because Coucou was the factory's first project, and nothing caught it when the factory became shared. Translations stay on Coucou's own folder: that check only runs in a project that turns it on, and only Coucou does.
>    Action: Ticket.
> 5. **Coucou keeps what it learned**: The removed text (the JavaScript rules, the French tone tips, the .po rule) is real Coucou knowledge. A Softfield job can't write into Coucou's repo, so the ticket pastes it word for word into this card's "For Coucou" section. Product work is on hold, so it can wait there.
>    Action: When Coucou starts again, plant on Coucou's Planning page: "Move F280's 'For Coucou' notes from Softfield into this project's .softfield/project.md (Mum, the French check) and .softfield/developer.md (the JavaScript rules)."
> 6. **One line in your own preferences file**: `runner/instructions/author/owner.md` (your preferences) says "the product (coucou/) keeps its calm look". I'd change it to "a project's own app keeps its own look", so a new project isn't told to look like Coucou. It's your file, so say no if you'd rather keep it.
>    Action: In the ticket unless you object.
> 7. **Past sign-offs stay as written**: The 7 sheets that mention Mum are records of what was written. Rewriting them would change the history and fix nothing going forward.
>    Action: Nothing.
>
> Proposals:
> - F280: the factory's instructions name no project (plan)
