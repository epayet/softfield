from runner.state import load_state, save_state


def test_round_trip(tmp_path):
    path = tmp_path / "runs" / "state.json"
    state = load_state(path)
    state.count_run(1)
    state.count_run(1)
    state.finding_seen["m1-F1"] = 2
    save_state(state, path)
    again = load_state(path)
    assert again.runs_used(1) == 2 and again.runs_used(2) == 0
    assert again.finding_seen == {"m1-F1": 2}
