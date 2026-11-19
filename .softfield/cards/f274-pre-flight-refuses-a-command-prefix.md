# Milestone F274: Pre-flight refuses a commands: prefix that can only match itself

> **State:** idea · **Area:** factory
> Planted by the owner on 2026-11-19.

## Notes
▎ Pre-flight refuses a command prefix that can't match. m1-01 on waifu-gallery (2026-11-19) listed curl -s https://danbooru.donmai.us/ in commands:; Claude Code matches a prefix only at a word boundary, so every …/tags.json?… probe was refused and the lead ticket blocked having changed nothing ($0.33). Refuse a commands: entry whose last word is a URL (or ends in /, =, ?), saying the prefix allows only that exact address; and put one line on it in task-writing.md.
