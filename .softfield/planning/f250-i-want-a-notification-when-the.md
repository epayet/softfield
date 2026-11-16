# F250: Tell the phone when the factory is done for the week, so you can switch off

The planning thread behind F250's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-14 12:40

> I want a notification when the factory is completely done for the week. No more tokens and no more dev work available. That means I can shut down my computer

## The lead, 2026-11-16 19:31

> I've drafted the plan for F250: the runner, which already goes round every project, sends one phone notification once nothing can start on its own for 12 hours or more. Two tickets are in `later/`, and both pass pre-flight.
>
> 1. **Last weekend shows the gap**: Claude's week limit stopped work on Sat 14 Nov at 10:33. The developer finished its last ticket at 12:40. After that nothing ran in any project for about 51 hours, until Mon 16:00, and nothing told you.
>    Action: Ticket f250-01: when nothing can start, the runner sends one notification, for example: "Softfield · Done until Mon 16:00 (51 h): Claude's week is used up. You can switch off." Tapping it opens the Overview.
> 2. **What counts as "done"**: It's the whole factory, not one project. The runner checks every project in turn, and it sends the notification when all of these are true: nothing ran in any project, your pause is off, and every project's remaining work is either waiting for Claude for 12 hours or more, waiting for you, or doesn't exist. A 5-hour window ends within 5 hours, so a 12-hour wait means the week's limit. Work that waits only for you doesn't send it on its own, because those items already notify you. The state must last 10 minutes, so a job that starts a minute later stops it. It's sent once, and any job that runs sets it up to send again next time.
>    Action: Decisions D1 and D4 in the card, built by f250-01.
> 3. **Why not the notification at the limit (F241, "A phone notification when Claude's limit pauses work")**: F241 notifies when Claude refuses a job. At that moment the developer may still have hours of work (two hours last Saturday), so switching off then would lose that work. This card waits until there's really nothing left to run. It uses F241's time format (weekday, hours in brackets), so it waits for f241-01, which is already ready.
>    Action: f250-01 depends on f241-01.
> 4. **Answer what waits for you before you switch off**: If something waits for you in any project, the notification adds " · 3 things wait for you". A sign-off or a reply can free work that the developer can do without Claude, so it's worth answering those before switching off.
>    Action: D3, in f250-01.
> 5. **Risk: the factory can't start again until you switch back on**: If the computer is off when Claude's week resets, the factory loses time until you switch it back on. The notification gives the exact time to be back. After a restart the runner starts by itself only if you enabled the services that `softfield service install` writes. Another option is to have the computer suspend instead of shutting down and wake itself at the reset (rtcwake). That changes the machine's own settings, so I've left it out of this card. To keep it, plant: "Wake the computer by itself at Claude's reset, so a weekend shutdown loses no factory time".
>    Action: Nothing in this card. Plant the idea above if you want it.
> 6. **When Claude still has your reserve**: Lead work sometimes stops because the week is down to the 25% kept for planning, not because it's all gone. Then the notification says "Claude's week is down to your reserve" instead of "used up". That way you know turning the reserve switch on would buy more work before you switch off.
>    Action: D3, in f250-01.
> 7. **The browser's "All work done" goes**: Today the browser shows "All work done" separately for each project, and only while a dashboard page is open. The new phone notification covers the whole factory, including the case where every queue is empty ("All work done: nothing is ready. You can switch off."). Keeping both would give you two notifications for the same moment.
>    Action: Ticket f250-02 (developer) removes the browser one.
> 8. **No mock-up**: No dashboard page changes. This is only a phone notification, and D3 in the card gives its exact words.
>    Action: Nothing.
>
> Proposals:
> - F250: a phone notification when the factory is done for the week (plan)
