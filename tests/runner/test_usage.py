import json
from datetime import UTC, datetime

from runner.usage import ClaudeUsage, claude_tokens, short, work_summary

T0 = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)


def _line(msg_id, at, **usage):
    return json.dumps(
        {"type": "assistant", "timestamp": at, "message": {"id": msg_id, "usage": usage}}
    )


def test_claude_tokens_counts_each_message_once_inside_the_window(tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.jsonl").write_text(
        "\n".join(
            [
                _line(
                    "m1",
                    "2026-09-28T12:00:05Z",
                    input_tokens=2,
                    cache_read_input_tokens=100,
                    cache_creation_input_tokens=10,
                    output_tokens=8,
                ),
                _line(
                    "m1",
                    "2026-09-28T12:00:05Z",
                    input_tokens=2,
                    cache_read_input_tokens=100,
                    cache_creation_input_tokens=10,
                    output_tokens=8,
                ),  # same message, 2nd block
                _line("m0", "2026-09-28T11:59:59Z", input_tokens=1000),  # before the window
                json.dumps({"type": "user", "message": {"content": "hi"}}),
                "not json",
            ]
        )
    )
    (tmp_path / "sub" / "b.jsonl").write_text(
        _line("m2", "2026-09-28T13:00:00+00:00", input_tokens=5, output_tokens=5)
    )
    assert claude_tokens(tmp_path, T0) == ClaudeUsage(
        input=2 + 5, cache_write=10, cache_read=100, output=8 + 5, steps=2
    )
    until = datetime(2026, 9, 28, 13, 0, tzinfo=UTC)
    assert claude_tokens(tmp_path, T0, until) == ClaudeUsage(
        input=2, cache_write=10, cache_read=100, output=8, steps=1
    )
    assert claude_tokens(tmp_path / "missing", T0) == ClaudeUsage()


def test_short():
    assert (short(1_400_000), short(420_000), short(950)) == ("1.4M", "420k", "950")


def test_work_summary():
    usage = ClaudeUsage(cache_write=200_000, cache_read=50_000_000, output=100_000, steps=200)
    # 250k + 5.0M + 500k = 5.75M; 28.8k a step; 5 steps x 2 tasks = 288k = 5%
    text = work_summary("M3", ["display-page", "snapshot"], 1_200_000, usage)
    assert "built 2 task(s) (display-page, snapshot) using 1.2M tokens" in text
    assert "Claude spent **≈5.8M token-equivalents** over 200 steps (≈29k a step; 87%" in text
    assert "roughly **288k**" in text and "**5%** of what it spent" in text
    assert "No local-model tasks yet" in work_summary("M4", [], 0, usage)
