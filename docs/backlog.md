# Backlog

Nits from reviews and triaged discoveries that aren't scheduled yet. One bullet each: `- [source] description`.

<!-- e.g. - [m1-review nit] Rename `x` to `y` in coucou/ordering.py -->

- [m0] Public app static-file serving (needed in M3); decide the approach then, with no new dependency by default.
- [m0] Revocation watcher closing WebSockets within 2 s (M3); `AuthGeneration.bump()` already exists.
- [m0] Download Playwright browsers when the first client JS lands (M2/M3).
- [m0] Exercise the headless Claude paths live. Escalation: done in calibration (2 runs, Pro login, cap counted). Still untested: the review loop (M1 review) and the usage-limit pause.
- [owner, M5] Renaming a vault or space slug after photos exist splits the history folder in two. When the history folder is built (M5), make admin either warn and require confirmation, or move the existing folder (and update stored paths) inside the same save.
- [owner, before public launch] Decide the final product name. "Coucou" is taken by several apps (see [`brand/name-check.md`](brand/name-check.md)). Keep it, add a qualifier (e.g. "Coucou Home"), or rename, and run a trademark search first. Settle it before the logo is final and before the native Android wrapper (which needs a package ID).
