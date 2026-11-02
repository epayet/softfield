# Working on Softfield's code

For anyone, with any agent or none. You don't need the factory to work here.

## Code
5. Keep rules as plain functions without side effects where practical: time and paths are parameters; git, SQLite, subprocesses and HTTP stay at the edges (`runner/loop.py`, `runner/gitops.py`, `runner/metrics.py`, the dashboard's routes).
6. Type-hint everything. Code must pass ruff (lint + format) and mypy.
7. No third-party network calls, CDNs, fonts, analytics or trackers in the dashboard. Every asset is self-hosted (`factory_dashboard/static/vendor/`).
8. The dashboard writes only through `POST /requests` (ADR 18); the runner is git's one writer.

## Tests
9. **One test file per module:** `runner/<name>.py` → `tests/runner/test_<name>.py`, `factory_dashboard/<name>.py` → `tests/factory_dashboard/test_<name>.py`. Add to the existing file; never create a second one. Tests use temporary git repos and databases, never the real ones.
10. Write tests for what the task's "Done when" asks. They must fail without your change and pass with it.
11. Change an existing test only when the task changes that behaviour. Never skip, xfail or delete a test to make it pass.
12. A task is done when its `tests:` pass **and** the full suite still passes (`softfield check-all`).

## Reading further
How the factory works: `docs/how-it-works.md` and `docs/workflow.md`.
