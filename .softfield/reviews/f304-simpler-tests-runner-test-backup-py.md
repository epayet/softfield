# Review: F304, Backup tests use the shared fake clock and THURSDAY

**Status:** review done after round 1, with no findings; ready for your sign-off.

### 1. What changed
- `tests/runner/test_backup.py` no longer has its own copy of the `THURSDAY` date and the `fake_clock` fixture. It uses the shared ones in `tests/runner/conftest.py`, so 16 lines are gone and there is one fake clock to maintain.
- The runner itself is unchanged. All 20 backup tests keep their names and pass. The shared clock also keeps `subprocess` on the real sleep, which the old copy didn't.

### 2. How to test it yourself
1. On the dashboard, open this milestone's run and check that its one ticket merged on the first attempt with every gate green.
2. Nothing else changes on screen or on your devices. This is test-only work.

### 3. Done when, as of now
- **Met:** `tests/runner/test_backup.py` defines neither `THURSDAY` nor `fake_clock`.
- **Met:** all 20 tests in the file pass under the same names as before (the review ran them again).
- **Met:** every gate passed at the merge, and ruff is clean on the file.

### 8. How the work went
- The local model did a small, exact Simpler ticket from an example in the code in 6 minutes, on its first attempt, with no Claude spend. Tickets this size and shape suit it well.

<!-- runner report -->
<!-- /runner report -->
