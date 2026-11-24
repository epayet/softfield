# Milestone F287: When a parked or interrupted Claude job resumes in a new…

> **State:** idea · **Area:** factory
> Planted by the owner on 2026-11-24.

## Notes
When a parked or interrupted Claude job resumes in a new run, its resume prompt repeats where its output goes (the review's findings file, a checkpoint's or an escalation's decision file), because the run's folder has changed; the F97 review wrote its findings to the old run's folder and stopped as "output unusable".
