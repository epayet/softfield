# Milestone F125: Projects page: say what runs next

> **State:** idea · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-14.

## Notes
From the terminal session of 2026-10-14 that built ADR 30 (sessions B, C, D).

The Projects page's Now panel says what runs now in any project, or "Nothing runs now". The
mock-up (.factory/cards/f120-many-projects-mockup/projects.html) also had a Next line across
projects, in the owner's order: "Next: Softfield's f15-02 once F110 merges; Coucou has nothing
ready". It was left out of D. `softfield run --dry-run` already knows it per project
(`loop.dry_run_plan`, `dispatch.plan`); the page needs the first runnable item across projects,
with why the higher ones wait (Claude's pace, a dependency).
