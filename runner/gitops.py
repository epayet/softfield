"""Thin git wrapper. Everything the runner does to the repo goes through here."""

import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


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

    def commit_all(self, message: str) -> bool:
        """Stage everything and commit. Returns False if there was nothing to commit."""
        self.run("add", "-A")
        if self.run("diff", "--cached", "--name-only").strip() == "":
            return False
        self.run("commit", "-q", "-m", message)
        return True

    def changed_files(self, base: str) -> list[str]:
        out = self.run("diff", "--name-only", f"{base}...HEAD")
        return [line for line in out.splitlines() if line]

    def diff_size(self, base: str) -> int:
        total = 0
        for line in self.run("diff", "--numstat", f"{base}...HEAD").splitlines():
            added, removed, _ = line.split("\t", 2)
            total += (int(added) if added != "-" else 0) + (int(removed) if removed != "-" else 0)
        return total

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

    def squash_merge(self, branch: str, into: str, message: str) -> None:
        self.checkout(into)
        self.run("merge", "-q", "--squash", branch)
        self.run("commit", "-q", "-m", message)

    def move(self, src: Path, dst: Path) -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        self.run("mv", str(src.relative_to(self.repo)), str(dst.relative_to(self.repo)))
