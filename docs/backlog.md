# Backlog

Nits from reviews and triaged discoveries that aren't scheduled yet. One bullet each: `- [source] description`.

<!-- e.g. - [m1-review nit] Rename `x` to `y` in coucou/ordering.py -->

- [m0] Public app static-file serving (needed in M3); decide the approach then, with no new dependency by default.
- [m0] Revocation watcher closing WebSockets within 2 s (M3); `AuthGeneration.bump()` already exists.
- [m0] Download Playwright browsers when the first client JS lands (M2/M3).
- [m0] Exercise the headless Claude paths live (escalation, review, usage-limit pause) during calibration.
- [owner, M5] Renaming a vault or space slug after photos exist splits the history folder in two. When the history folder is built (M5), make admin either warn and require confirmation, or move the existing folder (and update stored paths) inside the same save.
