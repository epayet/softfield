# F186: A sign-off stays signed: F142's keeps coming back

The planning thread behind F186's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-29 07:56

> Why can't I sign off f142 it keeps coming back

## The lead, 2026-10-29 08:05

> I've found why F142's sign-off keeps coming back and drafted one fix ticket for the lead (F186-01) to stop it. The fix also clears F142's stuck sign-off on its own once it lands, so you won't have to press again.
>
> 1. **Your first sign-off worked, then a late review undid it**: You pressed Sign off on F142, Phone notifications, at 08:37 yesterday while its review was still in round 2. At 08:53 the runner marked the card done, tagged it and cleared the item. The review finished afterwards and recorded its usual "ready for sign-off" verdict without checking that you had already signed off. Six minutes later that set the milestone back to "review" and put the sign-off back on your desk (item 250, open since).
>    Action: Ticket f186-01 (D1): when a review ends on a milestone that is already signed off, nothing more is recorded.
> 2. **Every press since then failed without telling you**: Signing off writes the card, commits, then creates the milestone's "done" tag, and only then updates the dashboard's database. The tag already existed, so your four later presses (yesterday 09:02, and today 01:04, 07:40 and 07:51) each failed at that step with "tag already exists". The dashboard was never updated, so the item stayed. The only trace in git is one commit that changed the sign-off date to today.
>    Action: Ticket f186-01 (D2): pressing Sign off on a card that is already signed off just settles it: the item is cleared and the milestone marked done, with no new commit or tag, and the first date stays.
> 3. **F142 clears itself, no extra press**: Once the fix is in, the runner closes any sign-off still open for a milestone that is already signed off, each time it handles your requests. F142 then leaves your desk at the runner's next pick. No other card is stuck like this: of the six sign-offs waiting for you, only F142's is already done.
>    Action: Ticket f186-01 (D3). Until it lands, ignore F142's sign-off: pressing again changes nothing.
> 4. **A failed request should show on your desk**: Your four failed presses ended with an error recorded in the database, but nothing showed you. Your rule says a refused request carrying your words stays on the desk until you act, and a sign-off press deserves the same. I've left it out of this card to keep the fix small. After this fix, the tag error can't happen any more for a done milestone.
>    Action: Nothing now. If you want it, I'll draft a ticket for F31, the requests card: a failed sign-off or approval shows on the desk with its reason.
>
> Proposals:
> - F186, A sign-off stays signed: one lead ticket (plan)
