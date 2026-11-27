# Milestone F304: Backup tests use the shared fake clock and THURSDAY

> **State:** done · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-27. Base: git tag `f304-simpler-tests-runner-test-backup-py-start`. Report: [`.softfield/reviews/f304-simpler-tests-runner-test-backup-py.md`](../reviews/f304-simpler-tests-runner-test-backup-py.md).
> Planted by the owner on 2026-11-25.

## Notes
Simpler: tests/runner/test_backup.py keeps its own `fake_clock` fixture and `THURSDAY` constant, which repeat the ones now in tests/runner/conftest.py; drop them for the shared ones (about 12 lines). From F290's review.

## Plan
One developer ticket, tests only: `f304-01-backup-tests-use-shared-clock`. Nothing on screen, so no mock-up.
