# F9 line polish: review

- **Status:** done, signed off by the owner on 2026-11-10.

## Sign-off sheet

### 1. What changed
The factory floor on the Overview reads better, on a phone especially:
- **The floor says when the line is clogged, and on what:** a clog sign with words on the queue or the machine that waits (a limit, you, a parked job).
- **Light mode reads well:** the planted rows' words and the floor's yellow bars stand out on grey.
- **Taps go somewhere:** a planted row opens its milestone; the seeds, a merged crate, the lead's next ticket, Planting and the ripe lines open what they name. On a phone a crate's card is a bottom sheet with Close; the seeds' sheet lists the set-aside tickets.
- **Machines:** an idle one looks idle and says what it merged today; plates show a bare rating ("4.2", no "rated"); the developer bay is blue.
- **Words on the floor:** belt counts say "today", Planting says what it is and counts the cards you're talking over (it was always 0), the faded crates are in the legend, savings say "so far".
- **Phone:** the top bar's title and project filter share one line; the planted rows show the three busiest with "Show all N"; the belts keep their words; the replay bar sits right under the floor.
- **The Overview:** no clog or Last verdict panels; choosing a stretch redraws While you were away in place, and each ticket there says who did it, in how many attempts, lead ticket or finished, with the blocked ones named.
- **Allowance:** back to bars, green to red, no Ollama row, refreshing live with its legend at the bottom; Claude's week shows today's pace as a dashed post, the stretch used beyond it striped, and says "on pace" or "Over pace: lead tickets wait until about …". A held lead ticket's row in Next in line says until when.
- **Elsewhere:** the Timeline's milestone filter works ("All milestones" too); the Set aside table shows each ticket's kind; the Milestones page lists in progress, then not started (by board order), then done, newest first.

No mock-up pictures were attached to this review.

### 2. How to test it yourself
1. On your phone, open the Overview. The title and project filter sit on one line; the floor shows at most three planted rows and "Show all N" opens the rest (and stays open through the 5-second refresh).
2. Tap a planted row: its milestone opens. Go back, tap the seeds: a sheet lists the set-aside tickets, with Close. Tap a merged crate: its card comes up from the bottom.
3. Check the idle machines say "idle" and "N merged today", and the lead's "next: …" sits inside its machine.
4. Scroll to the allowance: bars, no Ollama. If Claude's week is past today's pace you'll see the striped stretch and the Over pace plate, and Next in line's lead row says "waits for Claude's week pace until about …".
5. Switch to light mode (the theme button): the planted rows and yellow bars are readable.
6. Open Replay right under the floor: its controls are big enough to tap.
7. On a computer: the Timeline's milestone filter narrows the list; Tickets › Set aside has a Kind column; Milestones lists the cards in the order above.

### 3. Left for later
- Test-only fixes set aside by Copilot's checkpoints: `f9-06`, `f9-07`, `f9-10`, `f9-11` in `.softfield/tasks/later/` (the card says f8-09 made them developer tickets; they still wait there). `f9-12` duplicates `f9-11` and can go.
- Two test fixes queued from this review: `f9-35` (While you were away labels) and `f9-36` (the lead's next-link position).

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-04 to 10-10: most of the card, in many night runs: about 28 developer tickets by Qwen, nine of them fix tickets from Copilot's and Sonnet's checkpoints; three finished by Opus (f9-08, f9-30, f9-25). Session reports: `.softfield/sessions/`.
- 2026-10-13: f9-01 (the clog sign), lead ticket on Opus, first time.
- 2026-11-10: f9-29 (week pace) and f9-27 (phone rows), lead tickets on Sonnet, first time each, after f9-29 waited on F219's rule.
- **Lessons:**
  - Placement on the floor or a phone bar is past the developer (F3's lesson again): the phone title took three tickets, the phone belts three, and the lead's next link was drawn at (0, 16). Added to the Known range.
  - The checkpoints earned their keep: all 36 findings were real. Their weak point was chains: each fix ticket closed one finding and the next checkpoint found the neighbour.
  - A sort test whose cases also sort by key proves nothing: the Milestones page sorted not-started cards by key, not by board order, and its test passed. Fixed in this review, with a test where the two disagree.
- **What clogged the line:** about 13 of Qwen's 34 hours went to failed or timed-out attempts (36 of 67), mostly on the phone-layout and belt chains; the fix is routing those to the lead from the start. The card also stayed open five weeks because f9-29 waited for F219's pace rule and the last two lead tickets for Claude's week: a lead ticket that depends on another card's ADR could have moved to that card.

### 6. What next
- **Product:** product work is on hold, as you asked.
- **Factory:** close long-lived polish cards sooner: when a card's last tickets wait on another card, move them there and sign this one off. And a planning check that routes any ticket touching `factory.js` geometry or phone layout CSS to the lead, rather than a line in the Known range nobody's planner reads.

---

## What was built
See "What changed". The milestone's commits are listed in the review prompt; several merges also carried other cards' work.

## Findings (round 1)
| id | grade | route | what | status |
|---|---|---|---|---|
| F1 | should-fix | claude | Milestones page sorted not-started cards by key: `_with_priorities` ran after the sort, so every priority was None (f9-21); its test passed because F3 < F5 either way | fixed: priorities before the sort, test with F9 at priority 1 |
| F2 | should-fix | local | While you were away: no test that a ticket without `merged_by` shows no label, nor that Claude finishing after one passed developer attempt reads "1st try" (C724-2, C728-2) | ticket `f9-35` |
| F3 | should-fix | local | The lead next-link test is tautological and measures "THE LEAD", not the link (C728-1) | ticket `f9-36` |
| F4 | nit | claude | Docstring still listed Ollama among the allowance rows (C677-1) | fixed |
| F5 | nit | claude | Redundant `[data-merged]` click and Enter branches (C693-2); merged crates weren't keyboard-reachable, so the Enter branch was dead | fixed: one `[data-crate]` path, merged crates take focus |
| F6 | nit | report | `f9-12` in `later/` duplicates `f9-11`; the card says it goes | report only |
| F7 | nit | report | No test that the allowance legend follows the last row (C702-1); `#replay`'s -10 px margin the ticket said wasn't needed (C702-3); the phone replay test scrolls the bar into view before checking it (after C442-2) | report only: the template puts the legend after the loop by structure |

The checkpoints' 36 findings: all confirmed; nine became fix tickets during the card (f3-32, f9-08, f9-09, f9-18 to f9-20, f9-30 to f9-34), the dial ones went with f9-17's bars, five test-only ones wait in `later/`, and the rest are above.

## Factory
- **Flow:** no stop for the owner; f9-29 held for F219's rule (ADR 44), then for Claude's week. Three Opus escalations.
- **Models:** Qwen about 34 hours, 31 passing attempts and 36 failed or timed out; Opus three escalations, f9-01 and twelve directions; Sonnet f9-29 and f9-27 first time, and 14 checkpoints; Copilot 3 stand-in checkpoints. Dollars: the runner's numbers below.
- **To change:** route placement work (floor SVG, phone layout) to the lead at planning; see "What next".

## Workflow observations
- f9-26 removed f3-31's sticky replay bar on purpose (under the floor it can't stick to the bottom), so C442-2's sticky check is moot.
- f9-29's dashboard reads the runner's private `loop._rested`, `_windows_from` and `_passing_over` so the page and the pick can't disagree. Right call; if those are renamed, `claude_pace` breaks first, and its tests cover it.

<!-- runner report -->
<!-- /runner report -->
