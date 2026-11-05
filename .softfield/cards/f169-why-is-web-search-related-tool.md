# Milestone F169: Let the planner search and read the web for research

> **State:** ready · **Priority:** 1 · **Area:** factory
> Planted by the owner on 2026-10-21.

## Notes
Why is web search related tool not allowed for the planner? I just asked to do some research and it couldn't

## Plan (lead, 2026-10-21)
- Why: no headless job has ever had a web tool. `allowed_tools` (`runner/claude.py`) gives reads, edit globs and command prefixes, and `dontAsk` refuses the rest. It was never decided against, just never added.
- Decisions: [ADR 33](../adr/33-the-planner-can-search-the-web.md) (Proposed). The planner gets `WebSearch` and `WebFetch`, and a job with the web reads only the repo and the live docs.
- Tickets: `f169-01-planner-searches-the-web` (lead: the security joint, probe first). It waits for ADR 33 to be accepted.
