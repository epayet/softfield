# Review: F269, the 200-jobs test writes its jobs in one transaction

- **Status:** done, signed off by the owner on 2026-11-20.

## Sign-off sheet

### 1. What changed
- `write_more_jobs` in `tests/factory_dashboard/conftest.py` now writes its 205 jobs inside one `BEGIN IMMEDIATE` … `COMMIT`, and rolls back on an error, the same way `set_board_order` does.
- The setup of `test_more_than_200_jobs_shows_200_and_count` went from about 13 s to under 0.52 s. It no longer appears in the file's five slowest setups.

### 2. How to test it yourself
1. Run `uv run pytest -q tests/factory_dashboard/test_jobs.py --durations=5`.
2. All 13 tests pass, and `test_more_than_200_jobs_shows_200_and_count` is not in the slowest five (each of those is about 0.5 s).

### 3. Done when, as of now
- **Met:** the loop is wrapped in one `BEGIN IMMEDIATE` … `COMMIT`, with a rollback and re-raise on any exception, as in `set_board_order`.
- **Met:** the signature, the docstring and the rows written are the same, and `runner/metrics.py` was not touched.
- **Met:** the test passes unchanged, and its setup is under 1 s (measured by the review). The commit message doesn't quote the before and after times the ticket asked for.
- **Met:** no other fixture or test changed, and the gates passed.

### 6. What next
- **Product:** product work is on hold; nothing to suggest.
- **Factory:**
  - Run serially, `uv run pytest -q tests/runner tests/factory_dashboard` hangs for over 20 minutes. It stops just before the Chromium tests in `test_overview.py`, which pass when that file runs alone. The gates run in parallel (`-n`), so they never see this.
    > Run in one process, `uv run pytest tests/runner tests/factory_dashboard` hangs at about the 61% mark, just before `test_overview.py`'s Chromium tests, though that file passes alone: find which earlier test leaves something open (an event loop, a server, a browser) and close it, so a plain pytest run finishes.

### 8. How the work went
- The developer again didn't report the before and after times the ticket asked for (F270 had the same gap), so the review measured them itself. The F270 sign-off already suggests a gate for this, and this milestone adds a second case for it.

<!-- runner report -->
<!-- /runner report -->
