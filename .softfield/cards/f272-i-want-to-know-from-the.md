# Milestone F272: The top bar says how long the job has run and which attempt it is

> **State:** done · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-24. Base: git tag `f272-i-want-to-know-from-the-start`. Report: [`.softfield/reviews/f272-i-want-to-know-from-the.md`](../reviews/f272-i-want-to-know-from-the.md).
> Planted by the owner on 2026-11-19.

## Notes
I want to know from the headbar how long the job has been running and which attempt it is. if there is not much space, could be a hover mouse on desktop and part of the existing tooltip tap on mobile

## Today (read in the code, 2026-11-19)
- The top bar (`factory_dashboard/templates/_partials/bar_status.html`) names the job ("Running: travel-companion · m8-04b-place-note-chip") and nothing more. `Status` in `factory_dashboard/app.py` carries no time and no attempt.
- The Overview's "Now" panel (`_partials/running.html`) already shows both: an "attempt N" pill and "Elapsed", from `overview.running_jobs` (`Running.attempt`, `Running.elapsed`).
- That pill says "attempt 2" on a planner too (job 2471 tonight): outside a ticket's job, `jobs.attempt` counts that role's jobs (`next_number`), not tries.
- A developer ticket gets `max_attempts` tries (3 here, `.softfield/project.toml`); the last can be the lead's direction (`last-attempt`). A lead ticket has no such cap.

## Expected outcome
From the top bar, on any page, you see how long the job at work has been running and, on a ticket, which attempt it is: on a wide screen at a glance, on a narrower one by hovering the words, on a phone in the tapped words.

Picture: `.softfield/cards/f272-mockup/job-clock.html` (Today against Proposed, with travel-companion's job 2463 of this morning).

**Done when:** f272-01 is merged. To test, while a developer ticket runs: on a desktop wider than 1200 px, a "Job" plate after the words says e.g. "14 min · attempt 2 of 3" and counts on without a reload; narrow the window under 1200 px: the plate goes, and hovering the words shows "Job running 14 min · attempt 2 of 3" under the sentence; on the phone, tap the dot: the same line sits above "Computer on …". While the lead answers you here, the plate shows the time alone, and the Overview's "Now" panel no longer says "attempt" on a planner.

## Decisions
- **D1 What the bar carries.** `Status` (`factory_dashboard/app.py`) gains `job_for: str | None` and `attempt: str | None`, set whenever the words name a live job: "Running: …" with a job, and "Paused … · the lead is answering you". `job_for` is `machine.on_for(job's start, now)`, the "On" plate's words ("14 min", "1 h 5 min"). `factory_wide_status` keeps them as it picks a project. Between jobs, waiting for Claude, idle or stopped: both None.
- **D2 Attempt only where it means a try.** One function, `attempt_words(job, max_attempts)` in `factory_dashboard/overview.py`: role `developer` → "attempt N of M"; `last-attempt` → "attempt N of M, the last"; `lead-ticket` → "attempt N"; any other role (planner, review, checkpoint, direction, setup…) → None. M is the job's project's `max_attempts`, read as `factory_dashboard/line.py` reads a project's config (`load_config` on its repo); when it can't be read, "attempt N". The "Now" panel's pill uses the same words and shows no pill when they are None.
- **D3 Wide screen: a "Job" plate.** In `bar_status.html`, right after the words: a `.job` plate drawn as the `.uptime` one (key with a clock, then the value), `--control-h` high (F256's token), only when `job_for` is set. It shows from 1200 px wide; below, it hides.
- **D4 Hover and tap.** The words' and the dot's `title` become the sentence, a line break, then "Job running {job_for} · {attempt}" (the attempt left out when None). On a phone the tapped words gain a `.jobline` span with that line, above F251's `.on` line, shown only under 640 px as `.on` is.
- **D5 After F256.** f272-01 waits for f256-01 (F256, The top bar on one line), which sets the bar's heights and squeezes the words; the plate joins that row.

## Before and after
- `/`
- `/planning`

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | job-clock-in-the-bar | D | 3 | f256-01 | D1 to D5 |
