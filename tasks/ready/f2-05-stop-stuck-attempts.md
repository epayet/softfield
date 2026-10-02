---
id: f2-05-stop-stuck-attempts
milestone: f2
depends_on: []
agent: lead
difficulty: 5
files:
  - runner/local_model.py
  - runner/procs.py
  - runner/loop.py
tests:
  - tests/runner/test_local_model.py
  - tests/runner/test_procs.py
  - tests/runner/test_loop.py
---

### Goal
A developer attempt stuck in a thinking loop, or that hasn't edited anything after 10 minutes, is stopped early and counted as failed, instead of holding the GPU for 25–45 minutes.

### Context
Read `docs/reviews/factory-f1.md` ("The local developer, in detail") and `runner/local_model.py` (`run_opencode`, `stream_facts`, `parse_events`), `runner/procs.py` (`run_streaming`, `LIVE_EVERY`) and how `runner/loop.py` handles a timed-out attempt. Test-first.
- **F1's evidence:** 6 of 24 failed local attempts made no edit in 25–30 minutes. `var/runs/20260930-194445/f1-13-milestone-page/thinking-1.md` is 205 KB ending in "Building out the template structure... Building the template structure..." repeated for thousands of lines; f1-15's first attempt ended "OK, I'm going to write the code now. Let me create the files." with no edit.
- **The rules,** checked at each `LIVE_EVERY` tick on the streamed log: no file edit 10 minutes after the start; or the last ~4,000 characters of reasoning made of one short phrase repeated. Either one stops the attempt like a timeout and records the job with `note` "stopped: no edit after 10 min" or "stopped: repeating itself".
- The next attempt follows the usual retry rules (the gate output is the stop reason). Applies to every OpenCode agent, local and Ollama.

### Done when
- a fake stream with no edit for 10 minutes is stopped and its job noted
- a fake stream whose reasoning repeats one phrase is stopped within one tick
- a stream that edits at minute 9 runs on
- `uv run runner check-all --task f2-05-stop-stuck-attempts` passes
