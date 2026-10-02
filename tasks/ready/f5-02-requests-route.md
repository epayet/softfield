---
id: f5-02-requests-route
milestone: f5-board
depends_on: [f5-01-requests-apply]
agent: lead
difficulty: 5
files:
  - factory_dashboard/requests.py
  - factory_dashboard/app.py
  - factory_dashboard/templates/_partials/request.html
  - docs/agents/developer.md
tests:
  - tests/factory_dashboard/test_requests.py
---

### Goal
`POST /requests` lets a dashboard page ask the runner for something; it is the dashboard's only write, and the worked example the button tickets follow.

### Context
Read `docs/adr/18-dashboard-writes.md` items 2 and 3, D1 and D3 in `docs/milestones/f5-board.md`, `factory_dashboard/app.py` (the read-only `Db` dependency, `serve`) and `runner/metrics.py` (`add_request`). Test-first.
- A writable connection is opened only inside this route, never through `Db`.
- The guard is the `HX-Request` header plus an `Origin` (or `Referer`) whose host is the request's own host. Anything else gets 403 and writes nothing.
- The response is `factory_dashboard/templates/_partials/request.html`: "Asked: the runner will do it." With `hx-get` on the request's status every 5 s, it shows the `result` once the request is done, then stops polling.
- Add the pattern ("a button that asks the runner") to the worked examples in `docs/agents/developer.md`, pointing at this route and its tests.

### Done when
- a POST with the htmx header from the same origin writes one row and returns the partial
- a POST without the header, or from another origin, gets 403 and writes nothing
- the status partial shows the result once the request is finished
- `uv run runner check-all --task f5-02-requests-route` passes
