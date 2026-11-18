# F266: The over-pace stripe covers the week meter's green fill to its very end

The planning thread behind F266's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-18 07:33

> There's a tiny green dot on the right of the pace slider which annoys me. The pace slider is on top and leaves about a pixel of the green line under

## The lead, 2026-11-18 07:34

> I found the cause and drafted one small ticket for a developer to fix it.
>
> 1. **What the green dot is**: The Planning room's week bar is over pace right now: 36% used, with today's pace at 26%. The bar draws the green fill to 36%, then lays the yellow striped stretch over the part past the dashed pace post. The stripe stops short of the fill's end, so 1 to 4 pixels of green show on its right. That is the dot and the line you see. There are two reasons. First, the fill starts 1 pixel in from the bar's edge, but the stripe starts 1 pixel further left. Second, the stripe's width is rounded on its own: today it comes out at 9% where the fill minus the post is 10%. The Overview's week bar has the same fault, because both pages draw the bar from one template.
>    Action: Fix it in the template (point 2).
> 2. **The fix: the stripe ends exactly where the fill ends**: The stripe will reuse the same rounded numbers as the fill and the post. It starts 1 pixel right of the post and is as wide as the fill minus the post, so its right edge always lands on the fill's. The change is in the template only. The style sheet and the dashed post stay as they are. This is a small ticket that follows an existing test, so a developer takes it (difficulty 1).
>    Action: Ticket f266-01-stripe-covers-the-fill-to-its-end, after your Approve.
> 3. **No mock-up**: This brings back the look the bar was always meant to have (stripe to the end, no green past it), so there is no new picture to draw. Tell me here if you'd like one anyway.
>    Action: Nothing.
>
> Proposals:
> - The over-pace stripe covers the green fill to its end (plan)
