# Milestone F295: One list of an app's up states, for the Forget guard and the Stop button

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-24.

## Notes
runner/requests.py's _forget_project lists the app's "up" states itself while factory_dashboard/stacks_routes.py has UP for the same set: move UP into runner/stacks.py and use it from both, so Forget's button and the runner's guard can't drift apart. From F273's review.

## Decisions
- **D1:** `UP` lives in `runner/stacks.py`, beside the state words it groups. The Projects page (`factory_dashboard/stacks_routes.py`) and Forget's guard (`runner/requests.py`) both read it from there. Nothing new is built: the constant moves, and the page's own copy and the guard's inline list both go.
- **D2:** `BROKEN` (crashed, update failed) stays in `stacks_routes.py`: only the page uses it.

## Tickets
- f295-01-one-up-set (lead: `runner/` is protected)
