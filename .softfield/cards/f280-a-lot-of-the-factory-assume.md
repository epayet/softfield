# Milestone F280: The factory's instructions name no project: no Mum, no Coucou paths

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-20.

## Notes
A lot of the factory assume things are for mum but that was a coucou specific. I just made a new project and the review suggestion cards said mum will like that. There's probably an instruction leak

## What happens today
The leak is in the package's own instructions, which every project's lead job gets in its system prompt:
- `runner/instructions/lead.md`, "Sign-off sheet": item 1 says "what the owner and Mum will notice", item 6 "what Mum or the owner would enjoy next". "Review loop" says "Check the French in `coucou/locale/fr/`".
- `runner/instructions/task-writing.md`: the "JavaScript tasks (ADR 06)" section is Coucou's (its JS folder, its protected modules, Preact, `djangojs.po`), and two lessons are about Coucou's French.
- `runner/instructions/task-format.md`: the example `files:` and a rule that every ticket with user-facing text lists Coucou's `.po` files.
- `runner/prompts.py`: the findings examples name `coucou/x.py`; `runner/gates.py`: the translations hint names Coucou's folder and French.
- `docs/workflow.md`: the layout gate's line names `coucou/`.
- `runner/instructions/author/owner.md` ("Factory theme"): "the product (`coucou/`) keeps its calm look".

Seven sign-off sheets in three other projects carry "Mum" (metrics database, `milestones.signoff`): travel-companion's F1, F2, F5, F8 and F11, coaster-ranker's M1, wardrobe-teller's M1 ("does it suit the day for Mum").

## Decisions
- **D1: the package names no project.** Nothing under `runner/instructions/`, `runner/prompts.py`, `runner/gates.py`'s hints or `docs/workflow.md` names Coucou, its paths, its people or its language. Lessons keep their ticket ids (m4-06), which are history, not instructions.
- **D2: who a project is for lives in its own `.softfield/project.md`.** The sign-off sheet says "the people the project is for (its `.softfield/project.md` names them; the owner when it names nobody)". The setup guide (`runner/instructions/bootstrap.md`, "The project's own rules") adds "who it's for" to what that file holds, so a new project names them from day one.
- **D3: a test keeps it out.** A test in `tests/runner/test_prompts.py` reads every `.md` under `runner/instructions/`, `runner/prompts.py`, `runner/gates.py` and `docs/workflow.md`, and fails on "coucou" or the word "Mum" (any case), naming file and line. `runner/i18n.py` keeps its `coucou/locale` folder: the translations check only runs where `[checks] translations` is on, which is Coucou alone; making it configurable waits for a second project with translations.
- **D4: Coucou's knowledge isn't lost.** What leaves the package is kept word for word below ("For Coucou"), for Coucou's own `.softfield/project.md` and `.softfield/developer.md`: a Softfield job can't write to Coucou's repo (ADR 41 item 7).
- **D5: old sign-offs stay as they are.** They are records of what was written.

## For Coucou
Kept here until Coucou's own card moves it into its repo (D4); the ticket fills it with the exact text it removes.

## Done when
- A new project's sign-off sheet and its "What next" never mention Mum unless its own `.softfield/project.md` does.
- The test of D3 is red on today's main and green after the ticket.
- Coucou's removed instructions are in "For Coucou" above, word for word.
