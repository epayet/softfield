# Milestone F127: The factory is optional: its context is injected, and each thing lives with whoever it's true for

> **State:** ready · **Priority:** 100 · **Area:** factory
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

### From F134: softfield init fits a repo that already has its own AGENTS.md and CLAUDE.md (merged by the lead on 2026-11-02)
From the terminal session of 2026-10-14 (ADR 30). The owner asked what `softfield init`
does in a repo that already has AGENTS.md and CLAUDE.md, and whether it works with the factory.

Today: `setup.init` writes a template only where no file exists (`if path.exists(): continue`
over `setup.FILES`), so the repo's own AGENTS.md, CLAUDE.md, opencode.json and
.softfield/developer.md stay as they are, and runner/instructions/bootstrap.md never says to bring the
factory's parts into them (seen on the fact-printer trial).

What still works: the runner's gates (protected paths, diff size, tests: they read .softfield/),
and Claude's jobs from the runner (the brief pastes owner.md, lead.md's sections and
.softfield/project.md into every prompt, `prompts.brief`, `loop._brief`).

What doesn't:
- a terminal Claude session in that repo reads only the repo's CLAUDE.md: no owner's
  preferences, no project.md, nothing saying it's a Softfield project;
- the local developer (OpenCode) reads AGENTS.md plus opencode.json's `instructions`: nothing
  about BLOCKED.md, protected paths or adding no dependencies; and a repo's own opencode.json may
  not allow `softfield check-all`, so the developer can't check before the gates do. Mistakes
  surface late, as failed attempts.

Proposed:
1. The setup session merges instead of replacing (runner/instructions/bootstrap.md, "An existing project"):
   a short "Softfield" section in AGENTS.md with the factory's rules (scope, protected paths,
   no new dependencies, BLOCKED.md, discoveries; from runner/templates/AGENTS.md); the two
   import lines in CLAUDE.md (`@~/.local/share/softfield/live/runner/instructions/author/owner.md`,
   `@.softfield/project.md`); in opencode.json, AGENTS.md and .softfield/developer.md among
   `instructions` and `softfield check-all*` allowed. What the repo already says stays.
2. `softfield doctor` checks each of those and names the missing one.
Related: the planted card about shared rules staying shared (AGENTS.md drift).


### From F137: The developers' notes move to .softfield/developer.md in every project (merged by the lead on 2026-11-02)
the .softfield/developer.md setup in init looks very factory specific, so it should be in .softfield


## Done (2026-11-02, terminal session)
[ADR 41](../adr/41-the-factory-is-optional.md), accepted by the owner: the factory is optional, what it starts gets its context in the system prompt, and `softfield lead` is how a terminal session gets the lead's brief. Instructions moved to `runner/instructions/`; `docs/` is for people. F134's and F137's drafted tickets were dropped: they built the copies and appended rules the owner sent back.
- **Proved:** on a repo with a hostile `opencode.json`, a captured request shows the factory's rules, the project's and the repo's own in the system message, and the check-all permission intact. A clean install of the built package finds every instruction file. A resumed Claude session costs the same with the brief in the system prompt as pasted (measured: identical tokens).
- **Left:** the view of each role's files (ADR 41 item 6), `f127-02-who-reads-what`, with its mock-up first, for the runner.

