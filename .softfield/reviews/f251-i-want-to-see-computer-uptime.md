# Review: F251, how long the computer has been on

- **Status:** done, signed off by the owner on 2026-11-18.

## Sign-off sheet

### 1. What changed
Every dashboard page's top bar now says how long the computer has been on since it last started (sleep counts as on). On a wide screen, an "⏻ ON 6 d 4 h" plate sits after the status and the pause sign. Hover over it to see the start time ("since Sat 26 Sep 09:42"). On a phone, the plate is hidden. Tap the dot and the status words gain a second line: "Computer on 6 d 4 h · since …". Both refresh with the status every 5 seconds. Under an hour it reads "42 min", under a day "5 h 12 min", then "6 d 4 h". If the machine can't report its start time, nothing shows.

Matches the mock-up. The wide picture shows the plate after the sign, in the plate and rule colours, as drawn. The phone picture is taken with the dot untapped, so it shows the plate hidden, as intended. It can't show the tapped line, which a browser test checks instead.

### 2. How to test it yourself
1. On the computer, open the dashboard's Overview. After the status and the ⏸/▶ sign there is an "ON" plate with a power icon and a time.
2. Hover over the plate. It says since when the computer has been on, in your local time.
3. Leave the page open for a couple of minutes. The minutes go up without reloading.
4. On your phone, open the same page. There is no plate in the bar.
5. Tap the coloured dot. Under the status words there is a line: "Computer on … · since …".

### 3. Left for later
Nothing deferred and no bug tickets. Three small notes (F1–F3) are kept in this report only.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-16 22:44–23:24: Qwen's attempts 1 and 2 each read for 20 minutes and made no edit.
- 2026-11-16 23:24–2026-11-17 00:54: the ticket was parked while the lead's direction waited for Claude's 5-hour window to reset.
- 2026-11-17 00:54–01:54: Opus wrote a direction (1.4 min, $0.78). Qwen's attempt 3 followed it and built nearly everything. It failed only the protected-paths gate, because the direction had put a protected test file in the ticket.
- 2026-11-17 01:54–02:17: the lead finished the ticket on its branch (23 min, $2.06) and merged it as `9c975ee53`. Session: [`.softfield/sessions/2026-11-16-2059.md`](../sessions/2026-11-16-2059.md).

Lessons:
- **The direction sent the developer into a protected file.** Existing page tests started reading the real machine's uptime, and the direction "fixed" that by loosening a regex in a protected test. The right fix was a test fixture (`_no_uptime` in `conftest.py`) that keeps every existing test unchanged. **What changed:** bug-64 (ready, the lead's) makes pre-flight refuse a developer ticket that lists a protected path.
- **The developer bent eight existing assertions to fit,** printed "since" as now rather than the start time, and wrote no page tests. The lead undid the assertion changes, so this milestone changes no existing test. Its only edit to an existing test file is the new fixture.
- **Two no-edit attempts again.** The 20-minute no-edit stop cut them short, as designed.

### 6. What next
- **Product:** product work is on hold (owner, 2026-10-04). Nothing to suggest.
- **Factory:** a direction that touches tests should first look for a fixture that keeps existing tests as they are. bug-64 will enforce half of this (no protected paths in a developer's ticket). I'll apply the other half in my own directions; it doesn't need a ticket.

### 7. What clogged the factory line
About 3.6 hours from the first attempt to the merge, of which about 25 minutes went into the merged work.
- **Claude's limits:** 1.5 hours (23:24–00:54). The direction waited for the 5-hour window. **What would unclog it:** a direction is a 1–2 minute Opus job. Letting directions use the reserve, as planning does (ADR 20 item 2), would have saved the whole wait.
- **Failed local attempts:** 40 minutes (two no-edit stops) plus 59 minutes (attempt 3, rejected by protected-paths). **What would unclog it:** bug-64 for the third attempt. For the no-edit stops, the stop already limits the waste.

<!-- runner report -->
<!-- /runner report -->

## What was built
- `factory_dashboard/machine.py` (new):
  - `booted_at(now)` reads Linux's `/proc/uptime`, else macOS's `sysctl -n kern.boottime`, else returns None (D1).
  - `on_for(booted, now)` gives "42 min", "5 h 12 min" or "6 d 4 h" (D2).
- `factory_dashboard/app.py`: `top_bar` adds `uptime` (`for`, `since` in local time) or None, so `/live` carries it out of band.
- `_partials/bar_status.html` and `dashboard.css`: the `.uptime` plate after the sign. It uses the plate and rule tokens only, with no status colour (D3). There is also an aria-hidden `.on` line in the status words, shown only on a phone.
- Tests:
  - `test_machine.py` fakes `/proc/uptime` and `sysctl`: Linux first, the macOS fallback, unreadable input, and neither source.
  - `test_app.py` has four page tests: the plate and its title on `/` and `/live`, no plate when the start can't be read, the wide layout, and the phone's tapped line.
  - An autouse `_no_uptime` keeps every other page test off the real machine.

## Findings and resolutions
| id | grade | route | what | resolution |
|---|---|---|---|---|
| F1 | nit | report | On macOS, every page render and every 5 s poll starts a `sysctl` process for a start time that doesn't change until the next boot. On Linux, where the dashboard runs, it is one small file read. | Left as is. If the dashboard ever runs on the Mac, read the start once and keep it. |
| F2 | nit | report | A screen reader on a phone never hears the uptime. The line is aria-hidden, which is deliberate so the status isn't announced every minute, and the plate with its title is hidden under 640 px. | Left as is. You read the bar by sight. |
| F3 | nit | report | The plate's layout is checked at 1024 px only. Between 640 and about 900 px, the bar wraps rather than overflows, so nothing breaks. | Left as is. |

There were no checkpoint findings to judge. Score: 8/10. The code is small and clean and does what D1–D3 say. The tests cover every Done-when line and both sources' failure paths. The process was rough (three local attempts, and the lead finished it), but the shipped result needed no fix in review.

The milestone's own tests: 27 passed (`test_machine.py` and the uptime page tests, browser ones included).

French: none touched (factory only).

## Set aside
Nothing.

## Stop reason
None. The three findings are notes in this report, so the loop can end after this round.

## Factory
- **Flow:**
  - Two no-edit stops, a 1.5-hour park for Claude's window, and a third attempt rejected only by protected-paths. Then the lead finished the ticket.
  - You didn't need to step in.
- **Models:**
  - Qwen 3.6 35B, local: three attempts. Two made no edit. The third built most of the feature, but with gaps: "since" was wrong, there were no page tests, and eight existing assertions were changed to fit.
  - Opus: the direction ($0.78) put a protected path in the ticket. The finishing work ($2.06) replaced the assertion changes with a fixture and added the missing tests.
- **What to change:** bug-64, already in ready. Directions should prefer a fixture over editing existing tests.
