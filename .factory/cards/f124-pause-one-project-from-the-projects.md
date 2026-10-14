# Milestone F124: Pause one project from the Projects page

> **State:** idea · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-14.

## Notes
From the terminal session of 2026-10-14 that built ADR 30 (sessions B, C, D).

The database already has a pause per project (`projects.paused`, metrics V13) and the runner
skips a paused project (`cli._project_configs`); `softfield init` uses it while a project is
set up ("setting up", released by `softfield doctor`). Nothing on the dashboard sets it.

Give each project a Pause / Resume on the Projects page, as a request shown as on its way until
the runner takes it (owner.md, 2026-10-07). For when one project should wait while another runs,
without pausing the whole factory. Today "Pause after this job" on a project's Overview pauses
every project's tickets (a pause in any project holds every ticket, ADR 30 session D).
