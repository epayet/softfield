# Milestone F9: line polish

> **Status: done.** Signed off by the owner on 2026-11-10. Base: git tag `f9-line-polish-start`. Report: [`.softfield/reviews/f9-line-polish.md`](../reviews/f9-line-polish.md).
> The owner's notes from using the line on 2026-10-04, plus five of f3-22's proposals they confirmed (f3-25, f3-28, f3-29, f3-30, f3-31, re-homed here with their ids). Developer tickets, each a small change on the lead-written line (F3's lesson: no SVG geometry for developers); 01 is the lead's.

## Outcome
- The floor shows when the line is clogged, and on what (a limit, the owner, a parked job).
- Light mode reads well: planted rows and the floor's yellow bars on grey.
- Planted rows open their milestone; seeds open the set-aside tickets.
- Idle machines look idle and say what they did today; plates show a bare one-decimal rating.
- Phone allowances are one row of dials.
- The Timeline's milestone filter works; the Set aside table shows each ticket's kind.

## Not here
- Crates moving along the belts (the F1 mock-up's motion) and a workflow page on the dashboard: `docs/roadmap.md`, after F8, since the crates should carry every kind of job.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | line-shows-waits | L | 4 | – | the floor shows a clog sign, with words, while the runner waits |
| 02 | light-floor | D | 2 | – | planted rows' words and the floor's bars readable in light mode |
| 03 | field-links | D | 3 | – | a planted row opens its milestone; the seeds open the Set aside panel |
| 04 | timeline-milestone-filter | D | 2 | – | the Timeline's milestone filter, "All milestones" included |
| 05 | later-kind-column | D | 2 | f5-09 | the Set aside table: Kind instead of the queue command |
| f3-25 | allowance-dials | D | 4 | – | (re-homed) phone allowances as dials |
| f3-28 | floor-words | D | 2 | – | (re-homed) bare one-decimal ratings, no "rated" |
| f3-29 | machine-today | D | 4 | – | (re-homed) idle machines say what they did today, and look idle |
| f3-30 | phone-top-bar | D | 3 | – | (re-homed) the phone's top bar in two short lines |
| f3-31 | replay-bar-when-replaying | D | 2 | – | (re-homed) the phone's replay bar sticks only while replaying |
| 08–09 | (stand-in fixes) | D | – | – | Copilot's code findings on f3-30 and f3-29; its test-only findings wait in `.softfield/tasks/later/`: f8-09 made 06, 07, 10 and 11 `tests_only` developer tickets (11 holds 12's finding too, so 12 goes) |
| 13 | home-without-clog-and-verdict | D | 2 | – | the Overview drops the clog and Last verdict panels (owner, 2026-10-06) |
| 14 | away-span-in-place | D | 4 | – | choosing a stretch redraws While you were away without a reload |
| 15 | away-who-did-it | D | 4 | – | each ticket while away: who did it, in how many attempts, lead ticket or finished; the blocked ones named (owner, 2026-10-07) |
| 16 | no-ollama-allowance | D | 2 | – | the allowance panel drops the Ollama row (no data, ever) |
| 17 | phone-allowance-bars | D | 3 | – | rewritten (owner, 2026-10-06): phone allowances back to bars, green to red; the dials and their colour fix go |
| 21 | milestones-in-order | D | 3 | – | Milestones: in progress, then not started by priority, then done, latest first |
| 22 | floor-words | D | 4 | – | belt counts say "today", Planting says what it is, a blue developer bay, the faded crates in the legend, no refresh note, savings "so far" |
| 23 | floor-taps | D | 3 | 22 | merged crates, the lead's next ticket, stash tiles (short keys), Planting and ripe lines open what they name |
| 24 | tap-sheet | D | 3 | 23 | on a phone the crate card is a bottom sheet with Close |
| 25 | seeds-and-planting | D | 4 | 24 | Planting counts cards in talks (it was a hard-coded 0); the seeds open the sheet listing set-aside tickets |
| 26 | replay-under-floor | D | 2 | 13 | the replay bar right after the floor |
| 27 | phone-rows-compact | L | 4 | 25 | the phone's planted rows: 3 compact rows and "Show all N" |
| 28 | allowance-live | D | 3 | 16 | the allowance panel refreshes live, its legend at the bottom; the lead window shows the week too (owner, 2026-10-07) |
| 29 | week-pace | L | 3 | 28 | Claude's week meter shows today's pace line and says "on pace" or "over pace: lead tickets wait"; a held lead ticket's row in Next in line says until when (owner, 2026-10-07 and F116 2026-10-27; mock-up `f9-mockup/week-pace.html`) |

**The owner's notes of 2026-10-06** (from using the line on the phone) are 17 and 21–27. Crates moving along the belts went to [F10](f10-crates.md).

## Notes
### From F64: I like to see the list of tickers that got done while I… (merged by the lead on 2026-10-09)
I like to see the list of tickers that got done while I was away. Now I also want to see how long each task take, what time it got done, number of attempts. Like a mini report. It also.says who merged it, what does that mean?

### From F116: I want to be able to visualise when the claude pacing… (merged by the lead on 2026-10-27)
I want to be able to visualise when the claude pacing happens somehow
