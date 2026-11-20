# Milestone F276: The top bar's dot and words see the lead's setup jobs

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-19.

## Notes
i don't think the dot at the top knows about setup jobs

## What the code does (2026-11-19)
- `factory_status` in `factory_dashboard/app.py`: while the owner's pause holds, only a live `planner` job lights the lead's dot, yet the runner runs `setup` jobs during the pause too. So the bar says "Paused by you since …" with no dot while the lead sets up a project.
- Not paused, a running setup job does light the lead's dot, but its words are the raw role ("setup, job N"), as a planner's are today ("Running: softfield · planner, job 2502").
- A setup job that is only queued (duck-ascii-test's, queued at 16:04, still waiting behind two planner jobs at 16:08) is not on the bar: the bar says what runs, and the project's plate says "Asked". That is right as it is.

## Decisions
- D1: the bar's paused case counts a live `setup` job like a planner's: the lead's dot, words "· the lead is setting up X". The planner's words win when both run.
- D2: among paused projects, the one with a lit dot is the one shown.
- D3: lead jobs without a ticket are named in words: "the lead is setting up X", "the lead is answering you".

## Tickets
- f276-01-the-bar-sees-setup-jobs (developer)
