"""I/O helpers for the pipeline (complete — you do not need to edit this)."""
from __future__ import annotations

import json


def load_events(path: str) -> list[dict]:
    """Load newline-delimited JSON events."""
    events = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def load_enrichment(path: str) -> dict:
    """Load the region-enrichment table: region -> {"tier_multiplier": float}."""
    with open(path) as f:
        return json.load(f)


def write_submission(path: str, submission: dict) -> None:
    with open(path, "w") as f:
        json.dump(submission, f, indent=2, sort_keys=True)
