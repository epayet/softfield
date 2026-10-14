# Softfield

A software factory for the projects on this machine ([ADR 30](.factory/adr/30-many-projects-one-factory.md)).
A frontier lead (Claude) plans with the owner and writes tickets; local and cloud developers
build them; one runner gates, merges and reports; a dashboard shows it all, on a phone too.

- `softfield run`: the runner, for every registered project, by the owner's order.
- `softfield dashboard [--lan]`: the dashboard.
- `softfield init`: set up the current folder as a project (`.factory/`).
- `softfield doctor`: whether a project is ready for the web.

How it works: [docs/how-it-works.md](docs/how-it-works.md) and [docs/workflow.md](docs/workflow.md).
The lead's craft: [docs/agents/lead.md](docs/agents/lead.md).
