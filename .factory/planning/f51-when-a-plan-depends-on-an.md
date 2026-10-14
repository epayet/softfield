# F51: when a plan depends on an adr i have approved but is waiting for planner

The planning thread behind F51's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-08 12:47

> when a plan depends on an adr i have approved but is waiting for planner
>
> i can't do anything about it, so it shouldn't count as something on my desk for me to urgently look at (blocked)

## The lead, 2026-10-08 12:53

> I've drafted the F51 plan on `plan/f51`: the milestone doc and two tickets in `tasks/later/`. Nothing is queued until you approve it.
>
> 1. **Why it shows as blocked.** When you press Accept ADR, the runner only applies it at its next pick, which can be most of an hour away. Until then the desk still lists the plan under "Proposals to review", and the Planning tab's count and "Needs you" count it. Its Approve plan button stays greyed out because the ADR isn't Accepted on main yet. So it sits on your desk with nothing you can do about it. *Action:* plan F51 (below).
>
> 2. **Better: let you approve straight away instead of hiding it.** Hiding the plan until the runner accepts the ADR would still make you come back later, when it reappears. The runner applies your requests oldest first, so once you've pressed Accept ADR, Approve plan can be pressed too: at its next pick the runner accepts the ADR, then approves the plan. That's one visit, and nothing is left blocked. The cost is one lead ticket, because the runner's code is protected. It adds a guard: if the ADR's acceptance fails, the plan is refused too, so it can't go through on a Proposed ADR (today it could). The alternative is to only hide the plan until the ADR is accepted: a smaller developer-only ticket, but you'd still need two visits. *Action:* D2 and D3, ticket f51-02 (lead). I recommend this.
>
> 3. **Before you accept: one item, not two.** A card with an ADR and a plan counts as two desk items today, but you can only act on the ADR. With this change the desk shows the ADR alone, ending "· then its plan". You can still send the plan back from its thread. *Action:* D1, ticket f51-01 (developer).
>
> 4. **F16 repeats this card.** It's the same rule: the desk should only count what's still waiting on you. F16's bug is still in the code: a thread you've answered stays in "Your answers wanted" as well as in Coming, until the runner picks up your message. One small fix belongs in the same ticket. *Action:* merge F16 into F51. F16's side question ("what do we call the things on the desk?") moves with it. My answer: keep the words we already use. An idea nobody has asked about yet is a "seed", and the lead's drafts are "proposals". No new word is needed.
>
> 5. **F55 and F56 (dismissing finished conversations) are related but not repeats.** They're about clearing old threads, not about what counts as waiting. *Action:* none; they stay separate.
>
> 6. **Who builds it, and no pause needed.** Ticket 01 goes to a developer (difficulty 3, it follows the existing desk tests). Ticket 02 is mine, because the runner's code is protected. Neither touches a ticket that's already queued, so there's no replan and you don't need to pause the factory.
>
> 7. **If an ADR's acceptance fails.** A failed acceptance doesn't count as done, so the ADR comes back on your desk. With the new guard, its plan is refused rather than approved on a Proposed ADR. *Action:* nothing beyond ticket 02.
>
> 1. **Why it shows as blocked**: Accept ADR is applied only at the runner's next pick, which can be most of an hour away. Until then the plan stays under Proposals to review and is counted, with Approve plan greyed out because the ADR isn't Accepted on main yet.
>    Action: Plan F51
> 2. **Better: let you approve straight away**: Requests run oldest first, so Approve plan can be pressed as soon as Accept ADR has been asked: one visit, nothing left blocked. The runner gets a guard so a plan can't go through on an ADR whose acceptance failed. The cheaper alternative, only hiding the plan until the ADR is accepted, still means two visits.
>    Action: Ticket f51-02 (lead, D2 and D3). Recommended
> 3. **Before you accept: one item, not two**: A card's ADR and plan count as two desk items today; the plan now folds into the ADR's item, which ends 'then its plan'.
>    Action: Ticket f51-01 (developer, D1)
> 4. **F16 repeats this card**: Same rule: count only what still waits on you. F16's bug is still in the code: an answered thread stays in Your answers wanted until the runner picks up your message. Its side question: keep 'seed' and 'proposal', no new word.
>    Action: Merge F16 into F51; the fix goes in f51-01 (D4)
> 5. **F55 and F56 are related, not repeats**: They're about clearing finished threads, not about what counts as waiting.
>    Action: Nothing
> 6. **Who builds it, no pause needed**: 01 goes to a developer, 02 is the lead's (runner code is protected). No queued ticket changes, so no replan and no pause.
>    Action: Nothing
> 7. **If an ADR's acceptance fails**: A failed acceptance doesn't count as done, so the ADR comes back on your desk, and the new guard refuses its plan.
>    Action: Covered by f51-02
>
> Proposals:
> - F51: the desk counts only what you can do now (plan)
> - Merge F16 into F51 (merge)
