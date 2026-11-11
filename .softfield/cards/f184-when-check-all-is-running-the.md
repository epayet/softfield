# Milestone F184: The top bar's dot goes green while the runner checks, not grey

> **State:** done · **Priority:** 100 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-11. Base: git tag `f184-when-check-all-is-running-the-start`. Report: [`.softfield/reviews/f184-when-check-all-is-running-the.md`](../reviews/f184-when-check-all-is-running-the.md).
> Planted by the owner on 2026-10-29.

## Notes
When check all is running the dot in the header is grey like nothing is happening

## Outcome
- While the runner works on its own between jobs (check-all, the gates, the warm-up, picking the next ticket), the top bar's dot is green and breathes, on every page and on a phone. Grey means only that nothing is happening (idle).
- A pause asked during that work reads "Pausing after check-all · <ticket>", not "Pausing after this job".

Mock-up: [`f184-mockup/runner-dot.html`](f184-mockup/runner-dot.html).

## Why it is grey today
`factory_status` in `factory_dashboard/app.py` picks the dot from the live job only. Check-all, the gates and the warm-up aren't jobs: the runner writes them to `runs.activity` (`doing` in `runner/loop.py`), so the status falls through to `Running: {activity}` with the default dot, `idle`, which `dashboard.css` draws grey.

## Decisions
- **D1 A `runner` dot** (developer): `Status.dot` gains `runner`, set whenever the words say the run is busy without a job (`Running: …` from the activity, and "Pausing after …" with no job). `idle` stays for Idle and the paused hold. Its colour is `--good` with the same halo and breathing as the agents' dots; no new token.
- **D2 Nothing in `runner/` changes:** the activity is already there.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | runner-dot | D | 2 | – | D1: the green dot and the pause words |
