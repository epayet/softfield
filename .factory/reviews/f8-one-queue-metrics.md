# Milestone F8-ONE-QUEUE: runner metrics

- Tasks merged: 13; escalated at least once: 1 (escalation rate 8%)
- Attempts per task: [1, 1, 1, 1, 1, 3, 3, 1, 1, 1, 1, 1, 3] (average 1.5)
- Review rounds: 1; actionable findings per round: [1]
- Headless Claude runs: 14
- Loop stopped because: a finding came back a third time

**Who did the work in F8-ONE-QUEUE.** The local model built 13 task(s) (work-queue-table, dispatch, support-jobs-queued, reserve-switches, replan, switch-buttons, queue-view, claude-rechecks-stand-in, stand-in-fix-tickets, reserve-request-kind, fix-the-queue-can-claim, fix-queue-view-tests-do, fix-queue-running-row-test) using 15.8M tokens, free on your GPU. Claude spent **≈70.7M token-equivalents** over 3979 steps (≈18k a step; 63% of it re-reading the conversation). That includes preparing, reviewing and fixing the local model's work. Doing those 13 tasks directly would have cost Claude roughly **1.2M** (about 5 steps each at today's step cost), **2%** of what it spent. Delegating only saves allowance when preparing a task costs Claude less than that.
