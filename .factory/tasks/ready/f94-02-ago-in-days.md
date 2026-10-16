---
id: f94-02-ago-in-days
milestone: f94-opus-f9-25-seeds-and-planting
finding: f94-opus-f9-25-seeds-and-planting-F3
depends_on: [f94-01-away-row-facts]
difficulty: 1
priority: 0
files:
  - factory_dashboard/app.py
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
How long something took or has run reads in days from 48 hours on: "took 5.9 days", not "took 142.2 h".

### Context
`ago` in `factory_dashboard/app.py` writes "30 s", "3 min" and "2.6 h", and stops at hours. F94 uses it for "took" under While you were away, where a ticket parked for a week read "took 142.2 h" on 2026-10-16 (f17-01-status-dot-and-sign). The tickets page's "last worked … ago" uses it too, and gains the same.
- From 48 h on, write the days with one decimal, the same way the hours are written: "5.9 days", and "2 days" rather than "2.0 days".
- Below 48 h nothing changes: "36 h" stays "36 h".
- Change only `ago`; no template changes.

### Done when
- `ago(timedelta(hours=142.2))` is "5.9 days"; `ago(timedelta(hours=48))` is "2 days"; `ago(timedelta(hours=47))` is "47 h"; `ago(timedelta(minutes=58))` is "58 min"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
