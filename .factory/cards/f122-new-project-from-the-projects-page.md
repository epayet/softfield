# Milestone F122: New project from the Projects page

> **State:** idea · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-14.

## Notes
From the terminal session of 2026-10-14 that built ADR 30 (sessions B, C, D).

ADR 30 left this for later: start a project from the phone instead of a terminal.

On the Projects page: a big text box for the idea, a name, and a send. It's a request (the
dashboard never touches folders, ADR 18), shown at once as "New project on its way"; the runner,
which runs on this machine, carries out what `softfield init` does under `~/projects/<name>`
(runner/setup.py `init`), registers it paused ("setting up"), and the setup conversation that
the terminal Claude session does today (docs/bootstrap.md: the idea saved word for word in
seed.md, the stack, ADR 00 reviewed in the owner's format, the checks, the first card) happens
on that project's Planning desk instead. When `doctor` passes, the project goes to the runner.

Open questions: where the folder goes (a fixed root in the machine's factory.toml?), how Claude
gets trust for a new folder headless (`--add-dir`, `dontAsk`), and how ADR 00 is accepted from
the web (today a card's Accept needs a planner proposal).
