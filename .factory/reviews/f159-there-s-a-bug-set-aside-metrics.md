# Milestone F159-THERE-S-A-BUG-SET-ASIDE: runner metrics

- Tasks merged: 3; escalated at least once: 0 (escalation rate 0%)
- Attempts per task: [1, 1, 1] (average 1.0)
- Review rounds: 1; actionable findings per round: [2]
- Headless Claude runs: 3
- Loop stopped because: a finding came back a third time

**Who did the work in F159-THERE-S-A-BUG-SET-ASIDE.** The local model built 3 task(s) (set-aside-ticket-page, ticket-notes-keep-their-lines, fix-queue-answer-and-wrapped-done-when) using 10.5M tokens, free on your GPU. Claude spent **≈751k token-equivalents** over 63 steps (≈12k a step; 54% of it re-reading the conversation). That includes preparing, reviewing and fixing the local model's work. Doing those 3 tasks directly would have cost Claude roughly **179k** (about 5 steps each at today's step cost), **24%** of what it spent. Delegating only saves allowance when preparing a task costs Claude less than that.
