# Milestone F255: A README that welcomes people who want to use or work on Softfield

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-16.

## Notes
Make a readme up to date and more welcoming to others who want to use it or work on it

## Plan (lead, 2026-11-16)
- **What `README.md` lacks today:** it is written for the owner on this machine. It never says in plain words what Softfield is for or how its parts fit together, what you need (Linux, git, Python 3.13 and uv, Claude Code, optionally OpenCode with a local model), or how anyone else installs it. It leaves out `softfield lead`, `pause`/`resume`, `notify setup` and how to replace the author's opinions (`~/.config/softfield/owner.md`). Its paths (Dropbox) read as requirements, not defaults. `AGENTS.md`, the contributors' entry, numbers its rules from 5.
- **What is still right:** the "Every day" table, the setup steps, "Always on", "Where things live" and "How Softfield updates itself" match the code (checked against `runner/cli.py` and `factory_dashboard/templates/projects.html` on 2026-11-16). They stay, reordered.
- No mock-up: the README is no page the dashboard serves.
- Not a repeat of F204, Publish Softfield as a versioned package, with CI. That card makes Softfield installable from PyPI, and when it lands it changes the README's install line.
- Ticket: `f255-01-a-welcoming-readme` (lead).

## Decisions
- **D1: one README, reordered for a newcomer;** no new CONTRIBUTING.md or docs page. Order: what Softfield is (one paragraph, plain words, with an honest status) → how it works (plant, plan, tickets, developers, runner, sign-off, five lines) → what you need → install → your first project → every day → make it yours → always on → where things live → how it updates itself → working on Softfield (points at `AGENTS.md`) → licence (MIT).
- **D2: an honest status:** one person's factory, used daily on Linux, never installed on another machine yet (F204's open point). Welcoming, without promising more than that.
- **D3: others install from GitHub** with `uv tool install git+https://github.com/epayet/softfield` (ADR 41 item 6), and start the machine file from the example. The `live` checkout that follows main stays the owner's setup, under "How Softfield updates itself". Every fact comes from the code, not from memory. Whatever a fresh machine would still miss (an example `factory.toml` that isn't in the package, say) is written down in the README as a known gap.
- **D4: owner-specific settings read as defaults** (the Dropbox backup, the author's opinions in `runner/instructions/author/`), and the README says how to replace them.
- **D5: a test keeps it true:** `tests/runner/test_cli.py` checks that every `softfield <command>` written in `README.md` is a real subcommand of the CLI, so a renamed or removed command breaks the suite, not the README. It also checks that the everyday commands (`init`, `doctor`, `run`, `dashboard`, `lead`, `pause`, `resume`, `notify`) are in it.
- **D6: `AGENTS.md`'s rules number from 1.**
