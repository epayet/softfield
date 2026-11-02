# Milestone F3: runner metrics

- Tasks merged: 21; escalated at least once: 8 (escalation rate 38%)
- Attempts per task: [1, 3, 3, 1, 6, 1, 6, 4, 2, 3, 1, 1, 3, 3, 3, 1, 2, 1, 3, 3, 1] (average 2.5)
- Review rounds: 1; actionable findings per round: [1]
- Headless Claude runs: 38
- Loop stopped because: adr-needed

**Who did the work in F3.** The local model built 21 task(s) (factory-line, line-phone, line-motion, clog-today, line-panels, replay-data, replay-controls, line-phone-fixes, line-phone-finish, replay-steps, phone-floor, stop-kills-agents, line-on-overview, clog-panel, fix-overview-live-refresh, line-refresh-in-place, now-first, crate-details, machines-and-belts, since-you-looked, line-look-review) using 31.1M tokens, free on your GPU. Claude spent **≈46.6M token-equivalents** over 2493 steps (≈19k a step; 58% of it re-reading the conversation). That includes preparing, reviewing and fixing the local model's work. Doing those 21 tasks directly would have cost Claude roughly **2.0M** (about 5 steps each at today's step cost), **4%** of what it spent. Delegating only saves allowance when preparing a task costs Claude less than that.
