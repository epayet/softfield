# F165: A point that speaks of a mock-up opens it in one tap

The planning thread behind F165's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-21 08:57

> there's been a few conversations where it says 'on the mockup you can see...' but with no links to the mockup. why is that and how come it can happen

## The lead, 2026-10-21 09:05

> I've traced three causes; two already have tickets queued. Below is a plan for the third, with a mock-up.
>
> 1. **Why it happens: three different gaps**: First, the lead sometimes draws a mock-up and lists only the plan, so the dashboard has nothing to link (F152's first reply, 20 October). Second, a reply with an empty list of proposals hid a mock-up listed earlier: on F51 it showed 'replaced by a newer reply'. Third, and the most common: even when the reply does list the mock-up, the points never link to it. Each point stores which proposal it leads to, but the thread page only draws its title, answer and action. The only way in is the 'Proposals from this card' list, which on a phone sits under the reply box, the earlier messages and Archive. Across all threads, 47 of the lead's points that talk about a mock-up name no proposal at all.
>    Action: See points 2 to 4.
> 2. **Gaps one and two are already fixed in queued tickets**: For F152, A done card says where its review is: ticket f152-02, Every mock-up is listed (ready, priority 5). After each planner job the runner adds any mock-up file the reply forgot to list. For F51, When a plan depends on an ADR: ticket f51-03, Empty list keeps proposals (ready, priority 14). A reply with no proposals no longer hides the earlier ones.
>    Action: Nothing: both run on their own.
> 3. **How the third gap slipped through**: F31, Proposals close the loop, planned this link in its ticket f31-04, What to do now. That ticket was set aside to wait for a mock-up, and the mock-up was never drawn. F31 was then signed off with f31-04 still set aside, so the link never got built. That's my miss: the review should have flagged a set-aside ticket that a decision still relied on.
>    Action: This card builds the link on its own. The rest of f31-04 (points coloured by outcome, 'What to do now' under the reply) stays set aside.
> 4. **Fix: a point opens what it talks about**: Under a point's action there is now a plate, 'Open the mock-up' (or plan, ADR, replan), edged in that proposal's colour and showing where it stands. One tap opens the proposal's page. Points with no proposal look as they do today, and the list at the bottom stays. Developer ticket f165-01, difficulty 3.
>    Action: Ticket f165-01, Point opens its proposal; see the mock-up.
> 5. **The mock-up: F51's real reply on a phone**: Today: point 4 says 'Review the mock-up' with nothing to tap, and the mock-up is a full screen further down. Proposed: points 3 and 4 each get their 'Open the …' plate, marked in dashed green. On a wide screen, Today and Proposed sit side by side.
>    Action: Review the mock-up.
> 6. **And the lead always names the mock-up**: A link only works if the point names its mock-up, and today the lead often doesn't. The planner's prompt will say: every listed mock-up gets a point of its own with its id, and a point that leads to a proposal always names it. The prompt is the runner's code, which is protected, so this one is the lead's ticket (difficulty 2). I'm not adding a runner check that refuses replies missing such a point: a refused reply costs a whole planner job, and f152-02 already catches mock-ups that were never listed.
>    Action: Ticket f165-02, Every mock-up has its point.
> 7. **No pause needed**: Both tickets are new and touch no ticket that is already queued. Nothing runs before you approve.
>    Action: Nothing.
>
> Proposals:
> - F165: a point opens the mock-up it talks about (plan)
> - Thread points open their mock-up (mockup)

## The owner, 2026-10-21 09:30

> Is this just adding inline links to plans abd proposals for when the global links didn't work? I don't really want inline links, I just want to make sure the global links work. There's been times where mockups were mentioned but no link anywhere

## The lead, 2026-10-21 09:34

> Agreed: no links inside points. I've rewritten the plan so the card's own list of proposals always carries its mock-ups, and so each one opens with its picture.
>
> 1. **Yes, it was inline links, and they're gone**: The first draft only added a link on each point, plus a prompt rule to go with it. That doesn't fix what you saw, so I dropped both. The plan now makes sure the card's own list ('Proposals from this card', and the tabs on a proposal's page) always has every mock-up, and that each one opens with its picture.
>    Action: Plan rewritten, see below.
> 2. **Why a mock-up can have no link anywhere: four ways**: 1) The lead draws it and lists only the plan: this happened on F152, A done card says where its review is. 2) A reply with an empty list hid it: this happened on F51, When a plan depends on an ADR. 3) A later reply lists only the plan and forgets an older mock-up, which then drops out of the list. 4) The link is there but the page is blank: mock-ups listed before the October move are stored under their old folder, and the review page no longer reads that path. F8, F17, F65, F67, F68 and F94 open their mock-up page with no picture, though every file is still there. Check F67's mock-up page: you'll see key points with nothing above them.
>    Action: Ways 1 and 2 already have tickets queued (point 3). Ways 3 and 4 are this card.
> 3. **Already queued: drawn but not listed, and the empty list**: f152-02, Every mock-up is listed, is ready at priority 5: the runner lists any mock-up the lead drew and forgot to list. f51-03, Empty list keeps proposals, is ready at priority 14. If you want the empty-list fix sooner, drag F51, When a plan depends on an ADR, up the board.
>    Action: Nothing, unless you want F51 moved up.
> 4. **Fix: old mock-ups show their picture again**: The review page reads an old-folder path from the folder the file lives in now, so the six mock-ups show again. F54's file was never kept anywhere, so its page will say so plainly instead of showing nothing. Developer ticket, difficulty 2.
>    Action: Ticket f165-01.
> 5. **Fix: a mock-up never drops out of the list**: When a reply lists proposals, the runner adds every mock-up on the card's branch that the reply forgot, even one drawn on an earlier turn. It builds on f152-02, so it's a lead ticket, difficulty 3, and runs after f152-02.
>    Action: Ticket f165-02.
> 6. **The mock-up: F67's review page today, and with the fix**: Today shows F67's real page, with key points and no picture. Proposed shows the picture back, plus the line F54's page would show. I've redrawn the earlier mock-up file in place, because I can't rename or remove files from here.
>    Action: Review the mock-up.
> 7. **The two tickets keep their first names**: A planner job can't rename or delete a file, so the tickets are still named 'point-opens-its-proposal' and 'every-mockup-has-its-point', from the draft you turned down. Each ticket's goal says what it really does. This changes nothing about how they run.
>    Action: Nothing.
>
> Proposals:
> - F165: every listed mock-up shows, with its picture (plan)
> - F165: every listed mock-up shows its picture (mockup)
