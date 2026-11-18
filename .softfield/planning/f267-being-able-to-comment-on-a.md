# F267: Add notes to a thread while the lead is still writing its reply

The planning thread behind F267's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-18 07:34

> Being able to comment on a thread even though the lead is replying right now would be helpful even if it looks at it after it finishes what it's doing. In normal Claude chats you can steer it while it's doing something. It might not be up to that point but at least if I forgot something I can keep adding notes in the same thread that will be looked at at some point

## The lead, 2026-11-18 07:38

> The thread page hides its message box while the lead owes a reply, but the runner already accepts later messages. So the plan is: always show the box, and answer all the notes waiting on a thread in one reply. I've drafted the plan, two tickets and a mock-up, and both tickets pass the ticket check.
>
> 1. **Why you can't write now**: Only the page stops you. The thread page hides its box whenever the lead owes a reply. While this reply was being written, /planning/f267 showed 'the lead is writing this reply' and no box. The runner already handles a second message: it waits as 'Sent', you can still edit or cancel it, and the runner takes it at its next pick, right after this reply.
>    Action: Ticket f267-02 (developer): the box stays on the page, labelled 'Add a note · the lead reads it after this reply'.
> 2. **Several notes get one reply, not one each**: Today each message gets its own lead reply. If you sent three notes while the lead was writing, you would get three more replies, about $3.50 each (the average of 158 replies since 1 Nov). Worse, the first of those replies would be written without seeing your other two notes. I recommend that every note waiting on a thread when the lead starts goes into one reply. For the 'I forgot something' case, that's exactly what you want.
>    Action: Ticket f267-01 (lead, in the runner): one reply answers every note waiting on its thread, in the order you sent them.
> 3. **Steering a reply while it's being written: not planned**: In a normal Claude chat you can interrupt. Here each reply is a job that gets its instructions once. Adding a note mid-reply would mean changing how every Claude job is started, to win a minute or two on a reply that takes about 3 minutes. Your note is read right after, together with any others you added.
>    Action: Nothing. If replies get much longer, we can look at this again.
> 4. **Comments on points still wait for the reply**: While a reply is owed, the points on the page are the ones the lead is about to replace. So their comment boxes stay hidden until the new reply lands, as today. A free note works at any time.
>    Action: In D1. Tell me if you'd rather comment on the old points too.
> 5. **The picture**: Today and Proposed of /planning/f267 while the lead writes. Proposed shows your note waiting with a dashed edge, 'Sent · the lead reads it after this reply', with Edit and Cancel it, and under it the box as a striped plate. A calmer option is today's plain box with the new words.
>    Action: Mock-up .softfield/cards/f267-mockup/note-while-writing.html, named in f267-02.
>
> Proposals:
> - F267, Add notes to a thread while the lead is still writing its reply (plan)
> - F267 mock-up: add a note while the lead writes (mockup)
