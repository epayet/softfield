# ADR 41: The factory is optional: its context is injected, and each thing it knows lives with whoever it's true for

- **Status:** Accepted (by the owner, 2026-11-02)
- **Date:** 2026-11-02 (drafted 2026-10-27 on F127 as "35", rewritten twice with the owner)
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 30](30-many-projects-one-factory.md) item 4 (a project's `AGENTS.md` and `CLAUDE.md` point at the global rules), item 7 (`init` writes the pointer files) and its amendment "a project may carry its own `docs/agents/lead.md`".
- **Evidence:** F127, F134 and F137's threads. `softfield init` copies `AGENTS.md`, `CLAUDE.md`, `opencode.json` and `developer.md` into a project and never looks again; four generic lessons in Softfield's developer notes since 2026-10-15 never reached Travel Companion. The owner, 2026-11-02: people should be able to use OpenCode and Claude on a project with little context of the factory; it's an optional addition; agents started by the factory must have its context, and agents, local ones especially, don't always follow an instruction to read a file. Probe, OpenCode 1.18.32, on a fake model that captured the request: `instructions` set through `OPENCODE_CONFIG_CONTENT` reach the system message, from an absolute path outside the repo with `external_directory` denied, and the repo's own AGENTS.md and `instructions` still arrive; with `OPENCODE_CONFIG` a repo's own `opencode.json` wins (`"bash": "deny"` beat the factory's permission).

## Decisions (⚑ = deviates from an earlier decision)
1. ⚑ **The factory is optional.** A person or agent working without it sees a normal repo. `init` never touches or creates `AGENTS.md`, `CLAUDE.md` or `opencode.json`, and writes nothing in `docs/`. What it leaves is the dot folder, with a `README.md` saying what the folder is, that it can be ignored and how to remove it.
2. ⚑ **Its context is injected, never read by choice.** Everything the factory starts gets its context in the system prompt:
   - OpenCode: the runner sets `OPENCODE_CONFIG_CONTENT` for the run, with `instructions`, providers and permissions. A project needs no `opencode.json`, and one of its own can't stop the developer.
   - Claude jobs: `--append-system-prompt`, replacing the brief pasted into the first message.
   - Copilot: pasted in the prompt as today (it has no such flag; its custom instructions are off).
3. ⚑ **`softfield lead`** starts a terminal lead session with the same system prompt a lead job gets. A plain `claude` or `opencode` in a repo stays plain.
4. ⚑ **Each piece of knowledge lives with whoever it's true for.** Injected in this order, a later layer winning, except where a gate enforces the rule:
   - **The package,** read-only and versioned, `runner/instructions/`: `rules.md` (the generic rules), `lead.md`, `developer.md` (lessons that hold anywhere), `task-format.md`, `task-writing.md`, `bootstrap.md`.
   - **The author's opinions,** in the package for now so they're versioned for free, `runner/instructions/author/`: `owner.md`, `known-range.md`. Each opens by saying whose opinions these are and how to replace them. `~/.config/softfield/owner.md` or `known-range.md` replaces the package's file.
   - **The project's factory files,** in the dot folder: `project.md`, `developer.md`, `discoveries.md`. An upgrade never touches them.
   - **The project's own docs,** which the factory never touches. `project.md` may point at them ("Python style: docs/style.md").
5. **A gated rule changes where the gate reads it** (`project.toml`, `protected-paths.txt`), not in words.
6. **Updating Softfield updates the rules.** Nothing is copied, so nothing merges and nothing goes stale. The owner follows main through `live`; others `uv tool install` from GitHub and `uv tool upgrade`. Numbered releases and an "update available" notice come with publishing (its own card). A dashboard view lists each role's files as from Softfield, yours, or this project's.
7. ⚑ **How a lesson travels.** A checkpoint writes it into its own project's notes, always: a job in one project can't write to Softfield's repo. If it holds everywhere, the review suggests it as a Softfield card in "What next"; once approved it lands in Softfield and ships with the next version. 15 notes per file (ADR 07).
8. ⚑ **`docs/` is for people.** Softfield's agent instructions leave `docs/agents/` for the package, which today ships none of them. The factory stops writing in a project's `docs/`.
9. ⚑ **One rule, Softfield included, and the three projects migrate once.** Coucou's and Travel Companion's root files keep only what's useful to anyone working on them, and go if nothing is left. Softfield's `AGENTS.md` and `CLAUDE.md` describe only how to work on its code. So `claude` in a project is no longer the lead; `softfield lead` is.

## Alternatives turned down
- **Each project owns a full copy and merges updates** (the first draft): the owner sent it back; it puts the factory's text in the project's own files and needs a merge on every change.
- **One line in the root files:** it would remind a plain `claude` that `softfield lead` exists, but it edits the project's own files.
- **Your opinions in `~/.config/softfield/` now:** the owner chose to keep them versioned in the package while there's one user.
- **`OPENCODE_CONFIG`:** a repo's own config beats it (probe above).

## Consequences
- The factory's footprint on a project is its dot folder. Removing it means deleting that folder.
- A rule change reaches every project at its next job. That's the point; the Accepted-ADR rule keeps it deliberate, and it is the main risk.
- Forgetting `softfield lead` gives a session without the owner's preferences, and nothing warns about it. Accepted by the owner.

## What doesn't change
The gates, the protected paths' meaning, the note limit, and what a lead or developer is asked to do.

## Settled with the owner (2026-11-02)
Injection over root-file pointers; a README in the dot folder and nothing at the root; Softfield under the same rule; instructions in the package; the author's opinions in the package for now, labelled and replaceable.
