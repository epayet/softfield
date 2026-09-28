# ADR 03: Pairing details ADR 00 leaves open

- **Status:** Proposed
- **Date:** 2026-09-28
- **Deciders:** project owner (accepts), Claude (drafts)

## Context

ADR 00 §2.3–2.4 fixes the pairing and session protocol. Building M2 turns up a few choices it doesn't settle. Each item is independent, so you can accept some and reject others. Until an item is accepted, nothing that depends on it gets built. The Claude-only protocol work (M2 items C1–C6) doesn't depend on any of them.

## Decisions (proposed)

### 1. ⚑ Serve static files from the public app now, without a new dependency

**Why now:** the backlog said to decide this in M3. But the pairing page needs its JS and CSS in M2.

**Proposal:**
- A small protected view serves files under `coucou/static/coucou/` only. It refuses paths with `..`, lists no directories, and sets the content type from an allow-list (`.js`, `.css`, `.svg`, `.png`, `.webmanifest`).
- It sends an `ETag` and `Cache-Control: no-cache` until M3's service worker brings versioned file names.
- No WhiteNoise, no new dependency.

**Alternative:** WhiteNoise. It's mature, but it's a new dependency for a handful of files.

### 2. ⚑ Session cookie over plain `http://localhost` (dev and staging only)

**The problem:** ADR 00 §2.3 names the cookie `__Host-coucou_s`, which browsers accept only with `Secure`. Chromium treats `http://localhost` as secure, but WebKit may not, so the staging e2e tests could fail in WebKit for a reason that never happens in production.

**Proposal:**
- **Prod** always uses `__Host-coucou_s` with `Secure`. A settings test asserts this.
- **Dev and staging** use `coucou_s` without `Secure`, but **only if** `COUCOU_PUBLIC_ORIGIN` starts with `http://localhost` or `http://127.0.0.1`.

If WebKit turns out to accept `__Host-` on localhost, I'll drop this item.

### 3. Entry URLs

- `/display/` shows the display pairing screen, and `/phone/` the phone's. The kind comes from the URL, so there's no "what are you?" picker.
- `/` redirects to `/phone/`.
- After pairing, the same URL shows the "all set" page (until M3 and M4 build the real apps there).

### 4. The pairing screen's voice

- **French uses `tu`**: it's family, and warmer. English is just as informal.
- The screen says whom to give the code to, e.g. "Coucou ! Pour relier cet écran, donne ce code à {name}." The name comes from a new setting, `COUCOU_OWNER_NAME` (in the env file, so the repo doesn't hardcode it). When it's empty, the screen falls back to "the person who set this up".

### 5. Expired codes aren't renewed automatically

- A code lasts 10 minutes. When it expires, the screen shows **"Get a new code"**, and a new code is issued only when someone taps it.
- **Why:** a display left on the pairing screen overnight would otherwise re-register every 10 minutes and hit the limit of 20 registrations a day in about 3 hours.

### 6. Download Playwright's browsers

- Needed for C1's signature vectors and the C9 e2e tests: `uv run playwright install chromium webkit` puts about 300 MB in `~/.cache/ms-playwright`, and installs no system packages.
- If WebKit also needs `playwright install-deps` (system libraries through `sudo apt`), I'll stop and ask first (CLAUDE.md).

## Consequences

- Item 1 closes the backlog's "public static serving" question one milestone early. M3 may still add versioned names.
- Item 2 adds one settings branch, and prod's cookie stays exactly as ADR 00 says.
- Items 3–5 fix the contract the local model's pairing-page tasks are written against.
