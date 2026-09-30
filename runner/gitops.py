"""Thin git wrapper. Everything the runner does to the repo goes through here."""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

# Who made a commit (ADR 00 A4). Every automated commit carries an ``Agent:`` trailer;
# the local model's and the runner's also get their own author, so `git log` shows them.
LOCAL_MODEL_AGENT = "local-model"
LOCAL_MODEL_AUTHOR = "Coucou local model <local-model@coucou.invalid>"
RUNNER_AUTHOR = "Coucou runner <runner@coucou.invalid>"

_TRAILER_RE = re.compile(r"^([A-Za-z][A-Za-z-]*): (.+)$")
_LEGACY_ATTEMPTS_RE = re.compile(r"in (\d+) attempt")


class GitError(RuntimeError):
    pass


@dataclass(frozen=True)
class AgentCommit:
    sha: str
    author: str
    task: str
    attempts: str
    size: int


def with_trailers(message: str, **trailers: str) -> str:
    """Append git trailers (``Agent: runner``) after a blank line."""
    lines = [f"{key.replace('_', '-').capitalize()}: {value}" for key, value in trailers.items()]
    return message.rstrip() + "\n\n" + "\n".join(lines)


def parse_trailers(body: str) -> dict[str, str]:
    """Trailers from a commit message's last paragraph."""
    last = body.strip().split("\n\n")[-1]
    found = {}
    for line in last.splitlines():
        match = _TRAILER_RE.match(line.strip())
        if match:
            found[match[1]] = match[2]
    return found


def _legacy_attempts(body: str) -> str:
    match = _LEGACY_ATTEMPTS_RE.search(body)
    return match[1] if match else "?"


def _author(author: str | None) -> tuple[str, ...]:
    return ("--author", author) if author else ()


class Git:
    def __init__(self, repo: Path) -> None:
        self.repo = repo

    def run(self, *args: str, check: bool = True) -> str:
        proc = subprocess.run(
            ["git", *args], cwd=self.repo, capture_output=True, text=True, check=False
        )
        if check and proc.returncode != 0:
            raise GitError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
        return proc.stdout

    def current_branch(self) -> str:
        return self.run("rev-parse", "--abbrev-ref", "HEAD").strip()

    def head(self) -> str:
        return self.run("rev-parse", "HEAD").strip()

    def is_clean(self) -> bool:
        return self.run("status", "--porcelain").strip() == ""

    def fresh_branch(self, name: str, base: str) -> None:
        """Create or reset ``name`` to ``base`` and check it out, dropping untracked files."""
        self.run("checkout", "-q", "-B", name, base)
        self.run("clean", "-q", "-fd")

    def checkout(self, name: str) -> None:
        self.run("checkout", "-q", name)

    def commit_all(self, message: str, author: str | None = None) -> bool:
        """Stage everything and commit. Returns False if there was nothing to commit.

        The runner's commits skip the pre-commit hook (ADR 12 item 15): a wip commit holds a
        junior's unchecked work, and everything else the runner commits is gated its own way.
        """
        self.run("add", "-A")
        if self.run("diff", "--cached", "--name-only").strip() == "":
            return False
        self.run("commit", "-q", "--no-verify", "-m", message, *_author(author))
        return True

    def staged_files(self) -> list[str]:
        return [line for line in self.run("diff", "--cached", "--name-only").splitlines() if line]

    def changed_files(self, base: str) -> list[str]:
        """Every path changed since ``base``; a rename lists both its old and new path."""
        out = self.run("diff", "--name-only", "--no-renames", f"{base}...HEAD")
        return [line for line in out.splitlines() if line]

    def diff_size(self, base: str) -> int:
        total = 0
        for line in self.run("diff", "--numstat", f"{base}...HEAD").splitlines():
            added, removed, _ = line.split("\t", 2)
            total += (int(added) if added != "-" else 0) + (int(removed) if removed != "-" else 0)
        return total

    def numstat(self, base: str) -> list[tuple[str, int | None, int | None]]:
        """(path, added, removed) per file changed since ``base``; None counts for binaries."""
        changes: list[tuple[str, int | None, int | None]] = []
        for line in self.run("diff", "--numstat", f"{base}...HEAD").splitlines():
            added, removed, path = line.split("\t", 2)
            changes.append(
                (
                    path,
                    None if added == "-" else int(added),
                    None if removed == "-" else int(removed),
                )
            )
        return changes

    def diff(self, base: str) -> str:
        return self.run("diff", f"{base}...HEAD")

    def exists_at(self, ref: str, path: str) -> bool:
        proc = subprocess.run(
            ["git", "cat-file", "-e", f"{ref}:{path}"],
            cwd=self.repo,
            capture_output=True,
            check=False,
        )
        return proc.returncode == 0

    def squash_merge(self, branch: str, into: str, message: str, author: str | None = None) -> str:
        """Squash ``branch`` into ``into`` as one commit and return its sha."""
        self.checkout(into)
        self.run("merge", "-q", "--squash", branch)
        self.run("commit", "-q", "--no-verify", "-m", message, *_author(author))
        return self.head()

    def local_model_commits(self, base: str) -> list["AgentCommit"]:
        """Commits the local model made since ``base``, oldest first (ADR 00 A4).

        Before A4, merges carried no trailer; their body said "Implemented by the local model".
        """
        out = self.run(
            "log",
            "--reverse",
            "--format=%H%x1f%an%x1f%B%x1e",
            f"{base}..HEAD",
        )
        commits = []
        for record in out.split("\x1e"):
            if not record.strip():
                continue
            sha, author, body = record.strip("\n").split("\x1f", 2)
            trailers = parse_trailers(body)
            legacy = "Implemented by the local model" in body
            if trailers.get("Agent") != LOCAL_MODEL_AGENT and not legacy:
                continue
            subject = body.splitlines()[0] if body else ""
            commits.append(
                AgentCommit(
                    sha=sha,
                    author=author,
                    task=trailers.get("Task") or subject.split(":", 1)[0],
                    attempts=trailers.get("Attempts", _legacy_attempts(body)),
                    size=self.commit_size(sha),
                )
            )
        return commits

    def commit_size(self, sha: str) -> int:
        """Added + removed lines of one commit."""
        total = 0
        for line in self.run("show", "--numstat", "--format=", sha).splitlines():
            added, removed, _ = line.split("\t", 2)
            total += (int(added) if added != "-" else 0) + (int(removed) if removed != "-" else 0)
        return total

    def move(self, src: Path, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        self.run("mv", str(src.relative_to(self.repo)), str(dst.relative_to(self.repo)))
