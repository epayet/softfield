"""Translation checks: every user-facing string has a French translation (ADR 00, A2).

Django's ``makemessages`` regenerates the catalogues into place; we back them up, run it,
inspect the result and restore, so the check never changes the working tree.
"""

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

LOCALE_DIR = Path("coucou/locale")
TARGET_LANGUAGES = ("fr",)  # every language except the source language (English)
DOMAINS = ("django", "djangojs")
IGNORE = ("tests/*", "runner/*", "var/*", "docs/*", "coucou/static/coucou/vendor/*")


@dataclass(frozen=True)
class Entry:
    msgid: str
    translated: bool
    fuzzy: bool


def _unquote(line: str) -> str:
    body = line.split(" ", 1)[1] if " " in line else '""'
    return body.strip()[1:-1].encode().decode("unicode_escape", errors="replace")


def parse_po(text: str) -> list[Entry]:
    """Entries of a .po file (the header entry excluded)."""
    entries: list[Entry] = []
    msgid: list[str] = []
    msgstrs: list[list[str]] = []
    fuzzy = False
    field: str | None = None

    def flush() -> None:
        nonlocal msgid, msgstrs, fuzzy, field
        if field is not None:
            ident = "".join(msgid)
            if ident:
                translated = bool(msgstrs) and all("".join(s) for s in msgstrs)
                entries.append(Entry(ident, translated, fuzzy))
        msgid, msgstrs, fuzzy, field = [], [], False, None

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            flush()
        elif line.startswith("#,") and "fuzzy" in line:
            if field is not None:
                flush()
            fuzzy = True
        elif line.startswith("#"):
            continue
        elif line.startswith("msgctxt"):
            if field is not None and field != "msgctxt":
                flush()
            field = "msgctxt"
        elif line.startswith("msgid_plural"):
            field = "msgid_plural"
        elif line.startswith("msgid"):
            if field not in (None, "msgctxt"):
                flush()
            field, msgid = "msgid", [_unquote(line)]
        elif line.startswith("msgstr"):
            field = "msgstr"
            msgstrs.append([_unquote(line)])
        elif line.startswith('"'):
            value = line[1:-1].encode().decode("unicode_escape", errors="replace")
            if field == "msgid":
                msgid.append(value)
            elif field == "msgstr" and msgstrs:
                msgstrs[-1].append(value)
    flush()
    return entries


def catalogue_problems(po_text: str, name: str) -> list[str]:
    problems = []
    for entry in parse_po(po_text):
        if entry.fuzzy:
            problems.append(f"{name}: fuzzy translation needs checking: {entry.msgid!r}")
        elif not entry.translated:
            problems.append(f"{name}: missing French translation: {entry.msgid!r}")
    return problems


def _po_files(repo: Path) -> list[Path]:
    return [
        repo / LOCALE_DIR / lang / "LC_MESSAGES" / f"{domain}.po"
        for lang in TARGET_LANGUAGES
        for domain in DOMAINS
    ]


def compiled_out_of_date(repo: Path) -> list[str]:
    """Each committed .po must have an up-to-date committed .mo next to it."""
    problems = []
    for po in _po_files(repo):
        if not po.is_file():
            continue
        mo = po.with_suffix(".mo")
        with tempfile.TemporaryDirectory() as tmp:
            fresh = Path(tmp) / "out.mo"
            subprocess.run(["msgfmt", "-o", str(fresh), str(po)], check=True)
            if not mo.is_file() or mo.read_bytes() != fresh.read_bytes():
                problems.append(
                    f"{mo.relative_to(repo)} is out of date: run "
                    "`uv run python manage.py compilemessages`"
                )
    return problems


def regenerated_problems(repo: Path, timeout: int) -> list[str]:
    """Run makemessages, report untranslated strings, then restore the catalogues."""
    locale = repo / LOCALE_DIR
    with tempfile.TemporaryDirectory() as tmp:
        backup = Path(tmp) / "locale"
        if locale.exists():
            shutil.copytree(locale, backup)
        try:
            locale.mkdir(parents=True, exist_ok=True)
            for domain in DOMAINS:
                cmd = ["uv", "run", "python", "manage.py", "makemessages", "-d", domain]
                cmd += [f"-l{lang}" for lang in TARGET_LANGUAGES]
                cmd += ["--no-location", "--no-obsolete"]
                cmd += [f"--ignore={pattern}" for pattern in IGNORE]
                subprocess.run(cmd, cwd=repo, capture_output=True, timeout=timeout, check=True)
            problems = []
            for po in _po_files(repo):
                if po.is_file():
                    problems += catalogue_problems(
                        po.read_text(encoding="utf-8"), po.relative_to(repo).as_posix()
                    )
            return problems
        finally:
            shutil.rmtree(locale, ignore_errors=True)
            if backup.exists():
                shutil.copytree(backup, locale)
