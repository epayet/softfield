# Milestone F251: Show how long the computer has been on in the top bar

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-14.

## Notes
I want to see computer uptime on the dashboard curious to see how long the computer has been on

## Expected outcome
Every page's top bar says how long the computer that runs the factory (and the dashboard) has been on since its last start: an "On 6 d 4 h" plate after the status on a wide screen, and a second line under the status words when the dot is tapped on a phone. Picture: `.softfield/cards/f251-mockup/uptime.html`.

**Done when:** the plate shows on a wide screen and the line on a phone, both refresh with the status every 5 s, and a machine whose start time can't be read shows nothing rather than an error.

## Decisions
- **D1. What "on" means:** the time since the machine's last start, sleep included, read from the operating system: on Linux `/proc/uptime`'s first number, on macOS `sysctl -n kern.boottime`'s `sec =`. No new dependency (no `psutil`). It is the machine the dashboard runs on, which is the runner's.
- **D2. Where it lives:** `factory_dashboard/machine.py` (new) owns `booted_at(now) -> datetime | None` and `on_for(booted, now) -> str` ("42 min", "5 h 12 min", "6 d 4 h"). `app.top_bar` adds them as `uptime` (`{"for": …, "since": …}` or None), so the `/live` poll's out-of-band status carries it with no new request.
- **D3. Drawn in `_partials/bar_status.html`**, inside `#factory-status`: the `.uptime` plate after the sign, and a `.on` line inside `.words`. The plate uses the plate and rule tokens only, never a status colour; on a phone (max-width 639 px) the plate hides and the line shows in the tapped words.

## Before and after
- `/`

## Tickets
- f251-01-uptime-in-the-top-bar (developer)
