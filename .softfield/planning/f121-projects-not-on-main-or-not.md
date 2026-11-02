# F121: Projects on any main branch, in any language

The planning thread behind F121's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-24 00:32

> Plan this card.

## The lead, 2026-10-27 04:16

> I've planned the card as five lead tickets, saved as drafts. One question needs your answer first: whether to build this now at all, since none of your projects needs it yet.
>
> 1. **Nothing needs this today: when should it run?**: I checked all three projects (Softfield, Coucou and travel-companion). All are Python with uv, on `main`. The only one that hit the limit was fact-printer, a trial copy. Building this means five lead tickets in the runner's protected code, about half an hour each, all of it Opus or Sonnet. It also touches the gates every ticket passes through, so a slip here holds up the whole line for no gain today. Each ticket checks that the defaults run today's exact commands, which keeps that risk small. My recommendation: approve the plan, and leave F121, Projects not on main or not in Python, where it is on the board (last, priority 100). It then runs only after the 59 ready tickets, unless you drag it up when a real project needs it. Other choices: (b) keep the tickets set aside until you plant a project that isn't in Python; (c) build only the main-branch ticket now.
>    Action: Your choice: (a) recommended, (b) or (c).
> 2. **No new ADR needed**: ADR 30 already decided this. Its item 1 puts 'main branch, check commands' in `project.toml`, and its item 3 says the checks and gates run the project's own commands. This card finishes what that ADR left hard-coded, and no gate changes its rule.
>    Action: Nothing.
> 3. **Your 'any non-zero exit means the tests failed': I'd narrow it**: Under that rule, a broken test config or a missing file would count as 'your tests fail without the change' and let weak work through. Instead, each project lists the exit codes that mean 'the tests failed': 1 and 2 for pytest, as today, and just 1 for vitest.
>    Action: Decision D4, built in ticket f121-03.
> 4. **Two gaps your notes didn't list**: First, the 'tests fail on main' gate only counts files named `tests/test_*.py` as tests. On a JavaScript project it would quietly pass every ticket with 'no test files changed'. Second, Claude's headless jobs may only run `uv run pytest`, `uv run ruff` and `uv run mypy`, and their prompts tell them to run pytest. Both are covered: the first by a `test_files` setting (f121-03), the second by f121-04.
>    Action: Tickets f121-03 and f121-04.
> 5. **Some rules stay Python-only on purpose**: These stay as they are: the 'one test file per module' layout rule, the browser-test pattern gate, the end-to-end run and the French translations check. Each only applies when a project turns it on or has the folder, so a JavaScript project simply skips them. Each gets a setting when a real project needs one, not before.
>    Action: Nothing now (D5).
> 6. **'ruff' becomes 'lint' everywhere**: A gate named 'ruff' would be the wrong word on a JavaScript project. So the check and the gate become 'lint', and the factory drawing's label 'ruff · mypy' becomes 'lint · mypy'. Old runs in the history keep the name 'ruff'.
>    Action: Ticket f121-02 (D3).
> 7. **The proof: a test project now, a real JavaScript project at sign-off**: f121-05 builds a small project on `master` in a temporary folder, with shell commands for its checks. It shows that `init`, `doctor` and the gates pass good work and stop bad work, and it doesn't need Node on the M4. At sign-off, a small real JavaScript repo set up with `softfield init` is the check you asked for.
>    Action: Ticket f121-05, plus the sign-off check.
> 8. **No mock-up**: Nothing on screen changes apart from one label in the factory drawing, which is a wording change only.
>    Action: Nothing.
>
> Proposals:
> - F121, Projects not on main or not in Python: the plan and five lead tickets (plan)

## The owner, 2026-10-27 08:07

> On point 1: I have some javascript project coming up, happy for this to be at the back of th equeue for now
> On point 5: would languages preference be better managed in tehir own files? python.md

## The lead, 2026-10-27 18:52

> I agree with a shared guide per language, with one limit: the check commands stay in each project's `project.toml`. I added a sixth ticket for the Python guide, and the card stays at the back of the queue as you asked.
>
> 1. **F121 stays at the back of the queue**: Agreed. Approving queues the six tickets, but F121, Projects not on main or not in Python, keeps its last place on the board, so it runs after everything else. When your JavaScript project is closer, drag the card up and its tickets move with it. Setting up that project with `softfield init` is the real check at sign-off.
>    Action: Recorded in the card's plan.
> 2. **A shared guide per language: yes, for the writing rules**: Today each project's own rules file repeats its language rules: travel-companion's says 'Python 3.13, strict mypy…', and Softfield's AGENTS.md has its own Python lines. One shared `docs/agents/stacks/python.md`, shaped like the existing `docs/agents/preact.md`, says once how to write and test Python. A project lists its languages in `[project] stacks` (Python when it says nothing), and its developers and lead read those guides. Each guide ends with the `[checks]` lines a new project in that language starts from, and the setup session copies them.
>    Action: New ticket f121-06 (decision D7).
> 3. **But the commands stay in project.toml**: The runner should read its commands from one data file, not from a page of prose. Two JavaScript projects can also differ: one runs jest, another vitest. So the guide gives the starting lines, and `project.toml` holds what this project actually runs.
>    Action: Part of D7.
> 4. **Risk: the local developer can't read files outside the project**: The local developer runs with outside folders blocked, so it may not be able to load a guide kept in Softfield. f121-06 first tests whether opencode loads it anyway. If it doesn't, `init` copies the guide into the project. A copy can fall behind when Softfield's guide changes, so the ticket records which way it went, and the review will tell you.
>    Action: Handled in f121-06.
> 5. **javascript.md is written with your JavaScript project**: If I wrote it now there would be no project to check it against. The lead writes it in that project's setup session, from what the project actually uses, the same way the first ticket of any new kind is done.
>    Action: Nothing now. It happens at that project's setup.
>
> Proposals:
> - F121, Projects not on main or not in Python: the plan and six lead tickets (plan)
