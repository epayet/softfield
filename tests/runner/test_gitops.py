from runner.gitops import LOCAL_MODEL_AUTHOR, Git, parse_trailers, with_trailers
from tests.runner.conftest import git as run_git


def test_branch_diff_and_merge(repo):
    git = Git(repo)
    assert git.current_branch() == "main" and git.is_clean()
    git.fresh_branch("task/x", "main")
    (repo / "coucou" / "thing.py").write_text("def thing() -> int:\n    return 1\n")
    (repo / "coucou" / "new.py").write_text("A = 1\n")
    assert git.commit_all("wip")
    assert not git.commit_all("nothing")
    assert git.changed_files("main") == ["coucou/new.py", "coucou/thing.py"]
    assert git.diff_size("main") == 3  # one line replaced (1+1) + one new line
    assert git.exists_at("main", "coucou/thing.py")
    assert not git.exists_at("main", "coucou/new.py")
    git.squash_merge("task/x", "main", "task x")
    assert git.current_branch() == "main"
    assert (repo / "coucou" / "new.py").is_file()


def test_fresh_branch_resets_and_cleans(repo):
    git = Git(repo)
    git.fresh_branch("task/x", "main")
    (repo / "coucou" / "thing.py").write_text("changed\n")
    git.commit_all("wip")
    (repo / "stray.txt").write_text("untracked\n")
    git.fresh_branch("task/x", "main")
    assert "raise NotImplementedError" in (repo / "coucou" / "thing.py").read_text()
    assert not (repo / "stray.txt").exists()


def test_trailers_round_trip():
    message = with_trailers(
        "m2-01: do it\n\nBody.", agent="local-model", task="m2-01", attempts="2"
    )
    assert message.endswith("\n\nAgent: local-model\nTask: m2-01\nAttempts: 2")
    assert parse_trailers(message) == {"Agent": "local-model", "Task": "m2-01", "Attempts": "2"}
    assert parse_trailers("plain subject\n\nJust prose: not a trailer paragraph.") == {}


def test_local_model_commits_are_attributed_and_listed(repo):
    git = Git(repo)
    run_git(repo, "tag", "base")
    # A pre-A4 merge: no trailer, recognised by its body.
    (repo / "coucou" / "old.py").write_text("A = 1\n")
    git.commit_all(
        "m1-01-old: old\n\nImplemented by the local model (m) via the runner in 3 attempt(s)."
    )
    # An owner commit is never listed.
    (repo / "notes.txt").write_text("owner\n")
    git.commit_all("owner edit")
    # A post-A4 merge.
    git.fresh_branch("task/x", "main")
    (repo / "coucou" / "new.py").write_text("B = 1\nC = 2\n")
    git.commit_all("wip")
    sha = git.squash_merge(
        "task/x",
        "main",
        with_trailers("m2-01-new: new", agent="local-model", task="m2-01-new", attempts="1"),
        author=LOCAL_MODEL_AUTHOR,
    )
    assert sha == git.head()
    assert run_git(repo, "log", "-1", "--format=%an <%ae>").strip() == LOCAL_MODEL_AUTHOR
    assert run_git(repo, "log", "-1", "--format=%cn").strip() == "Test"  # committer: the owner
    found = git.local_model_commits("base")
    assert [(c.task, c.attempts, c.size) for c in found] == [
        ("m1-01-old", "3", 1),
        ("m2-01-new", "1", 2),
    ]
    assert found[1].sha == sha and found[1].author == "Coucou local model"
