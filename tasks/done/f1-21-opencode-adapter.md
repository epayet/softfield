---
id: f1-21-opencode-adapter
milestone: f1
depends_on: [f1-20-agents-config]
agent: lead
difficulty: 6
files:
  - runner/local_model.py
  - runner/agents.py
  - runner/loop.py
  - opencode.json
  - workflow/runner.toml
tests:
  - tests/runner/test_local_model.py
  - tests/runner/test_loop.py
---

### Goal
OpenCode is an adapter like Claude's, so a developer job can run on the local model or on an Ollama Cloud model by configuration alone.

### Context
Read `docs/adr/14-developers-and-agents.md` items 2–4 and 10, its probe results ("Ollama Cloud"), `docs/adr/15-allowance-aware-routing.md` items 2, 3, 7, 9 and 12 (they amend it), and `runner/agents.py`. Test-first, with the probe's fixture `tests/runner/fixtures/probes/opencode-ollama.jsonl`.
- `runner/local_model.py`'s `run_opencode` becomes the `opencode` harness's adapter: the agent's `model` picks the provider (LM Studio or Ollama, both in `opencode.json`); tokens, steps, peak context, streak and refused commands come back in the `JobResult`, as they do today.
- The LM Studio warm-up and loaded-context checks (`warmup`, `loaded_context_length`) apply only to the local provider.
- **Facts from the probe (f1-18):** OpenCode names the models `ollama/<tag>`, for example `ollama/gpt-oss:120b-cloud`; the six tags are in `opencode.json`'s `ollama` provider, which goes through the local Ollama daemon (no API key). The fixture's events have LM Studio's shape: `parse_events` and `stream_facts` read it unchanged (input 7795, output 92, peak 7867, reasoning 0). OpenCode's `cost` is 0, and nothing reports what a job costs of the allowance: the usage is our own token count (ADR 15 item 3).
- **Refusals:** no Ollama quota or limit error has been seen, so its shape is unknown. Classify errors into ADR 15 item 12's `limit`, `transient` or `failure`; an unrecognised error from a cloud tag counts as a possible limit (no reset), not a failed attempt, so `runner/allowance.py`'s unknown-capacity cooldown (item 2) applies. The local provider's errors stay failures.
- Declare the six Ollama tags as agents in `workflow/runner.toml` (ids as in D6 of `docs/milestones/f1.md`), each with one starting rating (ADR 15 item 9) from ADR 14's size comparison in its Context (item 7), and in no role yet.

### Done when
- a developer job on the local agent behaves as before (the loop tests pass)
- the same job on a fake Ollama agent runs `opencode run` with that model and skips the warm-up; the probe's fixture gives its tokens
- an unrecognised error from a fake Ollama agent gives a limit, not a failed attempt; the same error on the local agent is a failure
- `uv run runner check-all --task f1-21-opencode-adapter` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
