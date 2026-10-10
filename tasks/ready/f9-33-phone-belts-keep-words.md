---
id: f9-33-phone-belts-keep-words
milestone: f9-line-polish
depends_on: []
difficulty: 3
files:
  - factory_dashboard/static/factory.js
tests:
  - tests/factory_dashboard/test_line.py
finding: f9-32-fix-phone-belt-words
priority: 40
area: factory
---

### Goal
On the phone, `queue→developers` reads "developer · N today", `lead→checks` reads "lead's work · N today" and `checks→lead` reads "back to the lead · N today"; only belts that were bare numbers before f9-22 read "N today".

### Context
Read `belt` and `PHONE_BELTS` in `factory_dashboard/static/factory.js` and `test_a_phone_draws_every_station_with_its_crates_and_belts` in `tests/factory_dashboard/test_line.py`.
- f9-32 was asked to restore every `PHONE_BELTS` entry's `short` to its pre-f9-22 value (`git show e60c3f49b -- factory_dashboard/static/factory.js`). It removed `short: true` from `checks→merged` only. f9-22 had added `short: true` to `queue→lead`, `queue→developers`, `lead→checks`, `checks→developers`, `checks→lead` and `merged→reviewers` too, and they still have it, so a `short` belt with a `say` word drops that word: `queue→developers` says "7 today", not "developer · 7 today".
- Before f9-22 only `seeds→planting` was `short`.
- The phone tests check `checks→merged` and `seeds→planting` only; no test fails for the other belts.

### Done when
- on the phone, `queue→developers`, `lead→checks` and `checks→lead` read their `say` word, " · N today"; `seeds→planting` still reads "N today"
- every other `PHONE_BELTS` entry is as before f9-22 (`short` only on `seeds→planting`), and a test per belt with words checks its text from the document's count
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
