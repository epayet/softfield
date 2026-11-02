# F80: See how each agent does by kind of work before splitting its rating

The planning thread behind F80's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-23 22:27

> Plan this card.

## The lead, 2026-10-26 23:25

> I've planned F80. I recommend measuring first and leaving the single rating as it is for now, so the plan is one developer ticket and a mock-up of a new bay on the Agents page.
>
> 1. **A rating per kind would change nothing yet**: The runner reads a rating only to choose between developers, and since 15 October just one developer has worked: local-qwen3.6-35b-a3b, with 187 jobs. With nobody to choose between, a separate rating for pages, Python or iOS would not change who gets any ticket. It would also undo ADR 15 item 9 (one rating per agent), which needs an ADR. My advice: measure first, and write that ADR when the numbers would change a pick.
>    Action: Ticket f80-01 adds the measurement; the split goes into the card's Later section with a clear trigger (point 5).
> 2. **The project matters more than the kind of work**: I compared each coding result with what the agent's rating predicted at the time. On softfield, Qwen's page tickets scored 58% against 57% expected (109 tickets), so the rating was right. Its tickets without pages scored 76% against 68% (58 tickets). On travel-companion, its page tickets scored 94% against 73% (48 tickets). The biggest gap comes from the project, not from pages against Python. Part of it may be that travel-companion's tickets are estimated as harder for the same work.
>    Action: Both gaps show on the new bay. A rating per project goes into the same later ADR.
> 3. **A new bay on the Agents page: By kind of work**: It goes right after Efficiency. There is one row per agent and kind of ticket, with the number of tickets, the score (merged at the first attempt counts 1, merged later ½, not merged 0) and what the rating expected. A bar shows the score with a tick at the expected value. Each row says 'better', 'worse' or 'as rated' (within 5 points). Rows with fewer than 3 tickets say 'too few to say'. The project and milestone filters apply. The mock-up uses real numbers from the database.
>    Action: Mock-up: .softfield/cards/f80-mockup/by-kind.html, Today and Proposed.
> 4. **How a ticket's kind is decided, and iOS**: The kind comes from the ticket's files. It is Pages when any file is a template, CSS or JavaScript, otherwise 'Code, no pages'. iOS would be one more rule (Swift files), but no project can use Swift yet: F121, Projects not on main or not in Python, has to come first, because the checks only run Python's tools.
>    Action: Nothing for now; when F121 lands, adding the Swift kind is a one-line change.
> 5. **When to split the rating**: Write the ADR once two things are true: a second developer is listed for developer jobs, and the bay shows a gap of 10 points or more over at least 20 tickets of one kind. Until then, one rating stays.
>    Action: Written in the card's Later section.
> 6. **Who builds it**: It is a small ticket outside the protected code, and it follows an existing example (rating_data on the same page), so it goes to the developer. Qwen's softfield page tickets merge at the first attempt only 40% of the time, so expect a retry or two; that is still cheaper than the lead doing it.
>    Action: f80-01, developer, difficulty 4, no dependencies.
>
> Proposals:
> - F80: see each agent by kind of work, before splitting its rating (plan)
> - The Agents page with the By kind of work bay (mockup)
