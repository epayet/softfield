# F295: One list of an app's up states, for the Forget guard and the Stop button

The planning thread behind F295's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-24 22:08

> runner/requests.py's _forget_project lists the app's "up" states itself while factory_dashboard/stacks_routes.py has UP for the same set: move UP into runner/stacks.py and use it from both, so Forget's button and the runner's guard can't drift apart. From F273's review.

## The lead, 2026-11-25 08:19

> I drafted one small lead ticket for this card. `softfield check-tickets` passes it.
>
> 1. **Right call, and it's one small lead ticket**: The two lists hold the same three states today: running, starting and update failed. `factory_dashboard/stacks_routes.py:48` keeps its own `UP`, and `runner/requests.py:2161` writes the same three inline. If they drifted, the page could offer Forget's button while the runner still refused it, or the other way round. The fix moves `UP` into `runner/stacks.py`, beside the state words it groups, and both places read it from there. It changes `runner/`, which is protected, so it's a lead ticket. It's about the size of a 14-minute ticket and has nothing to wait for.
>    Action: Ticket f295-01-one-up-set (lead).
> 2. **The test's copy goes too**: `tests/runner/test_requests.py:2636` lists the three states a third time. The ticket makes that test loop over `stacks.UP`. A new test in `tests/runner/test_stacks.py` pins what `UP` holds, so a crashed or stopped app can never count as up without a test going red.
>    Action: Part of f295-01.
> 3. **BROKEN stays on the page**: `stacks_routes.py` also has `BROKEN` (crashed, update failed): the states that offer a card to fix them. Only the page uses it, so moving it would just make `runner/stacks.py` bigger for no gain. It stays where it is.
>    Action: Decision D2 in the card doc.
> 4. **No mock-up**: Nothing on screen changes: the Stop/Run button and Forget behave exactly as they do now.
>    Action: None.
>
> Proposals:
> - F295: one list of an app's up states (plan)
