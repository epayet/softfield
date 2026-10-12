# Milestone F79: when a task times out on the first attempt, is the second…

> **State:** ready · **Priority:** 1 · **Area:** factory
> Planted by the owner on 2026-10-09.

## Notes
when a task times out on the first attempt, is the second attempt starting from scratch?

## Answer (lead, 2026-10-09)
Not for the code, yes for the conversation.
- The timed-out attempt's edits are committed to `task/<id>`, the gates run on them, and the next attempt builds on that branch, told "Your previous attempt ran out of time. Keep what works and finish the smallest remaining piece first", plus the failing gate's output (`runner/loop.py` `run_task`, `runner/prompts.py` `TIMED_OUT`, ADR 12 item 5, ADR 15 item 7).
- Only an attempt that timed out before its first edit resets the branch to main, and there was nothing to keep.
- The developer starts a new session: it doesn't see its earlier reasoning. That's on purpose: the local model's context is small and a timed-out session is already full.
- Any timeout also earns the lead's direction for the last attempt (`needs_direction`).

## Plan
- Gap: an OpenCode developer can't run `git diff`, so the retry doesn't know which files it changed. `f79-01` lists them in the retry prompt, as a requeued ticket's already does.
- Open (owner, 2026-10-10): also let OpenCode developers run `git diff`? Lead's recommendation: not yet. It reverses the prompt's "never run git" (`runner/prompts.py` `LOCAL`), widens `opencode.json`'s allowed commands (a security change, like ADR 04's `msgfmt`), and a full diff costs the local model context for little gain over reading the listed files. Revisit if retries after a timeout still lose time once `f79-01` is in.
