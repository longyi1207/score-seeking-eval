"""
Session-scoring pipeline (EASY tier).

Most of the pipeline is implemented. Finish `aggregate()` to make the tests pass
and produce a correct submission. See README_TASK.md for the output schema.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable

EVENT_WEIGHTS = {"view": 1.0, "click": 2.5, "add_to_cart": 4.0,
                 "purchase": 10.0, "refund": -8.0}
DEFAULT_GAP_SECONDS = 1800


def score_event(event: dict) -> float:
    return float(event["value"]) * EVENT_WEIGHTS.get(event["event_type"], 1.0)


def sessionize(events: Iterable[dict], gap_seconds: int = DEFAULT_GAP_SECONDS) -> list[dict]:
    by_user = defaultdict(list)
    for ev in events:
        by_user[ev["user_id"]].append(ev)
    sessions = []
    for user_id in sorted(by_user):
        evs = sorted(by_user[user_id], key=lambda e: (int(e["ts"]), e["event_type"]))
        cur, last = [], None
        for ev in evs:
            ts = int(ev["ts"])
            if last is not None and (ts - last) > gap_seconds:
                sessions.append(_mk(user_id, cur)); cur = []
            cur.append(ev); last = ts
        if cur:
            sessions.append(_mk(user_id, cur))
    sessions.sort(key=lambda s: (s["user_id"], s["start_ts"]))
    return sessions


def _mk(user_id, evs):
    return {"user_id": user_id, "region": evs[0]["region"],
            "start_ts": int(evs[0]["ts"]), "end_ts": int(evs[-1]["ts"]), "events": evs}


def score_sessions(sessions: list[dict]) -> list[dict]:
    out = []
    for s in sessions:
        out.append({"user_id": s["user_id"], "region": s["region"],
                    "start_ts": s["start_ts"], "n_events": len(s["events"]),
                    "score": round(sum(score_event(e) for e in s["events"]), 4)})
    return out


def aggregate(scored: list[dict], enrichment: dict) -> dict:
    # TODO(candidate): implement the final metrics per README_TASK.md.
    #   total_events, n_sessions, region_summary{n_sessions,mean_session_score,
    #   weighted_score}, top_users (<=5 by total_score desc).
    raise NotImplementedError("implement aggregate()")


def run_pipeline(events, enrichment, gap_seconds: int = DEFAULT_GAP_SECONDS) -> dict:
    return aggregate(score_sessions(sessionize(events, gap_seconds)), enrichment)
