# Softfield

A software factory for the projects on this machine. A frontier lead (Claude) plans with the
owner and writes tickets; local and cloud developers build them; one runner gates, merges and
reports, for every project in the owner's order; a dashboard shows it all, on a phone too.
Why it looks like this: [ADR 30](.factory/adr/30-many-projects-one-factory.md).

## Every day

| To | Do |
|---|---|
| See where things are | `softfield` alone: whether a runner runs, the projects in order, the commands |
| Run the factory | `softfield run`, from any folder: every project, in the order of the Projects page |
| Run one project only | `softfield run --here`, in its folder |
| See what would run next | `softfield run --dry-run` |
| Stop it | **Ctrl-C**. Idle, it writes each project's report; mid-job, it stops at once and the next start recovers the job |
| Stop it gently | **Pause after this job** on the dashboard, then **Resume** |
| Open the dashboard | `softfield dashboard --lan`, then the address it prints, on the phone too (it opens on `/projects`) |
| Remove a project | `softfield forget <name>`: off the Projects page and the runner's list; its folder stays |
| Put a project first | The Projects page: change the numbers, **Send new order**; the runner takes it at its next pick |
| Plan, steer, sign off | Each project's Planning desk and Board, from the Projects page |

## A new project, or an existing one

In the project's folder (an empty one for a new project):

```sh
softfield init      # the factory's files in .factory/, committed on main, the project registered,
                    # then Claude opens to finish with you (docs/bootstrap.md):
                    # the idea or a look at the repo, ADR 00, the checks, the first card
softfield doctor    # asks to accept ADR 00, then what the web still needs; when it passes,
                    # the runner takes the project
                    # (it leaves it alone until then). The setup session runs it for you.
```

The factory works on a branch called `main`; `init` says how to rename another one.

## Always on (optional)

```sh
softfield service install                                    # systemd user units, with your PATH
systemctl --user enable --now softfield-runner softfield-dashboard
journalctl --user -u softfield-runner -f                     # what the runner says
systemctl --user stop softfield-runner                       # its Ctrl-C
loginctl enable-linger $USER                                 # keep them up while logged out
```

## Where things live

| What | Where |
|---|---|
| A project's tickets, cards, ADRs, planning, reviews, reports | its `.factory/` (run logs in `.factory/var/`, not in git) |
| A project's checks, caps and timeouts | its `.factory/project.toml` |
| A project's own rules (taste, languages, code) | its `.factory/project.md` |
| What the developers may not touch | its `.factory/protected-paths.txt` |
| This machine's agents, roles, Claude's reserves, backup | `~/.config/softfield/factory.toml` (a copy: `tests/fixtures/softfield-machine.toml`) |
| Every project's runs, jobs, requests and threads | `~/.local/share/software-factory/factory-metrics.sqlite`, copied daily to `~/Dropbox/software-factory-backups` |
| The owner's preferences, the lead's craft, how tickets are written | this repo's `docs/agents/owner.md`, `docs/agents/lead.md`, `docs/task-writing.md` |

## How Softfield updates itself

`softfield` runs from `~/.local/share/softfield/live`, a second checkout of this repo's `main`.
When `main` moves (a merged ticket, an approved plan, a terminal session's commit), the runner
moves `live` to it at its next pick and restarts on the new code; the dashboard reloads by
itself. A merge that changes `pyproject.toml` or `uv.lock` reinstalls first. Jobs never work in
`live`, so a bad branch can't break the running factory. With the runner off,
`softfield dashboard update` does the same move by hand.

## Working on Softfield itself

```sh
uv sync
uv run softfield check-all      # ruff, mypy, the layout rule, the full suite (about 5 min, on 16 workers)
uv run pytest tests/runner      # or one folder
```

`uv run softfield` runs this work tree's code; plain `softfield` runs `live`'s. Commits go
through `softfield check-all` (the hook in `.factory/hooks/`). While the runner runs, work in a
worktree: it checks out task branches here.

How it works: [docs/how-it-works.md](docs/how-it-works.md) and [docs/workflow.md](docs/workflow.md).
Tickets: [docs/task-format.md](docs/task-format.md). The lead's craft:
[docs/agents/lead.md](docs/agents/lead.md).
