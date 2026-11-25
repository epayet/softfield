# Milestone F295: One list of an app's up states, for the Forget guard and the Stop button

> **State:** idea · **Area:** factory
> Planted by the owner on 2026-11-24.

## Notes
runner/requests.py's _forget_project lists the app's "up" states itself while factory_dashboard/stacks_routes.py has UP for the same set: move UP into runner/stacks.py and use it from both, so Forget's button and the runner's guard can't drift apart. From F273's review.
