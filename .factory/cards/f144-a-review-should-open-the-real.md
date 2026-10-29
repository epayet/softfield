# Milestone F144: A review reads the real page and real data before the tests

> **State:** ready · **Priority:** 4 · **Area:** factory
> Planted by the owner on 2026-10-16.

## Notes
A review should open the real page with `softfield look page` before reading the tests: it is the cheapest check against tests built on tidy data (F109's lesson, again here).

## Plan (lead, 2026-10-27)
- Why: four reviews in a row (F109, F94, F30, F158) found their worst bug on real data, not in the tests, each because the reviewer happened to look. The review's brief only says `look` exists (ADR 28 item 5: on demand).
- Decisions: [ADR 37](../adr/37-a-review-reads-the-real-page-first.md) (Proposed). A review whose milestone changed a factory page opens it with `softfield look page` (text and raw HTML) before the tests, compares one fixture of each new test file with a real record, and names both in its report. Reviews only; checkpoints and planners unchanged.
- Tickets: `f144-01-review-reads-the-real-page` (lead: the review brief and the lead's "Review" section; no developer ticket, it's prompt text and its test). It waits for ADR 37 to be accepted.
