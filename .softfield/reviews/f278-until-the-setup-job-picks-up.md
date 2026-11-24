# Review: F278, A new project's M1 waits on the desk while its setup runs, not as a seed

- **Status:** done, signed off by the owner on 2026-11-24.

**Status:** round 1 done, ready for your sign-off. Score 6/10. One blocking point and one should-fix point, both fixed by the review.

### 1. What changed
- When you start a new project, its M1 no longer shows as a seed: from the first minute it sits under "Your answers wanted", dashed and on its way, "waiting for the lead · …".
- It stays there while the setup job runs, even before the lead has written anything, so M1 never drops off the desk; once the lead's first message lands it is the usual "the lead replied …" box.
- While you answer the lead on M1 during the setup, M1 is still one box (the review fixed a second, broken box that showed up then).
- No setup job was open during the review, so the live page couldn't show this; the tests cover it.

### 2. How to test it yourself
1. Start a new project from the Projects page, then open its Planning room on your phone.
2. Before the setup starts: M1 is under "Your answers wanted", dashed, "waiting for the lead · …", and Seeds doesn't list it.
3. Once the setup runs: the same box says "the lead is writing this reply · …", still in "Your answers wanted".
4. After the lead's first message, reply on M1 while the setup is still going: the desk shows M1 once, never a second box.

### 3. Done when, as of now
- **Met:** an open setup job puts its card under "Your answers wanted", dashed and on its way, with or without a thread, and Seeds never lists a card the desk is waiting on.
- **Met:** a finished setup job with the lead's message last shows "the lead replied …"; finished with no thread, the card is a seed again.
- **Your check:** the running setup reads "the lead is writing this reply" (shared code with planner replies; not tested here).

### 5. Decisions made along the way
- **The desk's waiting list is worked out once and handed to both the answers and the seeds.** That keeps the two groups from disagreeing; the ticket only asked that seeds leave those cards out. *Developer, on f278-01.*
- **A setup job's subject is cut at `#`, as a planner's already was.** Live setups answering your message are about `m1#1602`, which the ticket didn't mention; without the cut, M1 showed twice. *The review.*

### 6. What next
- **Factory:** a ticket that touches the queue's subjects should say what they look like on live, since the developer copied the ticket's bare `m1` and missed `m1#1602`.
  > When the lead writes a ticket that reads work_queue subjects, it quotes a real subject from the live database, including the `card#id` forms.

### 8. How the work went
- The local model took three attempts (one no-edit stop, one ruff failure, then a pass after the lead's direction); its code was right for a bare card but missed the `#` form real setup jobs carry. Checking the fixtures against live `work_queue` rows caught it.

<!-- runner report -->
<!-- /runner report -->
