# CLAUDE.md: Claude-only details

**You are the lead.** Follow [`AGENTS.md`](AGENTS.md) and [`docs/agents/lead.md`](docs/agents/lead.md): the process, the owner's preferences and what reaches the owner all live there, so any frontier model can lead. This file holds only what is specific to Claude.

## Model nudges
At the end of each phase, give the owner a ready-to-paste command for the next session (ADR 07 item 11). The owner may ignore it; nothing depends on it.
- Mechanical phases (tickets from an agreed plan, dry runs, small fixes): `claude --model sonnet "<brief>"`
- Plans, ADRs, protected code, security and reviews: `claude --model opus "<brief>"`

## Headless runs
The runner calls `claude -p` for lead tickets, directions, checkpoints, escalations and reviews (`runner/claude.py`, `runner/loop.py`) with the Pro login and a per-job tool list; checkpoints run on Sonnet (`checkpoint_model`), the rest on the default model. Headless jobs may read git (diff, log, show) but never commit: the runner does. Scope file writes with `Edit(<glob>)` (it covers Write too); `Write(<glob>)` grants nothing in `--permission-mode dontAsk` (probed 2026-09-30).

## Memory
**Prefer remembering in the repo, not in Claude's memory.** When you would save a memory about the owner, the project or the workflow, write it in `docs/agents/lead.md` instead (or `docs/agents/junior.md`, or `docs/task-writing.md` for ticket craft), so another frontier inherits it. Use Claude's memory only for what is truly Claude-specific (Claude Code quirks, `/model`, headless `claude -p`), plus pointers to the repo.
