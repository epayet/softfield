# Milestone F15-REPRIORITISING-TICKETS: runner metrics

- Tasks merged: 11; escalated at least once: 2 (escalation rate 18%)
- Attempts per task: [1, 1, 1, 1, 1, 3, 1, 2, 3, 1, 3] (average 1.6)
- Review rounds: 1; actionable findings per round: [2]
- Headless Claude runs: 12
- Loop stopped because: a finding came back a third time

**Who did the work in F15-REPRIORITISING-TICKETS.** The local model built 11 task(s) (reorder-request, board-shows-the-order, the-field, drag-and-send, replan, card-actions, arrows-go, card-says-what-it-waits-for, fix-populates-waits-for-cards, fix-wait-note-assertions-check, a-refused-send-keeps-the-moves) using 12.9M tokens, free on your GPU. Claude spent **≈126.0M token-equivalents** over 8799 steps (≈14k a step; 54% of it re-reading the conversation). That includes preparing, reviewing and fixing the local model's work. Doing those 11 tasks directly would have cost Claude roughly **787k** (about 5 steps each at today's step cost), **1%** of what it spent. Delegating only saves allowance when preparing a task costs Claude less than that.
