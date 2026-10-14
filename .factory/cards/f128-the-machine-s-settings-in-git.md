# Milestone F128: The machine's settings in git

> **State:** idea · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-14.

## Notes
From the terminal session of 2026-10-14 that built ADR 30 (sessions B, C, D).

ADR 30 item 3 split the settings: the machine's agents, roles, Claude's reserves, local model,
metrics and backup are in `~/.config/softfield/factory.toml`, outside any repo; each project's
in its `.factory/project.toml`. The machine file isn't versioned or backed up (a copy sits in
~/backups/softfield-factory-2026-10-14.toml, and tests/fixtures/softfield-machine.toml is the
tests' copy, which drifts).

Proposed: keep the real defaults in Softfield's repo (e.g. `machine.toml`), read first, with
`~/.config/softfield/factory.toml` only overriding what differs on this machine; the tests read
the repo's file. Rating and role changes then show in git history like everything else.
