---
id: f3-21-since-you-looked
milestone: f3
depends_on: [f3-20-machines-and-belts]
difficulty: 5
files:
  - factory_dashboard/queries.py
  - factory_dashboard/overview.py
  - factory_dashboard/templates/overview.html
  - factory_dashboard/templates/_partials/away.html
  - factory_dashboard/static/factory.js
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview says, in words, what the factory did since the owner last looked. "Replay overnight" becomes "Since you last looked (HH:MM)", with other spans to choose from.

### Context
Read `overview` in `factory_dashboard/overview.py` (the replay URLs and the `line_seen` cookie: it is read before it is set again), `overnight` and `line_replay` in `factory_dashboard/line.py`, `queries.clog` and its `Clog` dataclass in `factory_dashboard/queries.py` (the pattern to follow), the replay bar in `factory_dashboard/templates/overview.html`, `startReplay` in `factory_dashboard/static/factory.js` and the overview tests in `tests/factory_dashboard/test_overview.py`.
- **Why (owner, 2026-10-03):**
  - "The replay overnight is not clear: what does overnight mean?"
  - "I like the idea of reviewing since last time I saw it, or from a certain time frame."
  - "I need a nice way to see what was done while I didn't watch."

  `overnight()` already means "since you last opened the page, else 20:00 yesterday"; only the words hide it.
- **The data:** `queries.away(conn, project, since, now) -> Away`, a dataclass like `Clog`, from the metrics database:
  - `merged`: the tickets that reached `done` in the span, latest first, each with its ticket name (`tickets.ticket`, which `/tickets/<id>` expects, not the integer row id), title and who merged it (`tickets.merged_by`). A ticket's time is its last job's `ended`.
  - `failed`: developer and last-attempt jobs ended `failed` in the span.
  - `escalations`: escalation jobs started in the span.
  - `blocked`: the project's tickets in state `blocked` now.
  - `needs_you`: owner items created in the span.
  - `claude_usd`: the summed `cost_usd` of jobs whose agent starts with `claude-`, started in the span.
- **Fixtures:** `metrics.start_job` keys a job on (run, ticket, role, attempt): a second call with the same four restarts the same row instead of adding one. Give each fixture job its own attempt or run.
- **The panel** `#away` ("While you were away", in `factory_dashboard/templates/_partials/away.html`):
  - It goes right after the floor and the replay bar. The section order in `test_the_overview_shows_every_panel_in_order` gains `away`.
  - One line of counts, then the merged tickets as links to `/tickets/<ticket name>`.
  - With nothing in the span, it says "Nothing happened since HH:MM."
  - It is rendered at page load only, with no 5 s refresh.
- **The choices** replace the replay bar's select. The panel and the replay follow the chosen span:
  - "since you last looked (HH:MM)", the default, from `overnight(...)`, always showing its time;
  - "the last hour";
  - "today", since local midnight;
  - "the last 24 h".

  The span reaches the page as `?since=<iso>`: choosing an option reloads `/` with that `since`, and the page's replay URL is built from the same `since`, so "Replay" plays the chosen span. Today `startReplay` reads the select's value as the name of a `data-replay*` attribute on the page, so changing the option values alone breaks Replay. An ISO time has a `+`, which a URL turns into a space: encode it in links and tests. "Replay" stays the button's word.
- Plain words only, with no abbreviations (owner).

### Done when
- `queries.away` has unit tests on fixture jobs: each count, the merged order, and a job outside the span left out
- `/` shows "Since you last looked" with the cookie's time and no "overnight"; `/?since=<iso>` shows the panel for that span
- the panel lists each merged ticket as a link, and says "Nothing happened since …" for an empty span
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
