# F208: Let a local attempt finish its step before the no-edit stop

The planning thread behind F208's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-03 16:01

> there's been a few 'no edits after 20 minutes' failed attempts, i suspect that the local models sometimes need mor etime legitly as the project becomes more complex

## The lead, 2026-11-03 16:07

> The numbers show your hunch is only partly right, so the plan gives attempts one more step instead of raising the limit.
>
> 1. **More time is the answer for only some of these stops**: Since the stop moved to 20 minutes on 16 October, 64 attempts have hit it. 39 of them came on 29 and 30 October, when the model wrote 1.7 tokens a second instead of its usual 21 to 30. More time wouldn't have saved those. The other 25 are about 13% of about 190 attempts, under the quarter that F93, Developer attempts get 20 minutes, set as the sign that tickets are too big.
>    Action: Don't raise the limit across the board. See points 3 and 4.
> 2. **You're right that the project's size costs time**: Three files (planning.py, test_planning.py, planning.html) come to 40,000 tokens, 160 seconds in a single step. f170-04 read 61,000 tokens in one step, 4 minutes. Today's three first edits came at 8.5, 10.8 and 12 minutes, against a middle of 6.3 in October. That's later, but still well under 20, and it's only three attempts.
>    Action: No change now. The review in point 5 watches this.
> 3. **Today's two stops were cut in the middle of one long thought**: f170-05 spent 15.5 minutes on one step, about 21,000 tokens at a healthy 23.5 a second, with no tool call. f170-04 spent 14 minutes the same way and was at 129,335 of 130,304 tokens of context when cut, so it had almost no room left anyway. f170-05's next attempt started the same way, took 3 seconds on that step, and passed at 42 minutes. Nobody can tell whether those thoughts were useful, because a thought is only saved when its step ends. The repeat stop reads the same saved text, so it can't see a thought in progress either, and it has stopped nothing since 16 October.
>    Action: Ticket f208-01: a stopped attempt keeps its thinking, and a long thought now gets to finish, so it can be read.
> 4. **Better than a higher number: finish the step in hand**: At minute 20 with no edit, the attempt finishes the step it's on, and no later than minute 35. If that step ends without an edit, it stops. A flat 30 would give an attempt that's only reading 10 more minutes, while this gives it one more step and gives a long thought the room it needs. The cost is at most 15 more minutes of the GPU per attempt, 45 for a ticket that loses all three. It can't promise to save an attempt: whether those thoughts end in good edits is exactly what we don't know yet.
>    Action: Ticket f208-01, for the lead because the runner's code is protected. Nothing changes on screen, so no mock-up.
> 5. **How we'll know it worked**: At the factory's periodic review: how many attempts edited or passed after minute 20, and what the saved long thoughts say. If almost none did, it goes back to a plain stop at 20. If the thoughts go round in circles, that becomes a new card.
>    Action: Recorded as D3 on this card.
> 6. **The slow days cost the most, and nothing told you**: From 29 October to 04:00 on the 30th, directions and escalations came to 26 jobs and $27.64, and the 39 stopped attempts held the GPU for 13 hours. Nothing on the dashboard said the model had slowed down. It looks like what you saw with the KV cache in system memory, though the logs don't show that setting. Speed has been normal since 2 November. My fix is for the runner to read the speed from an attempt's first steps. Below about 5 tokens a second, it would hold local work without using up an attempt and put a line on your desk. That also needs a decision on what the line does while held, and it's your question on F195, I've reduced the context window, so I'd plan it there. The prompt cache misses in point 7 go there too.
>    Action: Recorded as D4 on this card, to go into F195's plan. If you'd rather have it here, say so and I'll add the ticket and its mock-up.
> 7. **An open cost: some steps re-read everything**: On 28 October, f81-03 kept re-reading about 40,000 tokens or more per step because LM Studio's prompt cache missed, so each step took 2 to 3 minutes and it got through only 7 to 10 steps in 20 minutes. I don't know why the cache missed yet. Your context settings stay as they are.
>    Action: Find the cause in F195's plan, along with point 6. Nothing to do here.
>
> Proposals:
> - F208: let a local attempt finish its step before the no-edit stop (plan)
