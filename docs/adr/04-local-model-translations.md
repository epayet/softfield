# ADR 04: The local model can't compile translations

- **Status:** Accepted (by the owner, 2026-09-28): item 1 as the alternative, allow `msgfmt` in OpenCode; item 2 as proposed
- **Date:** 2026-09-28
- **Deciders:** project owner (accepts), Claude (drafts)
- **Evidence:** M2 session 2026-09-28 14:54 (`var/runs/20260928-145423/m2-01-pair-page-code/`), and `docs/sessions/2026-09-28-1454.md`

## Context

m2-01 was the first local task with French text. Its code was right, but the `translations` gate failed because `django.mo` wasn't recompiled. The model couldn't recompile it:
- `opencode.json` allows only `uv run pytest*`, `uv run ruff*` and `uv run mypy*`
- the spec said to run `msgfmt`, and the gate's message said `manage.py compilemessages`: both were denied

This cost:
- **attempt 1:** 25 minutes, 155k input tokens and 41k reasoning tokens, going round in circles after the denials
- **attempt 2:** a correct `BLOCKED.md` (`needs-file`). Its first line was a `# BLOCKED.md` heading, though, so the runner read the category as "invalid" (item 2).
- **one headless Claude escalation,** which implemented the task itself

m2-02 and m2-03 are queued and would block in the same way. The mistake is mine: I didn't check that the model's allowed commands could produce every file its task lists.

## Decisions

### 1. ⚑ The model may run `msgfmt` (owner's choice)

**Decided:** add `"msgfmt *": "allow"` to `opencode.json`. AGENTS.md rule 9 and the `translations` gate's message now name the exact `msgfmt` command, instead of `compilemessages` (which stays denied). The runner-compiles option below was not chosen.

**Originally proposed:**

**Change:**
- After each local-model attempt, and before the gates, the runner runs `msgfmt -o <mo> <po>` for every `.po` file listed in the task's `files:`, so the result joins the attempt's commit.
- Specs stop asking the model to compile, and AGENTS.md rule 9 drops "then run compilemessages".
- A `.mo` that is out of date can't happen anymore, and the `translations` gate still checks for missing and fuzzy French.

**The alternative, chosen:** add `"msgfmt *": "allow"` to `opencode.json`. That's one line, but it widens what the model may run, and it relies on the model remembering a step it already fumbled.

### 2. A `BLOCKED.md` category is read from its first `CATEGORY:` line

AGENTS.md says the first line must be exactly `CATEGORY: …`. The model put a heading line above it. The meaning was clear, and the runner should honour it rather than call it "invalid".

**Change:** `parse_blocked` accepts the first line that starts with `CATEGORY:`, within the first 5 lines. AGENTS.md's wording stays as it is.

## Also noted (no rule change)

- **The model's French** (m2-02's discarded attempt) dropped accents ("Ce code a expire", "se connecter a", "s'est mal passe"), and it was stiff ("Veuillez…"). The tests can't catch accents, so I'll check every `msgstr` at review. Specs will add one line: "Write French with all its accents (é, è, à, ç…)".
- **My runner wrapper** `timeout 3000` killed the session mid-m2-02. That's why there's no runner-written report for it. I won't wrap runner sessions in an outer timeout any more. OpenCode's own 30-minute limit now kills its whole process group (a runner bug fix, already committed).

## Consequences

- m2-02 and m2-03 can run unattended once item 1 is in place. Until then they stay in `ready/` and aren't run.
- The runner change is about 15 lines, plus tests.
