---
id: f86-02-your-time-on-reports
milestone: f86-idea-tracking-time-the-human-spent
difficulty: 4
depends_on: [f86-01-owner-time-numbers, f59-02-reports-page]
files:
  - factory_dashboard/reports.py
  - factory_dashboard/templates/reports.html
  - factory_dashboard/static/dashboard.css
  - tests/factory_dashboard/test_reports.py
tests:
  - tests/factory_dashboard/test_reports.py
---

### Goal
The Reports page shows the owner's time: two tiles, a "Where your time went" panel, and the owner's part of each week's bar in "Hours worked, by agent".

### Context
Read `.factory/cards/f86-idea-tracking-time-the-human-spent.md` (D6) and build the Proposed of the mock-up, `.factory/cards/f86-mockup/your-time.html`.
- The numbers are `Week.owner` and `series` in `factory_dashboard/reports.py` (f86-01).
- Follow the page's own sections in `factory_dashboard/templates/reports.html` (f59-02): the tiles of The week in numbers, the plate-headed panels, the graphs through `data-chart` as they are drawn there.
- Add the token `--owner: var(--fg);` beside the agent colours at the top of `factory_dashboard/static/dashboard.css`, in the dark theme's `:root` (the light theme's `--fg` follows by itself), and use only it for the owner's bars.

### Done when
- The week in numbers ends with "Your time" (hours, and the week before's) and "Waited for you" (median hours, the number of items, and the week before's); a week with none resolved says "nothing waited"
- "Where your time went" shows the top 6 cards by minutes, each with its key and title, then "Everything else"; under it the sittings, the days and the actions by kind
- the panel says "Counted from your presses on the dashboard; terminal sessions are not included"
- each week's bar in "Hours worked, by agent" has an owner part in `--owner`, named in its key; a week before 7 Oct has none and its key says "not recorded"
- `?scope=<project>` shows that project's time and cards only
- on a 390 px wide screen nothing scrolls sideways that didn't before
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
