# ADR 06: Server-sent events instead of WebSockets; JavaScript tested in the browser

- **Status:** Accepted (by the owner, 2026-09-28; both items as drafted, including the WebSocket fallback if the Funnel test fails, the Chromium download, and UI-only JS for the local model)
- **Date:** 2026-09-28
- **Deciders:** project owner (accepts), Claude (drafts)

## Context

While planning M3, the owner made two points:
- **Push is one-way.** Every client write goes over HTTP: reactions from M3, and posts from M4. The live channel only ever pushes from the server to the device, so why not use server-sent events (SSE)?
- **The gates don't test JavaScript.** Claude's M3 plan said they can't, so all display JS had to be Claude's. They can: Playwright is driven from pytest and runs a real browser, and M3 installs it anyway (ADR 03 item 6).

**Evidence for item 2 (a workflow change).**
- The local model's record so far (`.factory/reviews/m1-metrics.md`, `m2-metrics.md`) is 10 tasks over M1–M2, all merged, with 9/10 passing on the first attempt of their final run.
- There were 3 escalations: 2 spec errors during calibration, fixed by ADR 01, and 1 tool permission (m2-01, ADR 04). None was the model failing at the code.
- It works well on small, well-tested tasks.
- In the current M3 plan it gets 6 tasks, while Claude writes every line of display JS, because nothing could check the local model's JS.

## Decisions

### 1. ⚑ Live updates use SSE, and Django Channels is dropped

Changes ADR 00 §1 ("Real-time: Django Channels over WebSockets"), and the WebSocket parts of §2.2 and §2.3.

- **One stream per device:** `GET /api/stream` (`text/event-stream`), an async streaming response in the public process.
  - The existing session middleware authenticates it like any other request: the cookie, the session row and revocation.
  - A display gets its space's events. A personal device (M4/M5) gets the events of the spaces it may read, via `coucou.scoping`.
- **Resuming:** each message carries an `id`. On reconnect, the browser's `EventSource` sends `Last-Event-ID`, and the server replays what was missed. When the gap is too old or unknown, the server sends a fresh snapshot instead. Reconnecting is built into the browser; the client only adds the re-auth when the session has expired.
- **Fan-out and revocation:**
  - The public process has one in-process hub (`coucou/live/`) and the DB watcher from ADR 00 §2.2.
  - Every second, the watcher polls `AuthGeneration` and events received since its last look.
  - It pushes new events to the matching streams.
  - It ends the streams of revoked devices within **≤ 2 s**, unchanged from ADR 00.
- **Heartbeat:** a comment line every 20 s keeps proxies from closing an idle stream. Each heartbeat also re-checks the session, and the stream ends when the session expires (1 h).
- **Dependencies:**
  - `channels` leaves `pyproject.toml`, and `asgi_public.py` serves the plain Django ASGI app.
  - The admin/public separation (ADR 00 §2.2) doesn't change.
- **Tailscale Funnel first:** before building this, Claude runs a 10-minute test on staging through Funnel. Events must arrive unbuffered and the stream must survive idle periods. If Funnel buffers or cuts the stream, M3 goes back to WebSockets as ADR 00 has it, and this item lapses.

**Not chosen:** keeping WebSockets for a two-way channel nothing uses; long polling.

### 2. ⚑ JavaScript modules are tested in a real browser, inside the tests gate

Changes `docs/workflow.md` (the tests gate) and `docs/task-writing.md`. The gates, caps and task format otherwise stay the same.

- **New layer `tests/browser/`:** pytest-playwright runs **headless Chromium**. A small fixture serves `coucou/static/` and a harness page.
  - Each test imports one ES module and checks it with network calls stubbed through `page.route`.
  - For example: render this snapshot and expect these `data-state` sections; queue a tap offline, go online, expect exactly one POST.
- **One test file per module,** like ADR 00 A1: `coucou/static/coucou/js/x.js` ↔ `tests/browser/test_x.py`. The `layout` gate checks the names.
- **The `all-tests` gate** runs `tests/browser` along with unit, integration and runner tests. The target is under 15 s. WebKit stays in `pytest -m e2e` on staging.
- **Browsers:** Chromium goes to Playwright's user cache (about 150 MB, no system packages), via `uv run playwright install chromium`, once per machine. If the browser is missing, browser tests fail with a clear message, never skip silently (the m2-F4 lesson).
- **Who writes which JS:**
  - **Claude only:** the security-relevant modules, meaning the crypto, `auth.js`, `pairing.js`, the outbox and the service worker. They stay in `.factory/protected-paths.txt`.
  - **Local-model tasks:** rendering, transitions and UI state, with Claude writing the failing browser tests first, as for Python.

**Not chosen:** Node with a test runner (the project has no Node); leaving JS untested until e2e.

## Consequences

- **One dependency fewer** (`channels`), and less protected code: no WebSocket handshake auth and no consumer.
- **The session middleware keeps its single-check guarantee.** The stream is a normal request, so it adds no second auth path to test.
- **Before M3 builds on item 1,** it has to pass the Funnel test.
- **The tests gate gets slower** by a few seconds, and each machine needs a one-time browser download.
- **The M3 plan** moves display rendering and transitions to local-model tasks with browser tests (see `.factory/cards/m3.md`).
- **Docs to update:**
  - `docs/architecture.md`: the `live/` description, and M3 as the milestone for real-time
  - `docs/workflow.md`: the tests gate
  - `docs/task-writing.md`: JS tasks

## Funnel test (2026-09-28): passed

A throwaway SSE server went out through Tailscale Funnel's public relay. It sent only a counter and a timestamp.
- **Timing:** 13 events 5 s apart, then one at 300 s and one at 600 s, with heartbeats every 20 s.
- **Clients:** one ran on the desktop, forced through the relay's public address (`curl --resolve`, because the desktop's own DNS keeps the name inside the tailnet). The owner's phone on mobile data was the second.
- **Result:** every event arrived, in 11–14 ms through the relay and under 300 ms on the phone. There was no buffering, and the stream stayed open through both idle periods. Item 1 stands: no fallback to WebSockets.
- **Seen on the way:**
  - Scanners probed the new Funnel address within minutes, through the certificate logs.
  - Once, the relay stopped forwarding to the desktop, while the desktop still reported Funnel as on. `tailscale funnel reset` followed by a new `tailscale funnel` fixed it.
  - Displays must survive this kind of outage: the offline cache and reconnection in M3 cover it. Note it for the M6 pilot.
