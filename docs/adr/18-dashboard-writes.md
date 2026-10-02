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
  - entering Ollama's usage by hand (Ollama has no usage API).
- **Today the dashboard opens the metrics database read-only** (`factory_dashboard/queries.py`). It listens on `127.0.0.1`, and the runner only takes answers on its terminal (`read_answer` in `runner/loop.py`).
- The repo is the state. Sign-off commits and tags (`runner/owner.py` `signoff`), and queueing a ticket moves a file. The runner is the only writer of git while it runs.

## Decisions (draft)
1. **⚑ Listen on the home Wi-Fi.**
   - `runner dashboard --lan` binds to the LAN address; the default stays `127.0.0.1`.
   - No tunnel, no public host.
2. **⚑ Writes are requests, never direct changes.**
   - The dashboard writes one row to a new `owner_requests` table: kind, subject, value, time, and a per-device key.
   - The runner, or the `runner` command when no run is live, applies each request with the same code as its console command (`signoff`, `queue`, the 5-hour answer). It then marks the request done, with its result.
   - Git and `tasks/` keep one writer.
3. **A guard even on the LAN.**
   - A one-time pairing: the desktop shows a code, and the phone keeps a long random token in a cookie.
   - Every write needs that token, and CSRF protection on every form.
   - Reads stay open on the LAN. This is security-relevant, so the lead writes it, test-first.
4. **Notifications:** web notifications from an open dashboard page first (no third party), for "needs you" and "all work done".

## Open questions
- Does a phone need a push when the page is closed? That needs a push service (web push through the browser vendor, or a self-hosted ntfy). Decide after using item 4.
- Which requests come first: sign-off and the 5-hour answer, then queue/later, then priorities (with [ADR 19](19-feature-board.md)), then the manual Ollama reading?
- Is the pairing code too much ceremony for a home network?
