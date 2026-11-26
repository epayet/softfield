# F302: Edit a review's idea in its own plate before planting it

The planning thread behind F302's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-25 20:56

> on factory suggestions i can plant or plant and ask the lead. when i like the idea but want to tweak it a bit, i'd like to have the option to edit the text myself before planting

## The lead, 2026-11-25 21:29

> Your idea plates can get an **Edit first** button. I've drafted the plan, one developer ticket (it passes pre-flight) and a mock-up of F290's review.
>
> 1. **Edit first, on the idea's own plate**: Each idea from a review gets a third button, Edit first, beside Plant and ask the lead and Plant. Pressing it turns the lead's words into a box you can change. The two Plant buttons then send your words, and the plate shows On its way and then links to the new card, as it does today. This is what you did by hand for F303 (the 1,800-lines check from F290's review), and the mock-up uses your own F303 note as the edited text. I recommend editing on the plate itself rather than sending you to the Plant box on Planning: on the plate, the plant stays tied to its idea, so the idea shows Planted afterwards. Your F303 copy wasn't tied to it, which is why F290's idea 1 still offers Plant today.
>    Action: Plan f302 with one ticket, f302-01-edit-an-idea-first.
> 2. **The mock-up: F290's review, Today and Proposed**: Proposed shows idea 1 with Edit first. Press it: the box opens holding your F303 wording, the tag says 'your words', and the lead's original words stay underneath with 'Put them back'. Pressing a Plant button shows the dashed On its way state. An emptied box greys out both Plant buttons.
>    Action: Read .softfield/cards/f302-mockup/edit-before-planting.html; the ticket builds it.
> 3. **The box includes 'From F290's review.'**: The box holds exactly what will land in the new card's notes, including the source line the plant adds today. That way what you see is what you get, and you can delete the line if you don't want it. The other option is to hide it and always add it, but then the box and the card wouldn't match.
>    Action: Decision D4 in the card doc.
> 4. **An edit you don't send is lost on reload**: Edits aren't saved anywhere until you press a Plant button. That's how the Plant box already works, and saving drafts would need a new table for little gain.
>    Action: Decision D5; nothing else.
> 5. **Who builds it, and the risk**: Only the dashboard changes: one template, its CSS and browser tests. The runner already plants any words it is sent. It's small and copies the existing plate tests, so it goes to a developer. The risk is F294's finding that htmx buttons with browser tests have stalled on the local model. If this one does, the runner escalates it to me after its tries.
>    Action: Developer ticket, difficulty 3; nothing more unless it escalates.
> 6. **Where it also shows**: The same plate is used in the review on a card's thread, in the review on its milestone page, and on F59's weekly report once that's built. All three get Edit first from this one change.
>    Action: Nothing.
>
> Proposals:
> - F302: edit a review's idea before planting it (plan)
> - F302 mock-up: edit a review's idea before planting it (mockup)
