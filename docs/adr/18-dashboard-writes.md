# ADR 18: The dashboard on the home Wi-Fi, and what it may write

- **Status:** Proposed (draft, to discuss with the owner)
- **Date:** 2026-10-02
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 13](13-factory-dashboard.md) (the dashboard is read-only and listens on the desktop only)
- **Evidence:** the owner's notes after F2 (`docs/roadmap.md`, "Owner's notes after F2"). The owner chose the home Wi-Fi only, not Tailscale or a public host (2026-10-02).

## Context
- The owner wants to follow the factory and steer it from a phone. That means:
  - signing off a milestone;
  - answering the runner's questions (Claude's reserve);
  - queueing a ticket from `tasks/later/`;
  - reordering priorities;
- **Today the dashboard opens the metrics database read-only** (`factory_dashboard/queries.py`). It listens on `127.0.0.1`, and the runner only takes answers on its terminal (`read_answer` in `runner/loop.py`).
- The repo is the state. Sign-off commits and tags (`runner/owner.py` `signoff`), and queueing a ticket moves a file. The runner is the only writer of git while it runs.

## Decisions (draft)
1. **⚑ Listen on the home Wi-Fi.**
   - `runner dashboard --lan` finds this machine's LAN address and binds to it (the owner runs `--host <ip>` today); the default stays `127.0.0.1`. It keeps picking up new code as it does now.
   - No tunnel, no public host.
2. **⚑ The dashboard's only write is a request row.** It writes to the metrics database (one new table), never to git or `tasks/`, and it changes nothing itself.
   - The dashboard writes one row to a new `owner_requests` table: kind, subject, value and time.
   - The runner, or the `runner` command when no run is live, applies each request with the same code as its console command (`signoff`, `queue`, the 5-hour answer). It then marks the request done, with its result.
   - Git and `tasks/` keep one writer.
3. **⚑ No pairing or login on the home network** (owner, 2026-10-02: "it's fine for people within my home to access"). Anyone on the Wi-Fi can read and write. The one guard kept is free: a write must come from the dashboard's own page (same origin, htmx's `HX-Request` header), so a website open in the owner's browser can't post to it.
4. **Notifications:** browser notifications while a dashboard page is open, for "needs you" and "all work done". Push to a closed page is in the roadmap (owner, 2026-10-02).

5. **Requests, first:** sign-off, the 5-hour answer, and queueing a ticket from `later/`. Moving and editing cards, adding ideas and planner questions come later (ADR 19 item 4); until then the owner does those in a Claude Code session. No manual Ollama reading (owner, 2026-10-02: too much hassle).

## Open questions
None left (2026-10-02).
