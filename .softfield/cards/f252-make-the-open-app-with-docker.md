# Milestone F252: The app's Open button on the Projects page opens a new tab

> **State:** done · **Priority:** 100 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-17. Base: git tag `f252-make-the-open-app-with-docker-start`. Report: [`.softfield/reviews/f252-make-the-open-app-with-docker.md`](../reviews/f252-make-the-open-app-with-docker.md).
> Planted by the owner on 2026-11-16.

## Notes
make the open app with docker button in project page open in a new tab instead

## Plan

One developer ticket, `f252-01-open-in-a-new-tab`: the app row's Open link (`factory_dashboard/templates/_partials/app_row.html`) gets `target="_blank" rel="noopener"`, like the milestone page's live links. This reverses F239's "same tab" (f239-05); Logs stays in the page. No mock-up: nothing on screen changes, only where the press lands.
