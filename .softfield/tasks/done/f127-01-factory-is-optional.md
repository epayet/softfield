---
id: f127-01-factory-is-optional
milestone: f127-shared-rules-stay-shared-across-projects
difficulty: 8
depends_on: []
agent: lead
files:
  - runner/prompts.py
tests:
  - tests/runner/test_prompts.py
---

### Goal
ADR 41: agents the factory starts get its context in their system prompt, and a project keeps only its dot folder.

---
**Done in the owner's terminal session of 2026-11-02.** Commit: "f127-factory-is-optional, and F137, F134 in Coucou and Travel Companion".
