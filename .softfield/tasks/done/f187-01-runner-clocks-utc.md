---
id: f187-01-runner-clocks-utc
milestone: f187-store-every-time-in-utc-the
difficulty: 4
agent: lead
files:
  - runner/loop.py
  - runner/owner.py
  - runner/cli.py
  - runner/backfill.py
  - runner/requests.py
  - runner/planner.py
  - runner/metrics.py
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_requests.py
---

### Goal
The runner stores every time in UTC and still shows local time wherever a person reads one.

### Context
Read `.softfield/cards/f187-store-every-time-in-utc-the.md` ("What we know", D1 to D4 and D6).
- The clocks: `now()` in `runner/loop.py`, `_now` in `runner/owner.py`, the `at` of the first card's thread in `runner/cli.py` (`datetime.now().astimezone().isoformat()`), and `_iso_ms`, `_iso_mtime` and a run's `started` in `runner/backfill.py`. Each returns or writes UTC (D1). `runner/cli.py`'s `today()` stays a local date (D4).
- Then every place in `runner/` that formats a time for a person converts it first with `.astimezone()`: search for `:%H:%M`, `%a %H:%M`, `strftime(` and `fromisoformat(` near text for the console, the run's report, desk items and planner context (for example `requests.py` "already paused, since …", `loop.py` "until …", `runner/planner.py`'s message times). Run folder names (`loop.py`, `f"{started:%Y%m%d-%H%M%S}"`) and backup file names stay local (D4).
- Say it once, in the docstring of `runner/metrics.py` ("Times are stored in UTC, as ISO-8601 with `+00:00`; shown in local time").
- Tests set the zone to `Europe/Paris` with `monkeypatch.setenv("TZ", …)` and `time.tzset()` (D6), and restore it.
- **Protected work: test-first.**

### Done when
- with the zone set to Paris, `loop.now()` has a zero UTC offset, and a job, a run, a usage event and a desk item written by a run store `+00:00`
- with the zone set to Paris, a pause stored at `08:00+00:00` answers "already paused, since 09:00", and a wait until `08:00+00:00` is logged as "until 09:00"
- a new run's folder is still named in local time
- `runner/metrics.py`'s docstring says times are stored in UTC and shown in local time
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
