# Softfield

A software factory for the projects on this machine ([ADR 30](.factory/adr/30-many-projects-one-factory.md)).
A frontier lead (Claude) plans with the owner and writes tickets; local and cloud developers
build them; one runner gates, merges and reports; a dashboard shows it all, on a phone too.

- `softfield run`: the runner, for every registered project, in the owner's order (the
  Projects page sets it); `softfield run --here` for this folder's project alone.
- `softfield dashboard [--lan]`: the dashboard; it opens on `/projects`. `softfield dashboard
  update` brings it to Softfield's latest main now (the runner does so at its next pick).
- `softfield init`: set up the current folder as a project, new or existing, then open Claude to
  finish with you (`docs/bootstrap.md`).
- `softfield doctor`: whether a project is ready for the web.
- `softfield service install`: systemd user units for the runner and the dashboard.

Softfield runs from `~/.local/share/softfield/live`, a checkout of this repo's `main`; a merge
moves it and the runner restarts on the new code (ADR 30 item 5). The machine's settings are in
`~/.config/softfield/factory.toml` (a copy: `tests/fixtures/softfield-machine.toml`).

How it works: [docs/how-it-works.md](docs/how-it-works.md) and [docs/workflow.md](docs/workflow.md).
The lead's craft: [docs/agents/lead.md](docs/agents/lead.md).
