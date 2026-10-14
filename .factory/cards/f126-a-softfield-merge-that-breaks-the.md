# Milestone F126: A Softfield merge that breaks the runner

> **State:** idea · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-14.

## Notes
From the terminal session of 2026-10-14 that built ADR 30 (sessions B, C, D).

Softfield runs from `~/.local/share/softfield/live`, which follows Softfield's main: after a job
in Softfield ends, `update_live` moves it and the runner restarts on the new code (ADR 30 item 5;
`softfield dashboard update` does it by hand). A merge that passed the gates but crashes at
start leaves the runner stopped, and nothing says so; the fix today is moving live back by hand
(`git -C ~/.local/share/softfield/live checkout --detach <previous>`).

Proposed: remember the last commit that started cleanly; when the restart fails, say it plainly
on the dashboard (the top bar, Needs you) with one button to go back to it, and a
`softfield status` that works without a milestone (today `softfield status` needs one, e.g.
`softfield status f15`) and says which commit live is on and whether the runner is up.
