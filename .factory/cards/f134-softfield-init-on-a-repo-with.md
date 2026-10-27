# Milestone F134: softfield init fits a repo that already has its own AGENTS.md and CLAUDE.md

> **State:** idea · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-15.

## Notes
From the terminal session of 2026-10-14 (ADR 30). The owner asked what `softfield init`
does in a repo that already has AGENTS.md and CLAUDE.md, and whether it works with the factory.

Today: `setup.init` writes a template only where no file exists (`if path.exists(): continue`
over `setup.FILES`), so the repo's own AGENTS.md, CLAUDE.md, opencode.json and
docs/agents/developer.md stay as they are, and docs/bootstrap.md never says to bring the
factory's parts into them (seen on the fact-printer trial).

What still works: the runner's gates (protected paths, diff size, tests: they read .factory/),
and Claude's jobs from the runner (the brief pastes owner.md, lead.md's sections and
.factory/project.md into every prompt, `prompts.brief`, `loop._brief`).

What doesn't:
- a terminal Claude session in that repo reads only the repo's CLAUDE.md: no owner's
  preferences, no project.md, nothing saying it's a Softfield project;
- the local developer (OpenCode) reads AGENTS.md plus opencode.json's `instructions`: nothing
  about BLOCKED.md, protected paths or adding no dependencies; and a repo's own opencode.json may
  not allow `softfield check-all`, so the developer can't check before the gates do. Mistakes
  surface late, as failed attempts.

Proposed:
1. The setup session merges instead of replacing (docs/bootstrap.md, "An existing project"):
   a short "Softfield" section in AGENTS.md with the factory's rules (scope, protected paths,
   no new dependencies, BLOCKED.md, discoveries; from runner/templates/AGENTS.md); the two
   import lines in CLAUDE.md (`@~/.local/share/softfield/live/docs/agents/owner.md`,
   `@.factory/project.md`); in opencode.json, AGENTS.md and docs/agents/developer.md among
   `instructions` and `softfield check-all*` allowed. What the repo already says stays.
2. `softfield doctor` checks each of those and names the missing one.
Related: the planted card about shared rules staying shared (AGENTS.md drift).
