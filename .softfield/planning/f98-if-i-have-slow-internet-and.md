# F98: A pressed button shows it is sending, and the same press is taken once

The planning thread behind F98's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-23 23:56

> Same for thinks Luke remove or other buttons

## The lead, 2026-10-27 04:09

> I drew the mock-up (`.softfield/cards/f98-mockup/pressed-buttons.html`), wrote the plan and its Decisions in F98's card doc, and drafted two tickets. Both tickets pass the ticket checks.
>
> 1. **Yes: every button, not only Plant**: I read the code and Plant isn't the only one. Every button that asks the runner something does nothing visible until the factory answers: Remove seed, Save, Cancel it, Dismiss, Send, Send back, Accept ADR, Queue it. During that wait, on a slow connection, a second press sends the request again. A few buttons already react on their own (Pause, Archive, Sign off, the reserve lever, Approve plan, Reject). So instead of fixing buttons one at a time, one rule in the page frame covers them all, including any button added later. The pressed button gets a dashed yellow edge, its own word ('Planting…', 'Removing…') and a yellow-and-black belt moving under it. The other buttons wait and the text box is locked. The buttons that already react keep doing what they do.
>    Action: Ticket f98-02-pressed-button-sends (developer), built from the mock-up.
> 2. **When no answer comes**: If the factory refuses the request, the connection drops, or nothing comes back within 30 seconds, the button comes back. A red line says 'Didn't hear back from the factory. Your note is still here: press again, it won't be planted twice.' Your words stay in the box.
>    Action: Part of f98-02.
> 3. **Going further than you asked: the factory takes the same press only once**: Locking the button stops double presses while you wait. It doesn't help when your plant reached the factory but the answer got lost, for example a phone switching networks. Then you see 'press again', press, and get a second card. That is probably how your duplicates happened. Fix: if the same request (same kind, same card, same words) comes in less than 60 seconds after the last one, the factory stores nothing new and answers with the first one. It only compares with the very last request, so Pause, Resume, Pause still counts as three. That code is protected, so it's a lead ticket. It costs one extra ticket. Without it, the 'press again' message would be a risk.
>    Action: Ticket f98-01-same-press-taken-once (lead), which goes first.
> 4. **The moving belt is a status, not decoration**: The theme rule says decoration never moves. The belt is allowed to move because it means something: 'your press is on its way'. It sits next to the dashed yellow edge that already means 'on its way' elsewhere on the dashboard. It joins the colour settings as a new token, and it stops moving for anyone whose device is set to reduce motion. If it feels like too much, the calmer option is the dashed edge and the word, without the belt.
>    Action: Nothing, unless you'd rather have the calm version.
>
> Proposals:
> - Pressed buttons: Plant and Remove seed, Today and Proposed (mockup)
> - F98: a pressed button shows it is sending, and the same press is taken once (plan)
