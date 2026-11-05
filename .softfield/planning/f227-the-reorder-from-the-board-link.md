# F227: Remove the 'Reorder on the board' link from the Overview's queue

The planning thread behind F227's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-05 11:03

> The reorder from the board link in overview is unnecessary

## The lead, 2026-11-05 11:26

> I drafted the plan on the branch: one developer ticket and a mock-up, for your Approve.
>
> 1. **Yes, the link can go**: I agree. The Board tab is always in the tabs on the same page and opens the same board for the same project, so the link adds a row for nothing, on a phone especially. The link only came in with F15, Reprioritising tickets, to point people to the board when the arrows left, and that job is done.
>    Action: One small developer ticket removes it from the page and its live refresh.
> 2. **An empty queue would show a bare heading**: With nothing waiting, the link is the only row under "Next in line". Removing it alone would leave that heading over an empty list. So I also drop the heading in that case, and the panel just says "The queue is empty." A lone queued job or a due review still shows under the heading.
>    Action: Part of the same ticket, drawn in the mock-up's lower picture.
>
> Proposals:
> - F227: the Queue panel without its board link (plan)
> - F227 mock-up: the Overview's Queue panel without the board link (mockup)
