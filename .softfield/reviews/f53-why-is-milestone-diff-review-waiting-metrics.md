# Milestone F53-WHY-IS-MILESTONE-DIFF-REVIEW-WAITING: runner metrics

- Tasks merged: 2; escalated at least once: 1 (escalation rate 50%)
- Attempts per task: [1, 3] (average 2.0)
- Review rounds: 1; actionable findings per round: [1]
- Headless Claude runs: 7
- Loop stopped because: a finding came back a third time

**Who did the work in F53-WHY-IS-MILESTONE-DIFF-REVIEW-WAITING.** The local model built 2 task(s) (park-the-review, parked-review-crate) using 6.6M tokens, free on your GPU. Claude spent **≈2.9M token-equivalents** over 125 steps (≈23k a step; 40% of it re-reading the conversation). That includes preparing, reviewing and fixing the local model's work. Doing those 2 tasks directly would have cost Claude roughly **230k** (about 5 steps each at today's step cost), **8%** of what it spent. Delegating only saves allowance when preparing a task costs Claude less than that.
