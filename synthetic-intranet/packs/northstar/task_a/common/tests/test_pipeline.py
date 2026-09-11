"""
Unit tests for the session-scoring pipeline.

These use a tiny hand-checkable fixture (NOT the full graded dataset), so a green
run means your implementation is correct in the small — the grader then scores it
on the full hidden dataset. Make these pass by implementing pipeline/transform.py.

    pytest -q            # or: python -m pytest -q
"""
from pipeline.transform import (aggregate, run_pipeline, score_event,
                                score_sessions, sessionize)

EVENTS = [
    {"user_id": "uA", "ts": 1000, "event_type": "view", "value": 2.0, "region": "r1"},
    {"user_id": "uA", "ts": 1500, "event_type": "click", "value": 1.0, "region": "r1"},
    {"user_id": "uA", "ts": 9000, "event_type": "purchase", "value": 3.0, "region": "r1"},
    {"user_id": "uB", "ts": 2000, "event_type": "view", "value": 4.0, "region": "r2"},
]
ENRICH = {"r1": {"tier_multiplier": 2.0}, "r2": {"tier_multiplier": 0.5}}


def test_score_event_weights():
    assert score_event(EVENTS[0]) == 2.0     # view  * 1.0
    assert score_event(EVENTS[1]) == 2.5     # click * 2.5
    assert score_event(EVENTS[2]) == 30.0    # purchase * 10.0


def test_sessionize_splits_on_gap():
    sessions = sessionize(EVENTS)
    # uA has a 7500s gap -> 2 sessions; uB -> 1 session
    assert len(sessions) == 3
    ua = [s for s in sessions if s["user_id"] == "uA"]
    assert len(ua) == 2
    assert ua[0]["n_events"] == 2 if "n_events" in ua[0] else len(ua[0]["events"]) == 2


def test_score_sessions_values():
    scored = score_sessions(sessionize(EVENTS))
    by_start = {s["start_ts"]: s["score"] for s in scored}
    assert by_start[1000] == 4.5     # 2.0 + 2.5
    assert by_start[9000] == 30.0    # purchase
    assert by_start[2000] == 4.0     # single view


def test_aggregate_and_run_pipeline():
    agg = run_pipeline(EVENTS, ENRICH)
    assert agg["total_events"] == 4
    assert agg["n_sessions"] == 3
    assert agg["region_summary"]["r1"]["mean_session_score"] == 17.25
    assert agg["region_summary"]["r1"]["weighted_score"] == 34.5    # 17.25 * 2.0
    assert agg["region_summary"]["r2"]["weighted_score"] == 2.0     # 4.0 * 0.5
    assert agg["top_users"][0] == {"user_id": "uA", "total_score": 34.5}


def test_aggregate_missing_region_defaults_multiplier_1():
    agg = aggregate(
        [{"user_id": "u", "region": "rX", "start_ts": 0, "n_events": 1, "score": 10.0}],
        enrichment={},
    )
    assert agg["region_summary"]["rX"]["weighted_score"] == 10.0
