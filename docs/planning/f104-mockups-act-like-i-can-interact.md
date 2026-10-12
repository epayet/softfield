# F104: Mockups act like I can interact with but I can't, f54 is…

The planning thread behind F104's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-10 19:10

> Mockups act like I can interact with but I can't, f54 is blocked because of that

## The lead, 2026-10-10 19:12

> The cause is in the code and the fix is drafted as one small lead ticket on `plan/f104`; F54's mock-up can be used today from its own address (point 2).
>
> 1. **Why the mock-ups don't answer**: The review page shows a mock-up inside a frame that turns its scripts off (a bare `sandbox` on the iframe in `factory_dashboard/templates/proposal.html`). Every button in a mock-up is script. F54's mock-up draws its whole queue, its five option tabs and its Refresh / Reload / Runner's next pick buttons that way, so in the frame you see the tabs, pressing them does nothing and the queue is empty. The mock-up itself is fine.
>    Action: Ticket f104-01 (the lead, difficulty 2): the frame lets scripts run.
> 2. **Unblock F54 now, without waiting**: The mock-up's own address already runs its scripts; only the frame blocks them. Open the dashboard's address followed by `/planning/mockups/f54/docs/milestones/f54-mockup/moves.html` in a new tab. The options, the arrows and the three buttons should work there. I read this from the code and have not opened it in a browser. Then choose on F54's thread as usual.
>    Action: Nothing to build: open that address, then answer on F54.
> 3. **Half of this is already queued in F42**: F42 found the same thing on 2026-10-08. Its ticket f42-01 adds an "Open the mock-up" link that opens it full screen with scripts on, and on a phone that link replaces the frame. It is in the queue, not built. So on a phone F42 already fixes your complaint. On a wide screen F42 keeps the frame, still dead. F104 adds only that missing part.
>    Action: Keep F42 as it is; F104 is one ticket that runs after f42-01.
> 4. **Why I don't propose merging F104 into F42**: A merge moves only your note. The wide-screen gap would then need another round on F42's thread, and I can't change F42's queued tickets from here. One small card with one ticket closes it in a single approval. If you would rather have one card, say so and I'll propose the merge, and the gap becomes a replan on F42.
>    Action: Nothing, unless you prefer the merge.
> 5. **To get it sooner, move f42-01 up**: f42-01 sits at priority 100 with most of the queue, and it waits for f12-03 (the review probe's removal). f104-01 waits for f42-01, because both change the same lines. Raising f42-01 and f12-03 brings both fixes forward. The arrows do work: the runner applies them at its next pick, which is F54's whole subject.
>    Action: Your choice: press ↑ on f12-03 and f42-01 in Next in line, or leave the order.
> 6. **Security: what a mock-up's script may do**: The frame gets scripts and nothing else. The mock-up stays in an origin of its own: it can't read the page around it, and anything it posts carries `Origin: null`, which `/requests` already refuses (tested). It never gets `allow-same-origin`, which would let a mock-up press Approve as you. This is what f6-08 already decided for the mock-up's own address; the frame was just stricter than meant. I decided it rather than raise an ADR, as it adds no new permission.
>    Action: In ticket f104-01, with a test in a real browser that fails on any wider permission.
> 7. **No mock-up for this card, and one check not run**: This restores how the page was meant to behave, so there is nothing new to draw. I could not run the ticket's pre-flight from this job (no runner command allowed here); I checked its paths and names against the code by hand.
>    Action: Nothing: the runner's pre-flight runs when the plan is approved.
>
> Proposals:
> - F104: a mock-up's buttons work in the review page (plan)
