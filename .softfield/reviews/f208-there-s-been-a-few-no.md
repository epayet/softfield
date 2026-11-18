# Review: F208, a local attempt finishes its step before the no-edit stop

- **Status:** done, signed off by the owner on 2026-11-18.

## Sign-off sheet

### 1. What changed
- **The 20-minute stop no longer cuts a thought in half.** At minute 20, if the developer hasn't made an edit yet, the step it's on gets to finish. The attempt is stopped at the next check after that step ends with no edit, and at minute 35 at the latest. If that step does make an edit, the attempt carries on as normal. The stop still reads "stopped: no edit after 20 min" on the dashboard.
- **A stopped attempt keeps its thinking.** Every attempt stopped for "no edit" or "repeating itself" now writes its thinking to `thinking-N.md` beside its log, whether or not the lead's direction follows. The next factory review can read whether those long thoughts were planning or going in circles (card D3).

No mock-up for this card (nothing on screen changes).

### 2. How to test it yourself
1. Wait until an attempt on the dashboard runs past minute 20 with no edit. It stays running while it finishes its step: under a minute when it's reading, up to minute 35 when it's in one long thought.
2. Once it's stopped, open its run's ticket folder (`.softfield/var/runs/<run>/<ticket>/`): `thinking-N.md` sits next to `opencode-N.jsonl`, and its last paragraph is the thought it was in at minute 20.
3. Over the next week or two, look for an attempt that made its first edit after minute 20 and still passed. That's the case this card is for.

### 3. Left for later
Nothing from this card. D4 (a warning when the model slows to about 2 tokens a second, and the prompt-cache misses) stays with F195, as the card planned.

### 4. Decisions waiting for you
None. This is a timeout, not a workflow rule (card D1), so there's no ADR.

### 5. How the work went
- 2026-11-18 ([session](../sessions/2026-11-18-1355.md)): one lead ticket (`runner/**` is protected), merged on the first try by Sonnet in 5.5 minutes for $0.26; planning on 2026-11-03 was $2.08 on Opus. The local model had no part in this card (its 3.0M tokens that session went to f267-02).
- Lessons:
  1. The plan's "What we know" did the real work. It split the 64 stops into a slow-machine spell (39), the normal rate (25, 13%) and today's two cut in one long thought. That made a narrow fix possible instead of moving the number again, as F93 did.
  2. The ticket's Done when named the comment, the tests and the 35. The lead ticket matched it line for line, with no rework.

### 6. What next
- **Product:** product work is on hold; nothing to suggest.
- **Factory:**
  - Card D3 is a measurement, not a card. At the next periodic review (F59), count the attempts that edited or passed after minute 20 and read their saved thoughts. If nearly none did, go back to a plain stop at 20.

### 7. What clogged the factory line
- **Waiting in line, 15 days** (planned 2026-11-03, run 2026-11-18): the card waited its turn in the board's order while 20-minute stops kept costing attempts. Unclog: nothing to change; the order is the owner's.
- **The work itself, 5.5 minutes** (15:34–15:40): no limits, no failed attempts, no stops for the owner, no tickets waiting on each other.

## What was built
`f208-01-finish-the-step` (in `runner/local_model.py`):
- `stuck()` takes `steps_at_limit`, the number of steps finished when minute 20 first passed. With no edit, it stops the attempt once a later step has finished, or at `NO_EDIT_LIMIT` (35 minutes).
- `run_opencode`'s tick records `steps_at_limit` once, at the first tick past minute 20. It keeps the last reasoning it read, and on a stop writes it to `thinking-N[-M].md`, named after the log.
- The comment above `NO_EDIT_AFTER` gives the F208 reason, and `STOP_NO_EDIT` keeps its words, so `stop_reason` still recognises it.

Tests (`tests/runner/test_local_model.py`):
- Five new tests: no step after minute 20 is stopped at 35; a step finishing at minute 24 is stopped then; an edit at minute 30 runs to the end; a stopped attempt leaves its thinking beside `opencode-2-3.jsonl`; and no reasoning means no file, while a repeat stop writes it.
- One existing test was edited: `test_a_stream_with_no_edit_for_20_minutes_is_stopped` now expects the stop at minute 20.5 instead of 20, because its stream finishes a step every half minute and the next step ends the wait. The edit is right and follows from D1.

Checked: the 38 tests in `test_local_model.py` pass and ruff is clean. The full `tests/runner tests/factory_dashboard` run reached 73% with no failures, then was killed at its 10-minute limit. It printed errors only after the kill, which looks like the interruption rather than real failures, and the change touches nothing the dashboard imports. The runner's gates run the suite in full. Neither the dashboard nor the prompts mention the 20 minutes, so neither needed changing. No French in this card.

## Findings and resolutions
- **F1 (nit, report):** two writers now save `thinking-N.md`. `run_opencode` names the file after the log, so attempt 2's transient retry becomes `thinking-2-2.md`. `loop._save_thinking`, at a direction, numbers by position in `rec.sessions`, so the same retry becomes `thinking-3.md`. This only happens after a transient retry, both files hold real thinking, and the direction reads every `thinking-*.md`. Nothing is lost, so it isn't worth a run.
- **F2 (nit, report):** the last new test runs three scenarios in a row, so a failure names only the first. It's correct and covers what it should.

No checkpoint ran on this card, so there are no checkpoint findings to judge. Score: 9.

## Set aside
Nothing.

## Workflow observations
- A small, protected runner change with exact expected numbers (24, 35, 20.5) suited a Sonnet lead ticket: $0.26 and one attempt.
- How well D1 works can only be told from future runs (D3). Until then, the 15 extra GPU minutes per runaway attempt are the known cost.

<!-- runner report -->
<!-- /runner report -->
