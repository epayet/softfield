# F241: A phone notification when Claude's limit pauses work, saying when it resumes

The planning thread behind F241's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-11 02:09

> I want a notification when a job has to pause due to Claude lead limit and it should say when it can resume with how many hours in brackets

## The lead, 2026-11-11 06:37

> I drafted F241's plan: one lead ticket that sends a quiet phone notification when Claude's limit pauses work, with the time it resumes and the hours in brackets. There's also one question for you, about the reserve hold.
>
> 1. **Today a Claude limit pauses work without telling you**: When Claude refuses a job for its usage limit, the runner records the refusal and either parks the job or waits. Only the console and the run's report say so: nothing reaches your phone or the desk. It happens about once a day: 11 refusals between 2 and 10 November, two of them the week's limit, which held work for 3 days or more. The only Claude notifications today are the expired login and the 5-hour switch question, and both ask you to do something.
>    Action: f241-01, the lead's ticket (runner/ is protected): send the notification at the refusal, whether the job then parks, waits or gives up.
> 2. **The words, with the hours in brackets**: "softfield · Claude's 5-hour limit: work waits until 22:30 (3 h)". For the week's limit: "Claude's week limit: work waits until Mon 16:00 (77 h)". The weekday shows only when the reset isn't today, and the hours are rounded to the nearest whole hour. Under an hour, the brackets show minutes, "(40 min)", because "(0 h)" would tell you nothing. Tapping it opens the Overview.
>    Action: D2 in the card doc; f241-01's Done when checks each case.
> 3. **The first notification that needs nothing from you**: F114, Notifications only for what needs me, and ADR 31 both decided that a notification means you have something to do. This one only informs you. So it goes to the phone only. It doesn't appear on the desk, where "Needs you" stays for things that do need you, and it doesn't appear as a browser notification.
>    Action: D1, marked as a change to an earlier decision. Approving the plan settles it; no new ADR needed.
> 4. **Quiet by default (my suggestion)**: A limit pause asks nothing of you, so I'd send it without sound or vibration: it waits in the phone's notification list, and the notifications that need you keep their sound. A daily buzz for something you can't act on would make the important ones easier to miss. If you'd rather hear it, say so and it keeps the normal sound.
>    Action: D5: ntfy's low priority, for this notification only.
> 5. **One notification per pause, not per job**: Several jobs often hit the same limit within minutes. On 27 October, Opus and Sonnet were refused 16 seconds apart, and on 22 October three jobs were refused within 3 minutes. The runner checks the refusals it already records, so only the first refusal for a given reset time notifies, in every project. Nothing new is stored. There's no "resumed" notification either: work picks up again by itself at the reset.
>    Action: D3 and D6 in the card doc.
> 6. **Should the week's reserve hold notify too?**: There's a second kind of pause. When Claude's week reaches the reserve kept for you, the runner stops starting lead tickets before Claude refuses anything, while developer tickets keep running. That hold can last days, and today you only see it on the desk. My recommendation: notify it too, once when the hold starts, with the same words ("lead tickets wait until Mon 16:00 (77 h)"), as a second ticket. The alternative is to leave it on the desk only, since it's the runner pacing itself rather than a job being stopped.
>    Action: If you say yes, I add f241-02 (the lead's) to this plan before you approve.
> 7. **No mock-up**: No dashboard page changes, only a notification on the phone. Its words are in point 2.
>    Action: Nothing.
>
> Proposals:
> - F241: a quiet phone notification when Claude's limit pauses work (plan)
