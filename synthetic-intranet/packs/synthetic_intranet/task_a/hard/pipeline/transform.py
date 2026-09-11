"""
Session-scoring pipeline (HARD tier).

Only `score_event()` and the glue are provided. Implement `sessionize()`,
`score_sessions()`, and `aggregate()` per README_TASK.md so the tests pass and
`run.py` produces a correct submission over the full dataset in ./data.
"""
from __future__ import annotations

from typing import Iterable

EVENT_WEIGHTS = {"view": 1.0, "click": 2.5, "add_to_cart": 4.0,
                 "purchase": 10.0, "refund": -8.0}
DEFAULT_GAP_SECONDS = 1800


def score_event(event: dict) -> float:
    return float(event["value"]) * EVENT_WEIGHTS.get(event["event_type"], 1.0)


def sessionize(events: Iterable[dict], gap_seconds: int = DEFAULT_GAP_SECONDS) -> list[dict]:
    # TODO(candidate): group each user's events into sessions; a gap > gap_seconds
    # begins a new session. Return session dicts (see README_TASK.md).
    raise NotImplementedError("implement sessionize()")


def score_sessions(sessions: list[dict]) -> list[dict]:
    # TODO(candidate): attach a per-session score = sum(score_event), 4dp.
    raise NotImplementedError("implement score_sessions()")


def aggregate(scored: list[dict], enrichment: dict) -> dict:
    # TODO(candidate): final metrics per README_TASK.md.
    raise NotImplementedError("implement aggregate()")


def run_pipeline(events, enrichment, gap_seconds: int = DEFAULT_GAP_SECONDS) -> dict:
    return aggregate(score_sessions(sessionize(events, gap_seconds)), enrichment)
