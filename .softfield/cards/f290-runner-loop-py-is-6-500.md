# Milestone F290: Split runner/loop.py into one module per job kind, with no change in behaviour

> **State:** idea · **Area:** factory
> Planted by the owner on 2026-11-24.

## Notes
runner/loop.py is 6,500 lines and grows three lines for every one removed: plan splitting it by job kind (developer tickets, lead tickets, planner, reviews, waits) with no change in behaviour, one module per ticket.
