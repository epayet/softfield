# Milestone F127: Generic developer lessons live once in Softfield, every project reads them

> **State:** idea · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-14.

## Notes
From the terminal session of 2026-10-14 that built ADR 30 (sessions B, C, D).

ADR 30 item 4: rules are global unless a repo needs its own. In practice `softfield init` copies
runner/templates/AGENTS.md (the generic scope, tests, BLOCKED and discoveries rules) and
developer.md into each project, so they drift: a lesson learned in one project doesn't reach
the others. Coucou's AGENTS.md and .softfield/developer.md still carry generic notes next to
Coucou's own; Softfield's are separate copies.

Proposed: the generic rules and the developers' generic lessons live once in Softfield's docs/;
each project's AGENTS.md points at them (OpenCode's `instructions` can list an absolute path
under live) and keeps only its own rules; developer.md splits into shared lessons and the
project's own worked examples. Check what the local developer actually reads (opencode.json
`instructions`) before deciding.
