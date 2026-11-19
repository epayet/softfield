# Milestone F274: Pre-flight refuses a commands: prefix that can only match itself

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-19.

## Notes
▎ Pre-flight refuses a command prefix that can't match. m1-01 on waifu-gallery (2026-11-19) listed curl -s https://danbooru.donmai.us/ in commands:; Claude Code matches a prefix only at a word boundary, so every …/tags.json?… probe was refused and the lead ticket blocked having changed nothing ($0.33). Refuse a commands: entry whose last word is a URL (or ends in /, =, ?), saying the prefix allows only that exact address; and put one line on it in task-writing.md.

## Plan

One lead ticket (`runner/` is protected): f274-01-refuse-a-prefix-that-cant-match.

## Decisions

- **D1. The rule.** In `_commands` (`runner/tasks.py`), an entry is refused when its last word (split on spaces) holds `://` or ends in `/`, `=` or `?`. The check runs before the `_COMMAND_RE` one, so an entry with a `?` gets this message, not the generic "may not include".
- **D2. The words.** The refusal names the entry and says what to write instead: `'commands' entry 'curl -s https://danbooru.donmai.us/' ends in 'https://danbooru.donmai.us/', which matches only itself: a prefix allows whole words, so 'https://danbooru.donmai.us/tags.json' would be refused. End the entry before it ('curl -s') and name the address in the ticket's Context.` It is a `TaskError`, so pre-flight, `softfield check-tickets` and `--dry-run` all show it as they show the others.
- **D3. The line goes in `runner/instructions/task-format.md`**, beside `commands:` in the frontmatter block, not in `task-writing.md`: the lead reads task-format.md when it writes `commands:`, and task-writing.md is about the developers' tickets, which can't name commands at all.
- **D4. Nothing else changes:** `git` and the owner's commands are still refused as before; entries already in ready tickets that end in a plain word (`ollama list`, `rm docs/old.md`) still pass.
- **D5. One ready ticket has the same fault.** f231-01-clear-the-seed-row (F231, Triage the set-aside bugs, and a Remove button for the ones not worth a run) names `rm .softfield/tasks/later/`, which allows only that exact word, so each of its 48 `rm .softfield/tasks/later/bug-…md` would be refused, as m1-01's probes were. If it is still in `ready/` when f274-01 runs, f274-01 changes that entry to `rm` (the files to remove are listed in its Context) so it passes the new rule and can do its work; the owner drags F274 above F231 on the board so this lands first.
