---
id: f5-03-dashboard-lan
milestone: f5-board
depends_on: []
agent: lead
difficulty: 2
files:
  - runner/cli.py
tests:
  - tests/runner/test_cli.py
---

### Goal
`uv run runner dashboard --lan` serves the dashboard on this machine's home-network address, so the owner's phone can reach it.

### Context
Read `runner/cli.py` (the `dashboard` command, `--host`) and `factory_dashboard/app.py` (`serve`, which reloads on code changes). Test-first.
- Today the owner types `--host <their LAN IP>`. `--lan` finds that address: the source address of a UDP socket "connected" to a public IP, which sends nothing. Then it serves as `--host` does, and prints the address to open on the phone.
- `--lan` and `--host` together is an error. The default stays `127.0.0.1`. Reloading on code changes stays as it is.

### Done when
- `--lan` serves on the address found (the finder faked in the test) and prints it
- `--lan --host x` exits with a clear message
- `uv run runner check-all --task f5-03-dashboard-lan` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
