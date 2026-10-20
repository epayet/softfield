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

## The lead, 2026-10-20 11:15

> Merged F157 here: The owner asked whether archiving F156 (merged into F135) also archived F135. Answer: no, Archive touches only its own thread. F135 was archived separately by the owner four minutes later, and its ticket f135-01 still runs. They also asked about the tickets for 'smarter actions' (Approve ADR then Approve plan at once), which are F51's f51-01 and f51-02. Nothing is still open.

## The owner, 2026-10-20 11:15

> From F157, merged here:
> if i archive something that got merged, it does'nt archive the merged plan right? i just archived f156, so just checking. there are tickets i believe about being smarter when doing actions (approve adr means approve plan for example)

## The lead, 2026-10-20 11:15

> Merged F99 here: When a proposal has bundled things like both a mock-up and…

## The owner, 2026-10-20 11:15

> From F99, merged here:
> When a proposal has bundled things like both a mock-up and and a plan. Bundle them in tbr planning list too. Right now it looks like I have 2 things to look into but one approval approves both. Like the current both f54

## The lead, 2026-10-20 11:26

> I folded F99, Bundle a mock-up with its plan, into F51: the desk would show one item per card. Below is a mock-up of the desk and a replan of f51-01.
>
> 1. **Archiving a merged card leaves the card it joined alone**: Right: Archive only touches the thread you press it on. Archiving F156 didn't archive F135, Reviews stop at once; you archived F135 yourself four minutes later. F135's ticket f135-01 still runs: archiving hides a conversation, not its work.
>    Action: Nothing
> 2. **'Accept ADR means approve plan' is f51-02, with two presses, not one**: f51-02, Approve plan once Accept ADR is asked, lets you press Approve plan as soon as you've pressed Accept ADR. At the next pick the runner accepts the ADR first, then approves the plan. I'd keep these as two presses rather than have one press do both. An ADR is a rule for all later work, and a plan is one card's tickets. You sometimes accept an ADR and still send its plan back, and a single button would take that choice away. Both presses happen on the same visit, so you don't have to come back.
>    Action: Nothing: f51-02 stays as it is
> 3. **One desk item per card, F99 included**: Your desk today has ten 'Proposals to review' for five cards. F27, Planning beside the line, has ADR 27, a plan and a merge of F34. F154, F158 and F159 each have a plan and a mock-up, and F153 has a plan alone. One Approve plan settles a card's plan, mock-ups and merges together, so five of the ten aren't real extra work. Proposed: one item per card. It lists the card's parts in the order you settle them (ADR first), says 'accept the ADR first' while the ADR is open, and links to the first part still to do. It counts until every part is on its way, then goes dashed. Your desk count would drop from 80 to 75. The general thread's seeds stay one item each, because each is planted by its own press.
>    Action: Rework f51-01 (replan) to this picture
> 4. **The mock-up**: Today is the desk's list as it stands, copied from the live template. Proposed shows the same five cards as one item each, plus F27's item before and after you press Accept ADR. Parts on their way use the desk's existing dashed orange, so no new colour.
>    Action: Review the mock-up
> 5. **Pause first if you want to be safe**: f51-01 is ready, at priority 7, behind about thirty tickets, so the line is unlikely to start it while we talk. If you'd rather be certain, pause the factory from the dashboard. Approving the replan lifts your pause.
>    Action: Optional: pause from the dashboard
>
> Proposals:
> - F51: one desk item per card, counted only while it waits on you (replan)
> - Your desk: one item per card (mockup)

## The lead, 2026-10-20 11:26

> Your F99 note was already covered in my last reply on this thread, so this reply changes nothing and the earlier proposals stand.
>
> 1. **F99's bundling is already in F51's replan**: My last reply on this thread already covers this note. The replan makes each card's open proposals one desk item: plan, mock-ups, merges, and the ADR when there is one. It lists the parts in the order you settle them, counts the item while any part still waits on you, and goes dashed once every part is on its way. The mock-up shows the desk with today's ten proposal items as five. Nothing has changed since, so the replan and the mock-up are still waiting for your Approve.
>    Action: Review and approve the replan (f51-replan) and the mock-up (f51-mockup) already listed on this thread
> 2. **Your example is F154, not F54**: F54, the reprioritise arrows that did nothing, is archived and has no proposals. I think you meant F154, One Planted column, a growing tag, and stages that say what comes next. It has a plan and a board mock-up that one Approve plan settles together, and it's one of the five bundled items in the mock-up's Proposed view.
>    Action: Nothing

## The owner, 2026-10-20 22:05

> How do I approve replan? There's nothing linked to this card and on f51 it just says 'replaced by a newer rrsplnse' or something

## The lead, 2026-10-20 22:06

> That was my fault: my last reply sent an empty list of proposals, which hid the replan and the mock-up. This reply lists them again, plus a small fix so it can't happen again.
>
> 1. **Approve it from this reply's buttons**: My previous reply listed no proposals. It was meant to leave the earlier list standing, but it was stored as an empty list. The thread page takes that as a newer list, so the replan and the mock-up showed 'replaced by a newer reply' and lost their buttons. Your desk still listed them, because it skips empty lists. Both are listed again below, unchanged: the replan of f51-01 (one desk item per card) and the desk mock-up. Approve them from here.
>    Action: Approve the replan and the mock-up below
> 2. **A fix so an empty reply can't hide proposals again**: The desk ignores a lead reply with an empty proposal list, but the thread page and the proposal pages don't. New ticket f51-03, Empty list keeps proposals (developer, difficulty 2): those pages read lead replies the way the desk does, so a reply without proposals no longer hides the earlier ones. A reply with new proposals still replaces the old list, as now. I've added it to this replan. It's the same file f51-01 changes, and it's about the same thing: what's still waiting on you.
>    Action: Ticket f51-03 in the replan
> 3. **Pause first if you want to be safe**: F51 is now priority 14, behind about forty ready tickets, so the line won't reach f51-01 while you read this. Pause from the dashboard only if you want to be certain. Approving the replan lifts the pause.
>    Action: Optional: pause from the dashboard
>
> Proposals:
> - F51: one desk item per card, counted only while it waits on you (replan)
> - Your desk: one item per card (mockup)
