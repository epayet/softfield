# Milestone F38: The new-version notice becomes a tag on the top bar, so no page moves

> **State:** ready · **Priority:** 90 · **Area:** factory
> Planted by the owner on 2026-10-08.

## Notes
the refresh prompt causes layout shifting, i wonder if there's a way to subtely suggest that from the header perhaps, or is that getting crowded a bit

The owner, 2026-10-23: "Yeah that's the thing that suggest the refresh the page button" (the "New version of the dashboard: refresh" bar from app.py's `/version` poller).

## Outcome
When the dashboard's code changes, no page moves: a small "↻ New version" tag appears on the top bar's hazard stripe, and a page left in another tab or on a locked phone loads the new version by itself.

## Done when
- Open the Planning page, merge anything that touches `factory_dashboard/`: within 10 s a yellow tag shows on the right of the hazard stripe and the page under it doesn't move; tapping it loads the new version.
- Leave a dashboard tab in the background during a merge: coming back, it already shows the new version (unless a reply was half typed: then the tag waits).

## Decisions
- **D1 A tag on the stripe, out of the flow.** The notice is drawn over the hazard stripe (`position: absolute` in a relative wrapper), not in the bar's row: the row already holds the brand, the status, the project picker and the theme switch, and on a phone a new item there would wrap and move the page itself. Mock-up: [`f38-mockup/new-version-tag.html`](f38-mockup/new-version-tag.html).
- **D2 A hidden page reloads itself.** When the page isn't visible and `liveIdle()` says nothing is being typed or selected, it reloads; a visible page only shows the tag, so nothing changes under the owner's eyes.
- **D3 Same poll.** `/version` and its 10 s poll stay; only what it returns and where it sits change.
- **D4 A page that updated itself says so** (the owner, 2026-10-28: "I've left the page open through a few tickets being done and haven't seen the new tag at all"). On main, `/version` answers with the tag, but a page reloads itself whenever it comes back into view (D2 and the review's fix), so in normal use the tag is rarely seen and the update leaves no trace. After a reload the page started itself, "✓ Updated HH:MM" shows where the tag hangs for 15 s, in plate colours, not hazard yellow: it states a fact, there's nothing to press. Mock-up: [`f38-mockup/updated-note.html`](f38-mockup/updated-note.html).
- **D5 The blocked f38-02 lands through the lead, after a test's clock is mended** (2026-11-03). Its work passed everything except one test outside it: `fake_clock` in `tests/runner/test_loop.py` replaces `time.sleep` for the whole process, so `subprocess`'s own 1 ms wait moves the fake clock under load, and an assertion that the clock stood still fails by exactly 1 ms. f38-03 mends the fixture. f38-02 can't go back to a developer, who continues the branch: the escalation's note in `.softfield/developer.md` is on it, and the protected-paths gate would refuse it on every attempt. So it becomes a lead ticket that copies the finished work over from the kept branch.

## Tickets
| # | name | agent | difficulty | depends on | covers |
|---|------|-------|------------|------------|--------|
| 01 | new-version-tag | D | 3 | – | D1–D3 |
| 02 | updated-note | L | 2 | 03 | D4, D5 |
| 03 | fake-clock-ignores-subprocess | D | 2 | – | D5 |
