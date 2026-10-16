# Milestone F17: Tighter running and pause presence in menu

> **Status: done.** Signed off by the owner on 2026-10-16. Base: git tag `f17-tighter-running-and-pause-presence-in-start`. Report: [`.factory/reviews/f17-tighter-running-and-pause-presence-in.md`](../reviews/f17-tighter-running-and-pause-presence-in.md).
> Planted by the owner on 2026-10-07.

## Notes
I don't need to see the name of the task, just a pointer that tells me if it's doing a job or not. Perhaps just a green dot? Space is small on mobile, maybe on desktop there's more space for more info. 
The color of the thing saying it's doing something should depend on whether it's lead or dev (orange or blue)   
The pause button should be just a sign, rather than PAUSE and then a play button

## Outcome
- The top bar's status is a dot: orange while the lead (or any Claude job: checkpoint, review, the planner) is on a job, blue while a developer is, grey with no job; an orange ring while waiting for Claude, a grey ring when stopped.
- Pause and Resume are a sign, ⏸ or ▶, with a 44 px target and their words for screen readers.
- On a phone the dot and the sign sit beside the brand: the bar loses a row. Tap the dot for its words. On a wide screen the words stay beside the dot.
- What the owner asked still shows at once, on its way (the dashed orange edge).

The picture: [`f17-mockup/top-bar.html`](f17-mockup/top-bar.html).

## Not here
- The Overview's own Pause or Resume and its state after a resume: F29.
- Pausing leaving planner jobs alone: F27 (today a planner job already runs while paused, and the dot shows it orange).

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | status-dot-and-sign | D | 4 | – | the dot (whose job, or none) and the ⏸ or ▶ sign; phone: one row, words on a tap |
