# ADR 13: A dashboard for the software factory

- **Status:** Proposed (the owner's idea, to explore; first step only)
- **Date:** 2026-09-30
- **Deciders:** project owner (accepts), Claude (drafts)

## Context

The owner wants to see how the factory performs over time ([ADR 02](02-software-factory.md)). Today the numbers are scattered, and writing the M4 review meant an hour of digging:

| Source | Holds |
|---|---|
| `var/runs/<run>/<task>/opencode-*.jsonl` | per-step tokens (so peak context), steps, timeouts |
| `var/runs/<run>/<task>/gates-*.txt` | which gate failed, on which attempt |
| `~/.local/share/opencode/opencode.db` (`part` table) | the junior's thinking, tool calls and edits |
| `docs/sessions/*.md`, `var/runs/state.json` | merges, escalations, headless runs |
| Claude Code transcripts (`runner/usage.py`) | lead spend, interactive and headless |
| git (`Agent:` / `Task:` trailers) | lines written by juniors vs the lead |

Some of it is lost when a run crashes: M4's first run wrote no session report.

## Decision (first step)

### 1. The runner writes a metrics database
- **Where:** `var/metrics.sqlite` (gitignored, like `var/runs/`).
- **When:** after each attempt, each escalation and each session. A row is written as soon as its facts are known, so a crash loses nothing.
- **Tables:** `sessions`, `tasks`, `attempts` (and `steps` for per-step tokens), `gate_results`, `escalations`, `claude_usage`.
- **Nothing sensitive:** note text and photo contents never appear in it, and neither does the junior's thinking. The thinking stays in `opencode.db`; the dashboard only links to it by session id.

### 2. `uv run runner dashboard` builds one static page
- **Output:** `var/dashboard.html`, self-contained, no server, no CDN (AGENTS.md rule 7 applies to our tools too). Charts are inline SVG.
- **Per milestone and as trends:**
  - first-attempt pass rate
  - attempts and gate failures by gate
  - timeouts and loop stops
  - peak context against the loaded size
  - local tokens, and Claude spend per merged junior task
  - escalations and why
  - junior share of lines
  - findings per review
- **ADR 07's measures table** is filled in automatically for the next review.
- **Backfill:** M1–M4 from the logs that still exist.

### 3. Later, only if wanted
- **Datasette** over the same file, for ad-hoc queries (one dev dependency).
- **Grafana** with a SQLite data source, for live history. It's a service to install and run, so it needs the owner's OK (lead.md: no services without asking).

Both read the same `metrics.sqlite`, so step 1 isn't wasted whichever way it goes.

## Consequences
- A little runner code (writing rows) and one command, with runner tests. No new runtime dependency.
- The review's metrics section and ADR 07's table come from one query instead of an hour of log reading.
- It stays tool-neutral: nothing in it depends on Claude or OpenCode beyond the parsers that read their logs, so another frontier or junior can be plugged in (ADR 02).
