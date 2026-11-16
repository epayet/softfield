---
id: f255-01-a-welcoming-readme
milestone: f255-make-a-readme-up-to-date
agent: lead
difficulty: 4
depends_on: []
files:
  - README.md
  - AGENTS.md
  - tests/runner/test_cli.py
tests:
  - tests/runner/test_cli.py
---

### Goal
Rewrite `README.md` so that someone who has never heard of Softfield can tell what it is, install it and set up a first project, and someone who wants to work on it knows where to start. Keep everything that is still true for the owner.

### Context
Read "Plan" and D1 to D6 in `.softfield/cards/f255-make-a-readme-up-to-date.md`. D1 gives the README's outline, in order.
- Today's README: `README.md`. The commands and their help: `main` in `runner/cli.py`. The default paths: `runner/config.py`. The example machine file: `tests/fixtures/softfield-machine.toml`. The packaged files: `pyproject.toml`.
- What Softfield is, in its own words: `docs/how-it-works.md`, `.softfield/adr/30-many-projects-one-factory.md`, `.softfield/adr/41-the-factory-is-optional.md` (item 6 for installing from GitHub). Notifications: `docs/notifications-on-the-phone.md`.
- Contributors: `AGENTS.md` (its rules start at 5).
- Check every claim against the code. Where a fresh machine would get stuck (a file the package doesn't ship, a step only the owner's machine has), say so in the README as a known gap. Never write around it.
- Plain words, short sentences, no internal ticket or card numbers in the README. ADR links are fine where they explain a "why". No personal details beyond what `LICENSE` already names.

### Done when
- `README.md` follows D1's outline. A newcomer finds what Softfield is, an honest status (D2), what to install first, the install from GitHub (D3) and a first project (`init`, `doctor`) before the owner's daily table
- the daily table also covers `softfield lead`, `pause`/`resume` and `notify setup`; machine paths read as defaults that can be changed (D4), and "Make it yours" says how to replace the author's opinions with `~/.config/softfield/owner.md`
- "Working on Softfield" points at `AGENTS.md`, `softfield check-all` and the worktree tip, and the README ends with the MIT licence
- `AGENTS.md`'s rules are numbered 1 to 8, with the same text otherwise (D6)
- a test in `tests/runner/test_cli.py` reads `README.md`, finds every `softfield <word>` written in backticks or a code block, and checks each is a subcommand of the CLI (`main([word, "--help"])` exits 0). A made-up command in the README fails it (D5). The same test checks that the README names the everyday commands `init`, `doctor`, `run`, `dashboard`, `lead`, `pause`, `resume` and `notify`, so it fails on today's README, which leaves out `pause`, `resume` and `notify`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
