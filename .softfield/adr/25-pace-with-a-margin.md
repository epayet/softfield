# ADR 25: Claude's week is paced with a day's margin

See ADR 44: the runner applied this to lead tickets only from then, and its evidence came from a dry run that disagreed with the runner.

- **Status:** Accepted (by the owner, 2026-10-06)
- **Date:** 2026-10-06
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 15](15-allowance-aware-routing.md) item A1, the "Spread" rule for fixed windows.
- **Evidence:** `runner run --dry-run`, 2026-10-06 22:50: Claude's week was 18% used, its pace line 12.6%, so five lead tickets waited (f5-07, f5-12, f5-13, f5-18, f9-01), and with them the whole board (f5-15 → 17). 26 hours into the week, not one day of the 30% reserve had been touched.

## Context
- ADR 15 spreads a fixed window evenly: a job may start only if `used + c ≤ (capacity − reserve) × elapsed / length`.
- A busy first day spends ahead of an even spread, and is then held until the clock catches up, even with 70% of the week unspent. Tonight that held F5's replan for about 15 hours, and the board behind it.
- The pacing still matters: on 5 Oct the week reached 0% a day before its reset, and nothing Claude-run could happen until Monday 17:00.

## Decisions (draft; ⚑ = deviates from an earlier decision)
1. **⚑ The pace line runs one day ahead:** a job may start if `used + c ≤ (capacity − reserve) × min(1, elapsed / length + margin)`, with `margin` one day of the window (1/7 of a week ≈ 10% of the spendable share). A busy day goes through; the week as a whole can't be front-loaded.
2. **The margin is a rule, not a setting:** `MARGIN = 1/7` of the window's length in `runner/allowance.py`, beside `SWEEP`. Copilot's month and Ollama's plan get the same rule (about 4 days of a month).
3. **Unchanged:** the reserve (30% of the week for the lead's support roles), the sweep in a window's last 10%, the 5-hour window's cap and its 25% for the owner, and the reserve switches (ADR 22).

## Consequences
- Tonight's 18% passes (line 12.6% + 10% = 22.6%), so the lead tickets run again.
- The most Claude can be ahead of an even spread is one day's work; on the last day the line meets the share as before.

## Settled with the owner (2026-10-06)
- "Ahead by a margin" over pure "until the reserve" and over the strict pace.
