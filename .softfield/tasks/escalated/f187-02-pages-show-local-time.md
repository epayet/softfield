---
id: f187-02-pages-show-local-time
milestone: f187-store-every-time-in-utc-the
difficulty: 3
files:
  - factory_dashboard/queries.py
  - factory_dashboard/app.py
  - factory_dashboard/overview.py
  - factory_dashboard/board.py
  - factory_dashboard/line.py
  - factory_dashboard/coming.py
  - tests/factory_dashboard/test_queries.py
tests:
  - tests/factory_dashboard/test_queries.py
---

### Goal
Every dashboard page shows a stored time in local time, whatever offset it was stored with.

### Context
Read `.softfield/cards/f187-store-every-time-in-utc-the.md` ("What we know", D3 and D6).
- Add `local(at: str | datetime | None) -> datetime | None` to `factory_dashboard/queries.py`: it reads a string with `datetime.fromisoformat`, treats a naive value as UTC (as `_when` in `factory_dashboard/line.py` does), and returns it with `.astimezone()`; None gives None.
- Use it wherever a page prints a clock time or a date from a stored time: `_clock` in `factory_dashboard/app.py`, the `strftime("%H:%M")` in `factory_dashboard/overview.py` (around line 82), `factory_dashboard/board.py`'s "since …" date, and the `_when` copies in `line.py` and `coming.py` (they may call it). Places that already call `.astimezone()` can stay.
- Nothing on screen should change today (UK winter time is UTC); the test makes the difference show by setting the zone to `Europe/Paris` with `monkeypatch.setenv("TZ", …)` and `time.tzset()`, restored after.

### Done when
- with the zone set to Paris, `local("2026-10-29T08:00:00+00:00")` and `local("2026-10-24T09:00:00+01:00")` give 09:00 and 10:00 local, and `local(None)` gives None
- with the zone set to Paris, the top bar's paused time for a pause stored at `08:00+00:00` reads 09:00
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: mypy)
attempts: 3
tokens: 2016898
logs: .softfield/var/runs/20261102-221022/f187-02-pages-show-local-time
```
