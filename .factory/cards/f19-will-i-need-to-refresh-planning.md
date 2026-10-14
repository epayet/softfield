# Milestone F19: Will I need to refresh planning page when my questions get answered on planning

> **State:** ready · **Priority:** 1 · **Area:** factory
> Planted by the owner on 2026-10-07.

## Expected outcome
The lead's answer shows up on the Planning desk and on an open thread by itself, within about 5 seconds, without the owner reloading and without ever wiping what they are typing. The Overview makes one request every 5 seconds instead of four.

## Done when
- With `/planning/<card>` open, a new lead message appears in the conversation within a poll, and the desk on `/planning` moves the card to its new group.
- Text typed in the reply box, a point's comment or the plant form is never replaced by a refresh.
- The Overview's live parts (Needs you, Now, Queue, and the allowance once f9-28 lands) refresh from one `/live` request per 5 s.

## How to test
Open a thread on the phone, send a message, leave the page open: the lead's reply appears without a reload. Start typing a comment before it lands: the text stays.

## Notes
- **Polling, not SSE (the owner asked, 2026-10-07).** The dashboard's data is a SQLite file the runner writes from another process; nothing tells the dashboard it changed. An SSE stream would still check the database on a timer server-side, so it saves no work, only adds long-lived connections: uvicorn's reload waits on them, a phone drops them when it sleeps, and htmx needs its SSE extension. Answers take minutes to arrive; 5 s is plenty. Revisit SSE only if the dashboard ever needs sub-second updates or serves many viewers.
- **The real waste is duplicate polls:** the Overview's three wrappers (`#live-needs-you`, `#live-now`, `#live-queue`) each fetch the same `/live` every 5 s, plus the top bar's: four renders of the same page every 5 s. f9-28 adds a fifth. One request swapping every part out of band (`hx-select-oob`) fixes it: f19-02.
- **Pausing while typing:** `window.liveIdle()` in `factory_dashboard/templates/base.html` pauses on scroll and selection but not on typing. f19-01 extends it: no refresh while a text field is focused or holds unsent text.

## Tickets
| # | id | Who | Diff | After | What |
|---|----|-----|------|-------|------|
| 01 | planning-live | D | 4 | – | the desk and an open thread refresh every 5 s; `liveIdle` also waits while the owner types |
| 02 | one-live-poll | D | 3 | 01, f9-28 | the Overview's live parts come from one `/live` request |
