# ADR 13: A dashboard for the software factory

- **Status:** Accepted (by the owner, 2026-09-30; reworked in conversation around ADR 14's agents)
- **Date:** 2026-09-30
- **Deciders:** project owner (accepts), Claude (drafts)
- **Goes with:** [ADR 14](14-developers-and-agents.md) (developers, agents, ratings and routing, which this database records)

## Context

The owner wants to see how the factory performs over time ([ADR 02](02-software-factory.md)). Today the numbers are scattered, and writing the M4 review meant an hour of digging:

| Source | Holds |
|---|---|
| `.factory/var/runs/<run>/<task>/opencode-*.jsonl` | per-step tokens (so peak context), steps, timeouts |
| `.factory/var/runs/<run>/<task>/gates-*.txt` | which gate failed, on which attempt |
| `~/.local/share/opencode/opencode.db` (`part` table) | the junior's thinking, tool calls and edits |
| `.factory/sessions/*.md`, `.factory/var/runs/state.json` | merges, escalations, headless runs |
| Claude Code transcripts (`runner/usage.py`) | lead spend, interactive and headless |
| git (`Agent:` / `Task:` trailers) | lines written by juniors vs the lead |

Some of it is lost when a run crashes: M4's first run wrote no session report.

ADR 14 adds more agents (cloud developers, Copilot), ratings, findings with verdicts, and allowances to track. The owner wants to see, live:
- which agents did what
- how efficient each was at its job
- the allowance each service has used, and when it will run out
- each ticket's and each job's details

The factory is also heading out of this repo, to become a generic tool for several projects ([ADR 02](02-software-factory.md)). Nothing here should assume Coucou.

## Decisions (⚑ = deviates from this ADR's first draft)

### 1. ⚑ One metrics database per user, for every project
- **Where:** `~/.local/share/software-factory/factory-metrics.sqlite`, configurable in `runner.toml`. It's outside the repo: never in git, and shared by future projects.
- **When:** a row is written as soon as its facts are known, so a crash loses nothing.
- **Backed up daily, off the machine** (owner, 2026-10-07, F20): the runner copies the database once a day into `[backup] dir` (`~/Dropbox/software-factory-backups` by default), keeping the last 14. Planning threads, the owner's requests and the ratings live nowhere else.
- **The tables follow the hierarchy** `projects` → `milestones` → `tickets` → `jobs`, with `runs` alongside:
  - A ticket can span runs (a rerun after a pause), so every job records both its run and its ticket.
  - A **job** is one unit of work by one agent: an attempt, a direction, a checkpoint, a shadow review, an escalation, a lead ticket, a review round or a bench attempt.
  - Jobs about several tickets (a checkpoint, a review round) hang off the milestone. Their findings name the ticket each one concerns.

| Table | Holds |
|---|---|
| `projects` | name, repo path |
| `milestones` | project, number, title, dates, verdict, review rounds, the final review's score, the owner's optional score |
| `runs` | project, start and end, the command, the exit verdict |
| `tickets` | milestone, id, title, difficulty (set, then corrected), final outcome, the agent that merged it, lines changed |
| `jobs` | run, ticket (or milestone), role, agent, start and end, outcome; tokens (in, cached, out) or requests; steps, peak context, edit streak, refused commands; the routing reason; `gates` (JSON: each check with pass/fail, seconds, log path); `note` (a direction's or escalation's text on how the developer worked); the harness session id (a link only) |
| `findings` | the reviewer job, the ticket it concerns, severity, file:line, summary and detail, the agent whose code it is, the final review's verdict (confirmed/rejected/missed), route |
| `rating_changes` | agent, skill (coding/reviewing), before → after, the ticket and result that moved it |
| `usage_events` | agent, time, kind (refusal, reset, API reading), value |

- **Why these tables:**
  - Gate results and notes are columns on `jobs`, since they're always read with their job.
  - `findings` is its own table: a finding is raised by one job, often about another ticket, gets its verdict later, and counts in both ratings.
  - Spend per agent is summed from `jobs`; `usage_events` holds only what jobs can't.
- **Nothing sensitive:** no note text or photo contents, and no developer's thinking. The thinking stays in the harness's own store; a job links to it by session id.
- **Backfill:** M1–M4 from the logs that still exist.

### 2. ⚑ `uv run runner dashboard`: a small local service, not a static page
- **Where it listens:** `127.0.0.1`, while the owner wants it running. A systemd unit is a later option, with the owner's OK.
  - ⚑ **Amended by the owner, 2026-10-01:** `--host <address>` serves it on the home network too (`uv run runner dashboard --host 192.168.178.34`). It's read-only with no login, so anyone on that network can read it; it answers only to loopback names and that address, so DNS rebinding is still refused.
- **The stack:** server-rendered pages with FastAPI + Jinja2, **htmx** for the live parts, **Apache ECharts** for charts, and one stylesheet. The JS is vendored: no CDN, **no build step**.
  - Every ticket, job and finding gets a real URL, which suits text-heavy browsing.
  - The factory stays one language (Python), so it packages as one tool at extraction.
- **⚑ New dependencies, approved by the owner:** `fastapi`, `uvicorn` and `jinja2` in a `factory` dependency group, plus the vendored `htmx.min.js` and `echarts.min.js` with their licences.
- **A self-contained `factory_dashboard/` package.** It only reads the database and imports nothing from `coucou/`. It's not a protected path, since it has no gate or merge logic: the lead builds the service and the first page as the worked example, and developers build the others.
- **Everything filters by project.**

### 3. The views
1. **Overview:**
   - what's running now (agent, role, ticket, difficulty, elapsed time, live tokens)
   - the queue with each ticket's routed agent
   - the last verdict
   - one allowance bar per service: used, the reset, a **run-out forecast**, and "leftovers to spend". The forecast uses the service's API where one exists, and otherwise learns from past run-outs.
2. **Timeline:** runs and jobs over time, one lane per agent, coloured by outcome, with refusals and fallbacks marked.
3. **Jobs:** a filterable list (project, milestone, ticket, agent, role, outcome), and a page per job:
   - prompt summary, gates, diff stats, findings, note
   - tokens and time, routing reason, log links
4. **Tickets:** a page per ticket with all its jobs in order, from the first attempt to the merge, plus every finding about its code.
5. **Agents:**
   - coding and reviewing ratings over time, against the difficulty of each ticket
   - role eligibility from shadowing (ADR 14 item 12)
   - efficiency: pass rate, attempts, time and tokens per merge, gates failed, escalation rate, rework, tokens per second
   - who did what: agents × roles
6. **Milestones:** each milestone's results, and trends across milestones:
   - pass rate, escalations
   - Claude spend per merged ticket, and Claude-equivalent work done by other agents
   - findings per ticket, both scores
   - ADR 07's measures
7. **Bench:** each replayed ticket × agent (ADR 14 item 8).

### 4. `runner report N` takes the review's numbers from the same queries
It writes them into `.factory/reviews/mN.md` as a frozen snapshot, per ADR 14 item 16.

### 5. Later, only if wanted
Grafana over the same database, for time-series trends. It's weak for text-heavy drill-down and it's a service to install, so it needs the owner's OK.

## Consequences
- **Before M5:** the runner writes the database from every job, and the dashboard runs, so M5 is measured from its first job. The rest of ADR 14 can follow alongside M5.
- **The review gets cheaper:** its numbers come from one query instead of an hour of log reading.
- **Tool-neutral and project-neutral:** only the adapters' log parsers know about Claude, OpenCode or Copilot, so another frontier, developer or project plugs in (ADR 02).
- **Build order:** a mockup of the pages, with M4's real numbers, before the first ticket.
