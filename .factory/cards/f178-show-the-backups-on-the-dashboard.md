# Milestone F178: Backups on the dashboard: copies, size, last copy, and a desk item on failure

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-27.

## Notes
Show the backups on the dashboard: how many copies, their total size, when the last one was taken, and a desk item when a copy fails.

## Plan (lead, 2026-10-29)
- **Where it stands:** `runner/backup.py` copies the metrics database into `~/Dropbox/software-factory-backups` once a day and keeps the last 14 (`[backup]` in `~/.config/softfield/factory.toml`). On 29 Oct the folder holds 14 copies, 9 Oct to 28 Oct 23:05. A failed copy is a console line and one report note (`check_backup` in `runner/loop.py`); nothing on the dashboard shows the copies. This card came from the answer on F131, how many backups the Dropbox folder keeps.
- **Mock-up:** `.factory/cards/f178-mockup/backups.html` (Today / Proposed, three states: all well, failing for an hour, runner was off).
- Tickets: `f178-01-backup-facts` (lead, runner: the listing, the machine's settings, the desk item), `f178-02-backups-panel` (developer, the bay on /projects), `f178-03-backup-on-the-desk` (developer, the desk's group).

## Decisions
- **D1: the bay is on /projects, under Projects.** The copies are the machine's, not a project's, and /projects is the page above every project. Its id is `backups`, so a link can open `/projects#backups`.
- **D2: what the dashboard reads.** `runner.config.machine_backup()` gives the machine file's `[backup]` (`Backup`, its defaults when there is none; `ConfigError` on a bad table, which the bay shows as its text). `runner.backup.listing(folder)` gives the copies oldest first as `Copy(path, taken, size)` (`taken` from `taken_at`, `size` in bytes); a missing folder is an empty list, and a file pruned between the listing and its `stat` is skipped. The dashboard lists the folder itself on each page load: 14 `stat`s, no new table.
- **D3: the bay shows** the count against `keep`, the total size and the mean, the last copy's time and how long ago, when the next is due (`taken + every_hours`), a crate per copy oldest first with dashed slots up to `keep`, and the folder with its settings. Late (the newest older than `every_hours` + 1 h, and no open `backup` item) is a calm line, not a failure: only a running runner takes a copy.
- **D4: a desk item after an hour of failures, not at the first.** A copy that fails is retried every 5 minutes (`RETRY_AFTER`); a passing failure (Dropbox holding a file) stays a console line. When copies have failed for an hour without one working, the runner opens an owner item of kind `backup` (`runner.backup.ITEM_KIND`), subject `metrics`, on the project it is running, with the error in its text, and sends one notification to the phone. The next copy that works resolves every open `backup` item in every project.
- **D5: the desk's group** "Backup failing" comes first on the Planning desk, in `--fail`, its item linking to `/projects#backups`; the Overview's Needs you lists it already, as any owner item. No button: it clears itself.
