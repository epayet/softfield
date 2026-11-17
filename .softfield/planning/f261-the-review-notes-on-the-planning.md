# F261: A short review on the card's thread, with the whole review one tap away

The planning thread behind F261's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-17 19:48

> The review notes on the planning sign off are a sub part of the whole review but it's a big part and when I look at the whole review I have to scroll down a lot. Keep the important info on planning conversation and then I can dig through the whole review

## The lead, 2026-11-17 19:57

> I've drafted a plan for F261: the review on a card's thread becomes one short plate, with a link to the whole review. There's a mock-up of it, and two tickets that pass the ticket check.
>
> 1. **Where the scrolling comes from**: On a card's thread, the review sits between your note and the conversation, with every part open. On F251, Show how long the computer has been on in the top bar, What changed alone is two paragraphs (about 840 characters), How to test is 5 steps, and 'Decisions waiting for you: None.' comes after that. The last 12 reviews all said 'None.' there. So the lead's latest message starts about a phone screen down.
>    Action: The plate in point 2.
> 2. **The thread keeps what you act on; the rest is behind a link**: The plate shows, in order: 'Needs your answer' (only when a decision really waits for you); 'In short', two lines on what the card does now; a count for Done when (for example '3 met · 1 your check'), writing out only the lines you have to check yourself; How to test, folded with its step count; Sign off; then 'The whole review ›', which says what's there (What changed, the decisions made along the way, what it cost). What changed leaves the thread: it stays in full on the card's page.
>    Action: The mock-up `.softfield/cards/f261-mockup/thread-review.html` (Today and Proposed, with F251's real review), and ticket f261-02.
> 3. **'In short' is a new line the review writes**: The cheaper option is to show the first sentence of What changed. That works for F251, but on most reviews the first sentence covers only one part, and it never says whether the work matches the plan. So I'd have the review write 'In short' itself: at most two lines, the same plate the lead's messages already open with. It costs one small lead ticket for the prompt, and the review writes about 50 more words. Old reviews fall back to the first sentence of What changed.
>    Action: Ticket f261-01, review writes in short (lead).
> 4. **How to test: folded or open?**: I folded it: you test once, but you open the thread many times. Once it's folded, the whole review plate fits in under half a phone screen. The other option is to leave it open, since it's what you do before Sign off. That adds about 5 lines and is still much shorter than today.
>    Action: Folded, unless you say open. It's one line in f261-02.
> 5. **It overlaps F216, A shorter, consistent review page**: F216's decision D13 adds 'Decisions made along the way' to the thread's review, which would make it longer again, and its ticket f216-03 builds that. This plan replaces D13: on the thread, those decisions become a count in the whole review's link. Both tickets wait for F216's (01 for f216-01, 02 for f216-03), because they change the same prompt lines and template. f216-03 does a few lines' work that f261-02 then undoes. That costs less than replanning F216, so I've left F216 as it is.
>    Action: Nothing on F216. The card doc says that D2 replaces F216's D13.
> 6. **Who builds it**: 01 goes to the lead, because the review's prompt is in the protected `runner/` folder. 02 goes to a developer: it's a template, `thread.py` and some CSS, and it follows two examples already on the same page (the lead message's In short plate and the thread's folds). On the board, F261 sits behind F216, so it can't start before F216 is done anyway.
>    Action: Approve the plan. The tickets queue in F261's place on the board.
> 7. **Pictures for the review**: The card doc lists `/planning/f251` and `/planning/f216` under Before and after. The review will take pictures of them and check them against the mock-up.
>    Action: Nothing.
>
> Proposals:
> - A short review on the card's thread (plan)
> - F261 mock-up: the review on a card's thread (mockup)
