# F259 review: the pace indicator, on the Planning room too

- **Status:** done, signed off by the owner on 2026-11-18.

## Sign-off sheet

### 1. What changed

The Planning room's "The lead's window" tile now shows Claude's week pace the way the Overview does:
- the week's bar gets the dashed yellow post (today's pace line), and the part used past it is striped;
- over pace, the same "Over pace · lead tickets wait until about …" plate sits under the week's line;
- on pace, the week's small line ends "· on pace · today's 33%";
- in the week's last hours, the "Last hours" plate shows (the review added this: the merged work had left it out);
- with the week's reserve lever on, there is no post and no plate.

The plate's words now come from one place for both pages, so they can't drift apart.

Matches the mock-up (the after pictures show the over-pace state, as the Proposed does).

### 2. How to test it yourself

1. On your phone, open Planning. "The lead's window" sits near the top.
2. Look at the second bar (the week). There's a dashed yellow post on it; if the green has gone past it, the part past the post is striped and an "Over pace" plate sits under it.
3. Open the Overview and compare Claude's week meter: same post, same stripes, same words on the plate.
4. If you're under the pace, the week's line on Planning ends "on pace · today's N%" instead, with no plate.
5. Turn the week's reserve lever on from the Overview: the post and the plate go away on both pages.

### 3. Left for later

Nothing.

### 4. Decisions waiting for you

None.

### 5. How the work went

- 2026-11-18 00:48, [session report](../sessions/2026-11-18-0048.md): 1 ticket merged by the local model on its second attempt (the first stopped with no edit after 20 minutes); 3.4M local tokens; no lead tokens until this review.

Lessons:
- The developer built the page change but wrote none of the ticket's tests, and the gate let it through because the named test file still passed unchanged. That missing test is why the "Last hours" plate was missing. The review added the plate and five tests.
- A tiny change (about 20 lines) took the local model 49 minutes, 20 of them on an attempt that never edited a file.

### 6. What next

- **Product:** nothing for now; product work is on hold.
- **Factory:**
  > Make the developer gate fail a ticket whose branch never touches any file in its `tests:` list, so "done" can't pass on the old tests alone (F259 merged with no new test and a missing plate).

### 7. What clogged the factory line

- **20 minutes on a stopped attempt:** the local model's first attempt made no edit in 20 minutes and was stopped (jobs, run 20261118-004802, 00:48–01:08). It's a single case here, so the fix is to keep watching it rather than change anything yet.
- **28 minutes on the second attempt** for about 20 lines in four files. That's the local model's normal speed on a 92k-token context. Nothing to unclog until it gets worse.
- No waits for limits, no stops for the owner, and no tickets waiting on other tickets (the card had one ticket).

---

<!-- runner report -->
<!-- /runner report -->

## What was built

`f259-01-planning-week-pace`: `planning` calls `claude_pace` once and passes its `.week` as `pace`; `planning.html` draws the week's bar with it and adds "on pace · today's N%" to the week's line; the Over pace and Last hours plates moved from `_partials/allowance.html` into the macro `pace_plate(wp)` in `_partials/allowance_bar.html`, which both pages now call. The Overview's output is unchanged, and its pace tests pass untouched.

## Findings and resolutions

| id | grade | what | route |
|---|---|---|---|
| F1 | should-fix | `/planning` showed the plate only when over pace, never in the last hours (`planning.html`) | fixed by the lead: `pace_plate` is called on its own, since it already picks the state |
| F2 | should-fix | no tests: `test_planning.py` was never touched, so none of the six Done-when lines was checked | fixed by the lead: five tests for over pace, on pace, last hours, a full week and the lever (the over-pace test also checks that the 5-hour bar has no post) |
| F3 | nit | a redundant `if pace` / `else` around the same `allowance_bar` call | fixed by the lead, with F1 |

No checkpoint ran on this card, so there are no checkpoint verdicts. Score: 5 out of 10. The page is right, but one Done-when line was missed and no tests were written.

There is no French: the change is to the factory dashboard, not to `coucou/`.

## Set aside

Nothing.

## Factory

- **Flow:** one ticket, one run, no stops, no interventions from the owner, no limits hit, nothing parked.
- **Models:** the local Qwen merged it on attempt 2, after attempt 1 stopped with no edit. Claude did only this review.
- **What to change:** the gate. A listed test file the branch never touches should fail the ticket (quoted in item 6). This is the root cause of both F1 and F2.
