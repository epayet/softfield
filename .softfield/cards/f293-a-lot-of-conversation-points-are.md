# Milestone F293: The planner stops telling the owner what they already know

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-24.

## Notes
A lot of conversation points are things that I already know I don't need to be told again like 
Accept the rule before approving the plan
The ticket depends on ADR 52 -- waste of my time

## What we found
Three threads in one evening spent a point (and a line of "In short") telling the owner to accept an ADR before approving the plan: F282 (point 3), F286 (point 4), F292 (point 5). Approve already refuses a plan whose ADR is still Proposed and says why on the desk (`runner/requests.py`, `ticket_problems` and `_proposed_adrs`), so the point tells them nothing. "No mock-up" was its own point nine times since message 1100, mostly on cards with nothing on screen, where the brief asks for no point at all.

## Decisions
- **D1. One rule in the planner's brief.** `_PLANNER_HEAD`'s "How to answer" (`runner/prompts.py`) gets one bullet: tell the owner only what they don't already know. No point, and nothing in the lines before the block, about how the dashboard's buttons work or the order to press them: accept an ADR before its plan, a ticket relies on ADR N, the plan waits for Approve, nothing is queued before it. The dashboard says these itself and refuses an approval out of order with its reason. A real choice stays a point, such as "if you turn the ADR down, the plan loses f292-02".
- **D2. "No mock-up" only where a page changes.** The mock-up bullet already says to explain a skipped mock-up only on a card with screen changes. It gains a few words: work with nothing on screen gets no point about a mock-up.
- **D3. The owner's preference, dated.** `runner/instructions/author/owner.md` gets the rule under "Reporting" (2026-11-24, F293), so terminal sessions follow it too.
- **Builds on and removes:** the existing brief only. No new mechanism, so nothing becomes removable. The pause point and the "can't take pictures yet" point stay: each one asks for something or warns about a real cost.
