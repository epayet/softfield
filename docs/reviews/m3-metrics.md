# Milestone 3: runner metrics

- Tasks merged: 8; escalated: 0 (escalation rate 0%)
- Attempts per task: [1, 1, 1, 1, 1, 1, 1, 1] (average 1.0)
- Review rounds: 3; actionable findings per round: [2, 1, 1]
- Headless Claude runs used: 4 of 10
- Loop stopped because: adr-needed

**Who did the work in M3.** The local model built 8 task(s) (display-page, display-css, build-snapshot, post-moment-command, me-name-form, bad-origin-message, render-moment, french-wording) using 738k tokens, free on your GPU. Claude spent **≈10.4M token-equivalents** over 390 steps (≈27k a step; 78% of it re-reading the conversation). That includes preparing, reviewing and fixing the local model's work. Doing those 8 tasks directly would have cost Claude roughly **1.1M** (about 5 steps each at today's step cost), **10%** of what it spent. Delegating only saves allowance when preparing a task costs Claude less than that.
