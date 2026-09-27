from runner.gitops import Git


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
