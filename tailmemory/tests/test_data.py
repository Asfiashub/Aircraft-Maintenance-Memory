from app.data.generator import generate_events, generate_truth


def test_generator_has_eight_tails_and_failed_fix_chains():
    events = generate_events()
    tails = {event["tail_number"] for event in events}
    assert len(tails) == 8
    failed_chain_tails = {
        event["tail_number"]
        for event in events
        if event["outcome_status"] == "failed"
    }
    assert len(failed_chain_tails) >= 5


def test_truth_discloses_synthetic_data():
    truth = generate_truth()
    assert "synthetic" in truth["disclosure"].lower()
    assert len(truth["held_out_faults"]) >= 5
