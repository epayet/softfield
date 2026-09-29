from pathlib import Path

from runner.config import read_protected
from runner.gates import touching_protected

REPO = Path(__file__).resolve().parents[2]


def test_security_tests_and_the_leads_docs_are_protected():
    """ADR 07 items 4 and 14: juniors may change tests, but not the ones guarding protected
    code, and not the lead's instructions or their own notes."""
    guarded = [
        "tests/integration/test_scoping_isolation.py",
        "tests/integration/test_revocation.py",
        "tests/unit/test_deviceauth.py",
        "tests/browser/test_outbox.py",
        "tests/e2e/test_display.py",
        "docs/agents/lead.md",
        "docs/agents/junior.md",
        "AGENTS.md",
    ]
    assert touching_protected(guarded, read_protected(REPO)) == sorted(guarded)


def test_ordinary_tests_are_not_protected():
    free = ["tests/browser/test_render.py", "tests/integration/test_display_css.py"]
    assert touching_protected(free, read_protected(REPO)) == []
