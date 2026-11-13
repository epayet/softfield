# Review: F242, a fast-lane card's review goes in the fast lane

## Sign-off sheet

### 1. What changed

- When a card in the fast lane has all its tickets done, **its review now goes with the lane**. The runner queues it ahead of every other job and ticket, so it no longer waits behind other cards' checkpoints, escalations or developer tickets.
- It waits only for a checkpoint or an escalation of **its own** card. Other cards' reviews keep the old rule.
- If Claude is in your share of the 5-hour window, the review **no longer parks**: it may use both reserves, the same as a fast-lane ticket. A real limit or an expired login still stops it.
- On the Overview, **Next in line** shows that review in the **Fast lane** bay, at the top, the same way it shows an escalation for a lane card.
- Nothing changes for cards that aren't in the fast lane.

The card has no mock-up and no after pictures: the review row already existed and only moves to the bay.

### 2. How to test it yourself

1. On the board, put a small card in the fast lane and let the runner finish its last ticket.
2. On your phone, open the Overview: within a minute, **Review: <the card>** appears at the top of the Fast lane bay, above any planning or developer work.
3. Watch the line: the runner takes that review next, as soon as the running job ends. A running ticket is never stopped for it.
4. If the 5-hour meter is in your share at that moment, the review still runs. Before F242 it parked until the reset.
5. Do the same with a card that isn't in the fast lane: its review appears under the run order, as before.

### 3. Left for later

Nothing deferred, and no bug tickets set aside.

### 4. Decisions waiting for you

None.

### 5. How the work went

- **2026-11-13, run 20261113-082658:** 2 tickets merged, 0 escalated. `f242-01` (the lead's runner work) was built by Sonnet in 9 minutes for $0.49. `f242-02` (the dashboard) was built by the local model in 79 minutes, all gates green on attempt 1.
- **Lessons:**
  - The lead ticket was small and well specified (D1 to D3 named the functions). It passed first time with no checkpoint needed.
  - Qwen's ticket copied an existing test pattern (F191 D3's) and still used 3.9M tokens in, reaching **130,249 of 130,304** context. It passed, but only just. If it happens again on a ticket this small, the planner should name the exact test to copy.
- Sessions: `.softfield/sessions/` (the 2026-11-13 reports).

### 6. What next

- **Product:** on hold, as you asked.
- **Factory:** the planning room could show each fast-lane card's **whole path**: tickets, then checkpoint, then review, then sign-off. That way "why is the lead reviewing something" is answered on the card itself. I'd plant it as a card if you want it. A second card could watch Qwen's peak context per ticket: two near-limit runs on small tickets would be worth a planner rule.

### 7. What clogged the factory line

- **About 4 h 40 min waiting:** `f242-01` merged at 07:53, but `f242-02` started only at 12:33, behind m10, m11 and m2 tickets. The card wasn't in the fast lane and sat at board place 6, so this was the board's order working as intended, not a fault. To unclog: put the card in the fast lane, or higher on the board.
- **79 minutes of model time** for a 7-line change, near the context limit: see lesson 2 above.
- The review itself was queued 2 seconds after the last merge and started 10 seconds later. No waits for limits and no stops for you.

## What was built

- `runner/dispatch.py`: `LANE_KINDS = (ESCALATION, DIRECTION, REVIEW)` is now the lane test in `plan`; `GOES_WITH` keeps its meaning (D1).
- `runner/loop.py`:
  - `lane_reviews` gives the due reviews of fast-lane cards that are still ready or building.
  - `work_queue` and `dry_run_plan` add them to `first`, and the round's lane pass takes them (D1).
  - `_queue_due_review` queues them first.
  - `_runnable_rows` lets them through past other cards' checkpoints and escalations, with `_holds_review` holding a review for its own card's (D2).
  - `park_review` asks `claude_hold` with `owners` for a lane card (D3).
- `factory_dashboard/overview.py`: `queued_jobs` treats a review whose subject starts with a lane card's short key as a lane row (D4).

I checked these by reading the code:
- A review's subject is the full key, and `lane_reviews` returns full keys, so `q.subject in first` matches.
- `_holds_review` matches a checkpoint by its full key, and an escalation of the card's tickets (or a fix ticket) by `<short>-`. `f24` can't match `f242-…`.
- Rounds pass `reviews=True`, so the lane pass sees the review. A picked review ends the turn with `s.report.review`, and `run_projects` runs it.
- `enqueue` keeps an already-open row, so queuing the lane review on every pick adds nothing twice.

## Tests

- **Runner:** six new tests in `test_loop.py`. They cover:
  - in the lane only while ready or building;
  - queued past another card's checkpoint;
  - held by its own card's escalation;
  - the old rule for a card outside the lane;
  - `owners` only for the lane card;
  - the dry run listing it first.
- **Dispatch:** one new test in `test_dispatch.py`: the lane review goes first and the rest keep their order.
- **Dashboard:** two new tests in `test_overview.py`: in the bay, and in the run order once the card is asked out.
- No existing test was edited.
- After the review's edits (docstrings only): the three test files the milestone touched (`test_overview.py`, `test_dispatch.py`, `test_loop.py`) pass, 609 tests. The full `tests/runner tests/factory_dashboard` run never finished within the session's 10-minute limit, twice: no failures up to the point each one stopped, while the runner and this review shared the machine.
- No French touched.

## Findings and resolutions

- **F1 (nit, fixed by the review):** `queued_jobs`' docstring still named only escalations and directions. It now names reviews, with F242 D4.
- **F2 (nit, fixed by the review):** a dashboard test's docstring claimed to cover a card "on its way out", but it tests only a card asked out. Narrowed to what it tests. The dashboard reads the lane from every stage (`reserve_marked`), unlike the runner's ready/building filter. But a finished review takes the card to sign-off and closes its row, so the two never show different things.
- No checkpoint ran, so there are no checkpoint findings to judge, and none were missed.

Score: 9.

## Set aside

Nothing.

## Workflow observations

The Factory section is above: "How the work went" and "What clogged the factory line". Only the local model's near-limit context needs following up, and it is planted as a suggestion, not a ticket, until it repeats.

<!-- runner report -->
<!-- /runner report -->
