import json

from runner.local_model import TokenTotals, configured_context_length, parse_events


def _step(inp: int, out: int, reasoning: int = 0) -> str:
    return json.dumps(
        {
            "type": "step_finish",
            "part": {"tokens": {"input": inp, "output": out, "reasoning": reasoning}},
        }
    )


def test_parse_events_sums_steps_and_ignores_noise():
    lines = [
        json.dumps({"type": "step_start"}),
        _step(6417, 4, 12),
        "not json",
        '{"broken',
        _step(8000, 200),
    ]
    assert parse_events(lines) == TokenTotals(input=14417, output=204, reasoning=12, steps=2)


def test_configured_context_length(tmp_path):
    (tmp_path / "opencode.json").write_text(
        json.dumps(
            {
                "provider": {
                    "lmstudio": {
                        "models": {
                            "qwen/qwen3.6-35b-a3b": {"limit": {"context": 157440, "output": 32768}}
                        }
                    }
                }
            }
        )
    )
    assert configured_context_length(tmp_path, "lmstudio/qwen/qwen3.6-35b-a3b") == 157440
    assert configured_context_length(tmp_path, "lmstudio/other") is None
