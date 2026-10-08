"""The metrics database's copies in a Dropbox folder (F20 D1): what lives only there (planning
threads, the owner's requests, ratings) survives a lost disk."""

import os
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
from pathlib import Path

from runner.config import Backup

NAME = re.compile(r"factory-metrics-(\d{8}-\d{4})\.sqlite")
STAMP = "%Y%m%d-%H%M"
# After a failed copy, the checks within this time skip it: a wait polls every few seconds
RETRY_AFTER = timedelta(minutes=5)


def copies(folder: Path) -> list[Path]:
    """The copies in ``folder``, oldest first; nothing else there counts."""
    return sorted(p for p in folder.iterdir() if NAME.fullmatch(p.name) and p.is_file())


def taken_at(path: Path) -> datetime:
    """When a copy (a name ``NAME`` matches) was taken: local time, to the minute."""
    stamp = path.name.removeprefix("factory-metrics-").removesuffix(".sqlite")
    return datetime.strptime(stamp, STAMP).astimezone()


def copy(db: Path, folder: Path, at: datetime) -> Path:
    """Copy ``db`` into ``folder`` with SQLite's online backup, safe while the run and the
    dashboard use it. The copy is written under a temporary name, out of WAL mode, then
    renamed: Dropbox only ever sees a finished file, and never the live one's -wal or -shm."""
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / f"factory-metrics-{at.astimezone():{STAMP}}.sqlite"
    part = folder / f".{target.name}.part"
    try:
        # read-only: a missing database is an error, never an empty one made here
        with (
            closing(sqlite3.connect(f"{db.as_uri()}?mode=ro", uri=True)) as source,
            closing(sqlite3.connect(part)) as dest,
        ):
            source.backup(dest)
            dest.execute("PRAGMA journal_mode = DELETE")
        os.replace(part, target)
    except BaseException:
        for leftover in (part, *(Path(f"{part}{end}") for end in ("-journal", "-wal", "-shm"))):
            leftover.unlink(missing_ok=True)
        raise
    return target


def prune(folder: Path, keep: int) -> None:
    """Past ``keep``, the oldest copies go; any other file in ``folder`` stays."""
    for path in copies(folder)[:-keep]:
        path.unlink()


class Backups:
    """When the next copy is due: the newest copy older than ``every_hours``, or none. While
    the folder is unchanged since it was last listed, a check costs one ``stat`` of it."""

    def __init__(self, db: Path, settings: Backup) -> None:
        self.db, self.settings = db, settings
        self._listed: int | None = None  # the folder's mtime when it was last listed
        self._newest: datetime | None = None
        self._retry_at: datetime | None = None

    def due(self, at: datetime) -> bool:
        folder = self.settings.dir
        try:
            mtime = folder.stat().st_mtime_ns
        except FileNotFoundError:
            return True
        if mtime != self._listed:
            found = copies(folder)
            self._listed, self._newest = mtime, taken_at(found[-1]) if found else None
        if self._newest is None:
            return True
        return at - self._newest >= timedelta(hours=self.settings.every_hours)

    def check(self, at: datetime) -> Path | None:
        """The new copy when one is due, else None. A failure raises (``OSError``,
        ``sqlite3.Error``), and the checks within ``RETRY_AFTER`` of it skip."""
        if self._retry_at is not None and at < self._retry_at:
            return None
        try:
            if not self.due(at):
                return None
            path = copy(self.db, self.settings.dir, at)
            prune(self.settings.dir, self.settings.keep)
            self._listed, self._newest = self.settings.dir.stat().st_mtime_ns, taken_at(path)
        except Exception:
            self._retry_at = at + RETRY_AFTER
            raise
        self._retry_at = None
        return path
