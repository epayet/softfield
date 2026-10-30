import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def _bare_git_template(tmp_path_factory):
    """Every `git init` here copies git's template (fifteen sample hooks); a run makes
    thousands of repos, so /tmp/pytest-of-<user> held over a million such files (F175).
    An empty template leaves just the repo."""
    template = tmp_path_factory.mktemp("git-template")
    previous = os.environ.get("GIT_TEMPLATE_DIR")
    os.environ["GIT_TEMPLATE_DIR"] = str(template)
    yield
    if previous is None:
        os.environ.pop("GIT_TEMPLATE_DIR", None)
    else:
        os.environ["GIT_TEMPLATE_DIR"] = previous
