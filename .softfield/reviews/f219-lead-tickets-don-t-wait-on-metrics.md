# Milestone F219-LEAD-TICKETS-DON-T-WAIT-ON: runner metrics

- Tasks merged: 3; escalated at least once: 0 (escalation rate 0%)
- Attempts per task: [1, 1, 1] (average 1.0)
- Review rounds: 2; actionable findings per round: [1, 0]
- Headless Claude runs: 8
- Loop stopped because: restart

**Who did the work in F219-LEAD-TICKETS-DON-T-WAIT-ON.** The local model built 3 task(s) (one-lead-rule, rewrite-f9-29, review-waits-for-held-fixes) using 0 tokens, free on your GPU. Claude spent **≈2.5M token-equivalents** over 96 steps (≈26k a step; 39% of it re-reading the conversation). That includes preparing, reviewing and fixing the local model's work. Doing those 3 tasks directly would have cost Claude roughly **391k** (about 5 steps each at today's step cost), **16%** of what it spent. Delegating only saves allowance when preparing a task costs Claude less than that.
