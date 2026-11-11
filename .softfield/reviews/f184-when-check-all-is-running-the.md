# Review: F184, the top bar's dot goes green while the runner checks

- **Status:** done, signed off by the owner on 2026-11-11.

## Sign-off sheet

### 1. What changed
- While the runner works on its own between jobs (check-all, the gates, the warm-up, picking the next ticket), the dot in the top bar is green and breathes, on every page. Grey now means only that nothing is happening.
- If you press ⏸ during that work, the bar names it: "Pausing after check-all · f184-01-runner-dot", not "Pausing after this job". The words that show when you tap are the same ones the bar keeps once the runner has your request.

### 2. How to test it yourself
1. On your phone, open the dashboard while the runner is between jobs (just after a ticket merges, while "Running: check-all · …" shows). The dot is green and breathes.
2. Tap ⏸ there. The bar reads "Pausing after check-all · <ticket>", with a dashed orange edge, and keeps the same words after the next refresh.
3. Press ▶ to resume. Once the runner has nothing left to do, the dot is grey again with "Idle: nothing to do".
4. While a developer or the lead has a job running, the dot stays blue or orange, as before.

### 3. Left for later
Nothing.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-06: f184-01-runner-dot merged on the local model's first attempt (33 minutes of model time, 15 minutes of gates, about 3.1M local tokens in). No Claude tokens apart from the plan and this review.
- 2026-11-10: the review was parked because Claude was at its limit. It ran on 2026-11-11.
- Lesson: the ticket said which side to fix (the sign's words, to match the server). The local model fixed the other side, the server, and wrote a test that copied the code's own logic, so the tests passed with the wrong order. The lead fixed it in the review (F1, F2). What changes: the sign's words now come from the server (`Status.pausing`), so they can't drift from the bar's words again.
- Session report: [`2026-11-06-0111`](../sessions/2026-11-06-0111.md).

### 6. What next
- **Product:** nothing new from this card; the product stays on hold.
- **Factory:** when a ticket names expected words ("Pausing after check-all · f1-04-live"), the developer's test should check those exact words, not work them out in the test. A line in the task format's "Done when" guidance would cover it: "a test asserts the literal words the Done when names".

### 7. What clogged the factory line
- **Waiting its turn:** planted and planned on 2026-10-29, built on 2026-11-06. Eight days in the queue behind other cards. That is the board's order working as meant, not a clog.
- **Waiting for Claude:** the review was parked on 2026-11-10 for Claude's limit and ran the next morning, about half a day. What would unclog it: nothing to change; ADR 20's reserve already orders this.
- **No failed attempts and no stops for you.**

## What was built
- `factory_status` (`factory_dashboard/app.py`) gives the `runner` dot to "Running: <activity>" and to a pause asked with no live job; "Idle: …", the paused hold and "Stopped" keep their dots.
- `dashboard.css`: `.factory-status .dot.runner` in `--good`, with the same halo and breathing as the agents' dots, and the comment says what green means.
- Lead fix in review: `Status.pausing` holds what a pause asked now would say. `bar_status.html` shows it in the ⏸ sign's `data-asked`, and `factory_wide_status` adds the project name when there are several projects.

## Findings and resolutions
- **F1 (should-fix, fixed by the lead):** a pause during check-all read "Pausing after f1-04-live · check-all", the reverse of the card's Outcome. The ticket asked to fix the template's reversal; the developer reversed the server's words to match it instead. It also named "picking the next ticket" and "Idle: …" lines, which the ticket excluded. Now the pause words are worked out once on the server and the sign shows them as they are. Fixed directly rather than by ticket: it was a design slip by the developer, and the fix (one field and one template line) was smaller than a ticket.
- **F2 (should-fix, fixed by the lead):** the new test `test_the_pause_sign_s_data_asked_matches_the_server_words` worked out its expected value with the same reversal as the template, so it couldn't fail on the wrong order, and it never asked for a pause. It is replaced by `test_the_pause_sign_shows_at_the_tap_what_the_server_then_says`, which reads the sign, asks for a pause and compares with the bar's words for five cases (a developer job across projects, a lead ticket, check-all, idle, waiting).
- The existing tests the developer edited (the top bar's parametrised cases and ids, and the dot's colour and breathing assertions) were extended in the right way; only the runner-paused case's expected words changed in review (F1).
- French: none; the dashboard is English only.
- Pictures: none for this card.
- Score: 6/10. The dot is right, but the pause words came out backwards and a test that copied the code hid it.

## Set aside
Nothing.

## Workflow observations
- No checkpoint ran on this one-ticket card, so the wrong order reached review. For a single difficulty-2 ticket that's acceptable; the cost was one lead fix.
- A test that works out its expected value the same way as the code passes whatever the code does. The guidance suggested in "What next" targets that.

<!-- runner report -->
<!-- /runner report -->
