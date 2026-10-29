# F188: Drop the 'N agreed · M to change' count from the review's phone bar

The planning thread behind F188's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-29 08:19

> I don't need the '4agreef 0 to change ' to be sticky in the planning sticky approve plan bar it takes too much space

## The lead, 2026-10-29 08:20

> I've drafted one small developer ticket and a phone mock-up. Together they take the count off the review page's bottom bar on a phone.
>
> 1. **The count leaves the bar at the bottom of a phone**: Agreed, it's redundant. The yellow dots above the bar already show which points have a comment. Once you comment, the button already reads "Send 1 change back". On a phone the bar will hold only the button, with the Reject… fold at the right.
>    Action: One developer ticket, f188-01, about 20 minutes: it hides the count with CSS on narrow screens only and updates the test that checked it was there.
> 2. **The bar won't get any shorter**: The bar's height comes from the 44 px button, which is the size a finger needs, so dropping the count frees width but not height. The bar will still be about 60 px tall. If what bothers you is the bar's height and not the clutter, the other option is to stop it sticking to the bottom, as you asked in F42, 'The space for me to scroll'. We kept it sticky there so Approve is always in reach. I'd keep it sticky and just drop the count.
>    Action: Nothing, unless you want the bar to stop sticking to the bottom too. Say so and I'll add that to this plan.
> 3. **Wide screen stays as it is**: On a wide screen the review sits in its side panel and doesn't stick to the bottom, so the count costs no space there and stays.
>    Action: Nothing.
> 4. **Mock-up of the bar on a phone**: It shows Today and Proposed, each with no comment and with a comment on point 2. The values come from this card's own plan.
>    Action: Look at the mock-up; the ticket builds its Proposed side.
>
> Proposals:
> - F188: the count leaves the phone's review bar (plan)
> - F188 mock-up: the review's bar on a phone, without the count (mockup)
