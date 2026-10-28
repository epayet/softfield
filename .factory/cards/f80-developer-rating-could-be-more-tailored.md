# Milestone F80: See how each agent does by kind of work before splitting its rating

> **State:** done · **Priority:** 100 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-10-28. Base: git tag `f80-developer-rating-could-be-more-tailored-start`. Report: [`.factory/reviews/f80-developer-rating-could-be-more-tailored.md`](../reviews/f80-developer-rating-could-be-more-tailored.md).
> Planted by the owner on 2026-10-09.

## Notes
developer rating could be more tailored to the type of work (frontend, backend, ios dev, etc.)

## Plan (lead, 2026-10-26)
- **Why not split the rating now:** routing reads a rating only to choose between developers, and since 2026-10-15 one developer has run (local-qwen3.6-35b-a3b, 187 jobs). A rating per kind would route no ticket differently, and it would undo [ADR 15](../adr/15-allowance-aware-routing.md) item 9 (one rating per agent), so it needs an ADR, worth writing only once the numbers below show a gap that would change a pick.
- **What the data says (2026-10-26, coding games, score against what the rating at the time expected):** on softfield, Qwen's page tickets 58% against 57% expected (109 tickets) and its other tickets 76% against 68% (58); on travel-companion, its page tickets 94% against 73% (48). The project moves the gap more than the kind does.
- **Mock-up:** [`f80-mockup/by-kind.html`](f80-mockup/by-kind.html).
- **Tickets:** `f80-01-by-kind-of-work` (developer).

## Decisions
- **D1, the kind of a ticket,** from its `files:` (`tickets.files`): **Pages** when any file ends in `.html`, `.css` or `.js`; else **Code, no pages**. A new kind (Swift, once [F121, Projects not on main or not in Python](f121-projects-not-on-main-or-not.md), lets a project be in another language) is one more suffix rule. `work_kind(files)` lives in `factory_dashboard/agents.py` while only the page reads it; routing by kind would move it to `runner/` under its ADR.
- **D2, a game's score and expectation:** the coding rows of `rating_changes` whose `result` is `merged at the first attempt` (1), `merged later` (0.5) or `not merged` (0); expected is `runner.ratings.expected(before, difficulty)`, the ticket's corrected difficulty when set. Bench games and finding penalties are left out. Both are averaged per agent and kind, shown as whole percentages.
- **D3, the words:** the gap (score − expected, in points) reads "better" above +5, "worse" below −5, else "as rated"; under 3 tickets the row says "too few to say" and is drawn faded.

## Later
- **A rating per kind, in routing:** an ADR once a second developer is in `[roles] developer` and the By kind of work bay shows a gap of 10 points or more over 20 tickets or more in one kind.
- **A rating per project:** the larger gap above (travel-companion +21) may be the project's difficulty scale rather than the agent; the same ADR would weigh it.
