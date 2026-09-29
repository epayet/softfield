# ADR 08: WebKit in the end-to-end tests

- **Status:** Accepted (by the owner, 2026-09-29, option 1: WebKit installed; e2e runs in Chromium and WebKit)
- **Date:** 2026-09-29
- **Deciders:** project owner (accepts), Claude (drafts)

## Context

ADR 00 (testing), `docs/testing.md` and M3's C7 / "done when" say the e2e tests run in **Chromium and WebKit**. The M3 e2e test (`tests/e2e/test_display.py`) has only run in Chromium: only `chromium-1243` is in `~/.cache/ms-playwright/`. WebKit needs `playwright install-deps` (apt, sudo), and CLAUDE.md doesn't allow Claude to install system packages without asking.

The finding (m3-F7) was sent to the backlog in rounds 1 and 2. The runner counts it as recurring, so it keeps coming back to review. It won't resolve until the owner decides, so it needs a decision rather than another round.

## Options

1. **Install WebKit on this machine.** The owner runs `uv run playwright install-deps webkit` (sudo) and `uv run playwright install webkit`. Then `uv run pytest -m e2e --browser chromium --browser webkit` on staging. The test is browser-agnostic already, and the cookie question (ADR 03, `__Host-` on `http://localhost`) gets checked for real. Cost: a few hundred MB of system libraries on the dev box.
2. ⚑ **Chromium only in e2e; iOS is covered by the real-iPhone check.** This amends ADR 00 and `docs/testing.md`: WebKit on Linux is "a rough stand-in for iOS Safari, *not* a substitute" (ADR 00), and the real-device checks at sign-off are what matter. Cost: iOS-only bugs (Wake Lock, IndexedDB, service worker quirks) show up later, on a real phone.
3. ⚑ **Defer.** Accept M3 with Chromium only and do option 1 or 2 before the first milestone that ships the phone app to iPhone users.

## Recommendation

Option 1 if the owner is fine with the system packages. It's one command, and the test is already written. Otherwise option 3, noted in M3's sign-off.

## Consequences

- Option 1: m3-F7 is resolved once a WebKit run on staging passes. Claude updates `docs/reviews/m3.md` and removes the backlog entry.
- Option 2: Claude edits `docs/testing.md`, `docs/milestones/m3.md` and the test's docstring, and the backlog entry goes.
- Option 3: the backlog entry stays, with the milestone named, and review no longer counts m3-F7 as open for M3.
