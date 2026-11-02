# F193: The project picker follows the owner's project order

The planning thread behind F193's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-02 17:43

> The project picker at the top should be ordered by project order

## The lead, 2026-11-02 22:21

> One small ticket is drafted for you to approve.
>
> 1. **Why the picker is out of order**: The picker has its own list, sorted by name, so it shows coucou, softfield, travel-companion. The Projects page and the runner use your order: travel-companion, softfield, coucou.
>    Action: One developer ticket makes the picker use the same list as the Projects page.
> 2. **No mock-up**: The picker looks the same and stays where it is. Only the order of the names inside it changes, so a picture would show nothing new.
>    Action: None, unless you want one.
> 3. **When a new order shows**: A new order you send from the Projects page reaches the picker after the runner's next pick, once a page is reloaded. The Projects page's order changes at the same pick.
>    Action: None.
> 4. **It waits behind most of the board for now**: F193, The project picker, sits at the end of the ready cards once approved, and those tickets come first. The fix itself is one small ticket, and nothing else depends on it.
>    Action: If you want it soon, drag it up the board after approving. I'd put it near the top, since you see this list on every page.
>
> Proposals:
> - The project picker follows the owner's project order (plan)
