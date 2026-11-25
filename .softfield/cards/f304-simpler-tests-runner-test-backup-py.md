# Milestone F304: Backup tests use the shared fake clock and THURSDAY

> **State:** idea · **Area:** factory
> Planted by the owner on 2026-11-25.

## Notes
Simpler: tests/runner/test_backup.py keeps its own `fake_clock` fixture and `THURSDAY` constant, which repeat the ones now in tests/runner/conftest.py; drop them for the shared ones (about 12 lines). From F290's review.
