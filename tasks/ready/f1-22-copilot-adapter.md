---
id: f1-22-copilot-adapter
milestone: f1
depends_on: [f1-20-agents-config]
agent: lead
difficulty: 6
files:
  - runner/copilot.py
  - runner/agents.py
  - workflow/runner.toml
tests:
  - tests/runner/test_copilot.py
---

### Goal
`runner/copilot.py` runs a job spec through the Copilot CLI, for read-only review jobs.

### Context
Read `docs/adr/14-developers-and-agents.md` items 2–4 and 10, its probe results ("Copilot CLI" and "Billing"), `docs/adr/15-allowance-aware-routing.md` items 2, 3 and 12, and `runner/agents.py`. Test-first, with the probe's fixture `tests/runner/fixtures/probes/copilot-review.txt`; tests fake the subprocess, never call Copilot or GitHub.
- Build on `runner/copilot.py` (it exists: `review_command` already denies shell, write, URLs and the GitHub MCP server, and binds the prompt to its flag). The spec becomes that command with the agent's model; **the denials stay, whatever the spec says**, and the tests in `tests/runner/test_copilot.py` keep passing.
- **Flags (probed):** `--no-custom-instructions` (without it Copilot loads AGENTS.md), `--no-ask-user` and `--no-auto-update` exist, as do `--output-format json` (JSONL) and `--usage-output-file <file>`; neither output's shape was saved, so the fixture is the `--silent` text.
- **Models:** which models Free offers is unknown. `--model auto` (the default) lets Copilot pick and doesn't say which. An unavailable or unknown name fails at once with `Error: Model "<name>" from --model flag is not available.` (exit 1): a config failure, not a refusal. The agent is `copilot-auto` (D6).
- **Usage:** Free is metered in fractional credits, 200 a month (the probe's review used at most 0.3), not 50 requests. The result counts the job's requests (ADR 15 item 3). `uv run runner github-get /copilot_internal/user` answers on Free with `quota_snapshots.chat` (`entitlement`, `quota_remaining`, `percent_remaining`) and `quota_reset_date`; it is undocumented and may lag. After each job, read it and return it in the result as a reading, in the form f1-44 gives Claude's (window `month`, `value` = 1 − `percent_remaining`/100, `resets_at` from `quota_reset_date`), so the caller writes it to `usage_events` as it does Claude's; when it doesn't answer, there is no reading. The billing endpoints (`/users/<user>/settings/billing/...`) answered 404 (they need the `user` scope the owner hasn't granted): don't read them.
- **Refusals:** no quota refusal has been seen; classify errors into ADR 15 item 12's classes, with an unrecognised error as a possible limit (no reset).
- Declare `copilot-auto` in `workflow/runner.toml`, in no role yet (f1-26 adds the shadow).

### Done when
- a read-only spec gives the command line with shell and write denied; a spec asking for edits is refused before running
- the fixture's output parses into the result's text and one request
- a faked `/copilot_internal/user` answer with `percent_remaining` 99.8 gives a reading of 0.002 for window `month`, reset 2026-11-01; a failed one gives none
- the "not available" model error is a failure; an unrecognised error is a limit with no reset
- `uv run runner check-all --task f1-22-copilot-adapter` passes
