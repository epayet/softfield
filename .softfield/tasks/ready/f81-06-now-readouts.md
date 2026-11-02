---
id: f81-06-now-readouts
milestone: f81-assess-the-current-ui-state-of
agent: developer
difficulty: 2
depends_on: [f81-02-square-parts]
files:
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/templates/_partials/running.html
  - factory_dashboard/templates/_partials/queue.html
tests:
  - tests/factory_dashboard/test_app.py
  - tests/factory_dashboard/test_overview.py
---

### Goal
On the Overview, a running job's numbers read as readouts on a plate, the Queue's count is one big number, and Next in line is a row of crates edged in the floor's lead or developer colour.

### Context
Build Now and the Queue of the Proposed side of `.softfield/cards/f81-mockup/theme-pass.html` (`.readouts`, `.readout`, `.count`, `.belt`); card doc `.softfield/cards/f81-assess-the-current-ui-state-of.md` D3.
- `factory_dashboard/templates/_partials/running.html`: the job's `dl.kv` (Elapsed, Live, Heartbeat, Waiting, Difficulty) becomes `.readouts`, one `.readout` per fact: the number in the display face with its unit, the fact's name under it. A Waiting line stays words (it has no number).
- `factory_dashboard/templates/_partials/queue.html`: the "N tickets waiting" line becomes `.count`; the rows of Next in line become an `ol.belt`, each `li` classed `lead` or `developer` from the ticket's kind (the colours `.swatch.lead` and `.swatch.developer` use, which the floor's legend explains); queued jobs and batches keep the plain edge. Keep every link, word and number the rows show today, whatever the partial shows when this runs.
- The ids `#now` and `#queue` and the `/live` poll stay as they are.

### Done when
- a running job shows Elapsed, tokens read and Heartbeat as readouts; a waiting job shows its words
- the Queue shows its count large and Next in line as rows edged by who does the ticket
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
