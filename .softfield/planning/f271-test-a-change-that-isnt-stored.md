# F271: Two refused-edit tests check the request list instead of waiting 300 ms

The planning thread behind F271's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-18 19:13

> test_a_change_that_isnt_stored_leaves_the_row_open (test_coming.py) and test_a_message_change_that_isnt_stored_leaves_the_editor_open (test_thread.py) still prove "no re-fetch followed" with wait_for_timeout(300): use watch_requests and requests_until from the dashboard tests' conftest, as f71-03 did for the other two. From F71's review.

## The lead, 2026-11-18 19:17

> I drafted one small, tests-only ticket for a developer. It passes the ticket check; the whole-folder check fails only on two old F9 drafts that belong to another card.
>
> 1. **One developer ticket, following f71-03's own fix**: Both tests save an htmx form that posts to /requests: the plant editor on the planning page and the message editor on a thread. So the request watcher in the dashboard tests' conftest sees the post just as it does in the two tests f71-03 already fixed. Each test will wait for the post's answer, then check that the list holds only that post's two entries, sent and answered. A late re-fetch would make that check fail, where today a fixed 300 ms wait can miss it. This is small and copies an example already in the code, so a developer does it, not the lead.
>    Action: Ticket f271-01-refused-edits-wait-on-requests, tests only, no code change.
> 2. **Other short waits stay for now**: About 30 other browser tests still call wait_for_timeout for 50–500 ms, mostly in the board, planning and app test files. f71-03 allowed waits up to 500 ms, so most of them are pauses, not proofs that nothing happened, and that kind of wait is less fragile. I'm keeping this card to the two tests F71's review named, so it stays a 40-minute ticket.
>    Action: Nothing now. If one of those tests turns flaky, it gets a card of its own.
>
> Proposals:
> - F271: two refused-edit tests check the request list instead of waiting 300 ms (plan)
