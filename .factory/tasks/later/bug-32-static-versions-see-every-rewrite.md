---
id: bug-32-static-versions-see-every-rewrite
milestone: bugs
difficulty: 2
depends_on: []
area: factory
priority: 60
finding: f48-F4
files:
  - factory_dashboard/app.py
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
A static file rewritten within the clock's grain still gets a new `?v=` version.

### Context
Read `def static` in `factory_dashboard/app.py` and its tests in `tests/factory_dashboard/test_app.py`.
- Today the hash is cached while the file's `st_mtime` (a float) is unchanged. Key the cache on `st_mtime_ns` and the file's size instead.

### Done when
- a file rewritten with different content of a different size and the same `st_mtime` gets a new version (set the time back with `os.utime(..., ns=...)` in the test)
- a file left alone keeps its version and isn't read again
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
