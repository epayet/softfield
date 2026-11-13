# F108 review: desk boxes say when

## Sign-off sheet

### 1. What changed
- On `/planning`, a card to sign off now says when it was reviewed: "reviewed 2 h ago · waits for your sign-off". A card reviewed in a terminal session (no review job) still says "reviewed · waits for your sign-off".
- A proposal's time ("· proposed 3 min ago") shows where a proposal stands alone: the general thread's proposals on the desk, and the Overview's "Needs you" notices. On the desk, F210 (merged the same day) put a card's proposals in its conversation's box, which already says "the lead replied 3 min ago". That box doesn't add a second time.
- A box on its way (approved, rejected, or being revised) shows no time: it says what's coming.

There's no mock-up for this card, so there's nothing to compare against.

### 2. How to test it yourself
1. On your phone, open `/planning` while a milestone waits for your sign-off. Its box reads "reviewed N h ago · waits for your sign-off".
2. Ask the lead something on the general thread so that it answers with a proposal. The proposal's box reads "… · proposed N min ago", and the time grows when you refresh.
3. Approve it. The box turns dashed and reads "on its way · the runner applies it at its next pick", with no time.
4. On the Overview, a card's open proposals in "Needs you" end with "proposed N ago".

### 3. Left for later
- Nothing set aside. As the card decided (D5), seeds, "Didn't go through" and blocked tickets still show no time.

### 4. Decisions waiting for you
- None.

### 5. How the work went
- 2026-11-12 ([session](../sessions/2026-11-12-0628.md)): 1 ticket merged by the local model on its third attempt. Attempts 1 and 2 each hit the 75-minute limit, then a lead direction (about 1 minute of Opus) got attempt 3 through in 46 minutes.
- Lessons:
  - A difficulty-2 "follow the example line" ticket still cost about 3 hours of local time. The direction step is what unblocked it.
  - The local model changed a function's signature, so it had to update callers outside `files:` (overview.py, thread.py). That was fine here, but the ticket should have listed them.
  - It loosened one existing test to make it pass (now pinned again). Edited tests still need the reviewer's eye.
- Review round 1 (Claude): 2 should-fix and 1 nit, all fixed directly. Each was under 20 lines in one file.

### 6. What next
- **Product:** product work is on hold; nothing proposed.
- **Factory:** when a ticket changes a function's signature, the planner should list the callers in `files:`. Grepping the callers while planning takes a minute and saves an attempt. Also consider sending the lead direction after the first timeout on a difficulty ≤ 2 ticket, not the second: here it would have saved about 75 minutes.

### 7. What clogged the factory line
- **About 150 min on two timed-out attempts** (11:46–14:18 on 2026-11-12, from `jobs`). Fix: send the direction after the first timeout on small tickets (above).
- No waits for limits, no stops for the owner, no tickets waiting on one another: it's a single ticket.

## What was built
`f108-01-desk-says-when` (commit 46fa80eca):
- `_open_proposals` now takes `now` and appends "· proposed {ago} ago" to open proposals.
- `_ripe` reads the latest finished `review` job's end.
- The callers in `overview.py` and `thread.py` pass `now`.

F210, merged right after, moved a card's proposals into its conversation box. It kept F108's time only where a proposal stands alone (`_general_items`, and a lone bundle in `_with_proposals`), and it rewrote F108's desk tests to exact words.

## Findings and resolutions
| id | severity | route | what | resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | `_ripe` looked the milestone up by key alone, but keys are only unique per project (`bugs` exists twice in the live database), so a box could show another project's review time | Fixed: one query joining jobs, milestones and projects by name. Test `test_a_ripe_cards_time_is_its_own_projects_review`, built so that a key-only lookup finds the other project first |
| F2 | should-fix | claude | `_open_proposals` added "proposed N ago" to a bundle being revised (dashed, on its way), against D3. It showed on the Overview notices and the thread page | Fixed: same `not item.on_its_way` guard as `_with_proposals`. Test `test_a_proposal_being_revised_says_no_proposed_time` |
| F3 | nit | claude | An edited assertion in `test_thread.py` was loosened to startswith/contains | Fixed: full match on the sentence's shape |
| F4 | nit | report | `_ripe` runs one query per ripe card | Left as is: a few cards at most |

No checkpoint findings to judge. Score: 6/10. The code meets the spec, but it had two real correctness slips and a loosened test, and a small ticket took three attempts.

## Tests read
- `test_planning.py`: the F108 block (since made exact by F210) covers open, merge, no key points, a later reply, pending approval, review end, two reviews, and no review. It was missing the cross-project and revising cases, which are now added.
- `test_proposal.py`: the edits only append the expected "· proposed 30 min ago". They're correct.
- `test_thread.py`: loosened, now pinned (F3).

No French: this is factory work only.

## Workflow observations
- The runner flagged both the files outside `files:` and the edited tests. Both flags were useful in this review.
- The direction step works. On small tickets, run it earlier.

<!-- runner report -->
<!-- /runner report -->
