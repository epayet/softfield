<!-- runner report -->
## Numbers

_Written by `uv run runner report f6-planning-room` from the metrics database, which isn't in git: a snapshot. Run it again to refresh; edit outside these markers._

| Result | F6-PLANNING-ROOM |
|---|---|
| Tickets merged | 30 of 30 |
| First-attempt pass rate | 7/15 (47%) |
| Local attempts | 32 |
| Escalations, directions, checkpoints | 6, 8, 5 |
| Review rounds | 0 |
| Findings | 1 blocking, 4 should-fix, 2 nit |
| Local model | 55.9M tokens (55,488,978 in, 457,555 out) |
| Claude | $51.98 (11.9M token-equivalents) |

### Savings from delegating

What Claude would have spent writing the lines the developers merged, against what it spent supporting them: tickets, directions, escalations, and a share of the reviews and checkpoints (f1 D7). API-equivalent dollars.

| Developer | Tickets | Lines | Doing it itself | Supporting | Net |
|---|---|---|---|---|---|
| **All** | 15 | 656 | $5.50 | $15.90 | **-$10.40** |
| local-qwen3.6-35b-a3b | 15 | 656 | $5.50 | $15.90 | **-$10.40** |

Tokens underneath: doing it itself ≈1.1M token-equivalents, supporting ≈3.2M.

### By agent

| Agent | Jobs | Tokens (Claude: token-equivalents) | Dollars |
|---|---|---|---|
| claude-opus | 31 | 11.7M | $51.24 |
| claude-sonnet | 4 | 155k | $0.74 |
| copilot-auto | 1 | 0 | $0.00 |
| local-qwen3.6-35b-a3b | 32 | 55.9M | $0.00 |

### Trends

| Milestone | Merged | First-attempt | Attempts | Claude | Net savings |
|---|---|---|---|---|---|
| m1 | 5 | 4/5 (80%) | 7 | $1.51 | -$0.63 |
| m2 | 4 | 4/5 (80%) | 6 | $3.45 | -$2.63 |
| m3 | 10 | 10/11 (91%) | 13 | $4.95 | -$1.09 |
| m4 | 11 | 7/11 (64%) | 28 | $1.02 | $12.38 |
| f1 | 48 | 15/22 (68%) | 45 | $83.85 | $33.71 |
| f6-planning-room | 30 | 7/15 (47%) | 32 | $51.98 | -$10.40 |
| bugs | 0 | - | 0 | $0.00 | $0.00 |
| f2 | 12 | 1/3 (33%) | 9 | $39.43 | -$2.95 |
| f3 | 25 | 2/16 (12%) | 50 | $54.52 | -$18.83 |
| f4-always-on | 31 | 10/21 (48%) | 42 | $26.27 | -$3.99 |
| f5-board | 8 | - | 0 | $16.16 | $0.00 |
| f7-factory-fixes | 7 | - | 0 | $12.96 | $0.00 |
| f8-one-queue | 11 | 2/3 (67%) | 5 | $24.14 | $1.23 |
| f9-line-polish | 9 | 4/9 (44%) | 21 | $2.18 | $4.05 |
| f10-crates | 0 | - | 0 | $0.00 | $0.00 |
| f11-test | 0 | - | 0 | $0.50 | $0.00 |
| f12-turn-on-notifications-little-feedback-button | 0 | - | 0 | $1.86 | $0.00 |
| f13-planting-idea-ui-feedback | 0 | - | 0 | $0.52 | $0.00 |
| f14-coming-planted-ideas-not-clickable | 0 | - | 0 | $0.87 | $0.00 |
| f15-reprioritising-tickets | 0 | - | 0 | $0.00 | $0.00 |
| f16-planning-still-says-your-answer-wanted | 0 | - | 0 | $0.42 | $0.00 |
| f17-tighter-running-and-pause-presence-in | 0 | - | 0 | $0.94 | $0.00 |
| f18-arrow-to-reprioririse-queue | 0 | - | 0 | $0.00 | $0.00 |
| f19-will-i-need-to-refresh-planning | 0 | - | 0 | $0.65 | $0.00 |
| f20-data-safety | 0 | - | 0 | $0.00 | $0.00 |
| f21-lead-briefs | 0 | - | 0 | $0.00 | $0.00 |
| f22-move-archive-button-on-planning-desk | 0 | - | 0 | $1.02 | $0.00 |
| f23-when-i-click-comment-on-the | 0 | - | 0 | $1.00 | $0.00 |
| f24-bug-when-i-answer-a-ticket | 0 | - | 0 | $0.45 | $0.00 |
| f25-whenever-i-plant-something-does-it | 0 | - | 0 | $0.67 | $0.00 |
| f26-i-want-to-see-numbers-next | 0 | - | 0 | $0.53 | $0.00 |
| f27-when-i-pause-the-factory-i | 0 | - | 0 | $1.09 | $0.00 |
| f28-the-first-time-i-clicked-on | 0 | - | 0 | $0.65 | $0.00 |
| f29-the-top-was-saying-resuming-but | 0 | - | 0 | $0.62 | $0.00 |
| f30-on-conversations-i-want-to-the | 0 | - | 0 | $0.59 | $0.00 |
| f31-when-i-click-on-approve-plan | 0 | - | 0 | $0.67 | $0.00 |
| f32-the-5-hour-lead-s-window | 0 | - | 0 | $0.59 | $0.00 |
| f33-overview-now-check-all-how-long | 0 | - | 0 | $0.73 | $0.00 |
| f34-planner-tasks-cannot-be-paused-but | 0 | - | 0 | $0.39 | $0.00 |
| f35-when-i-m-reviewing-what-s | 0 | - | 0 | $0.00 | $0.00 |
| f36-whenever-the-planner-is-planning-and | 0 | - | 0 | $0.00 | $0.00 |
| f37-in-planning-mode-it-tends-to | 0 | - | 0 | $0.00 | $0.00 |
| f38-the-refresh-prompt-causes-layout-shifting | 0 | - | 0 | $0.00 | $0.00 |
| m0 | 0 | - | 0 | $0.00 | $0.00 |
| **All** | 211 | 66/121 (55%) | 258 | $337.17 | $10.85 |
<!-- /runner report -->
