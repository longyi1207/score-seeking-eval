#!/usr/bin/env python3
"""
run.py — produce submission.json for the take-home.

Loads the event log and region-enrichment table from ./data, runs the pipeline
you implement in pipeline/transform.py, and writes ./submission.json.

Usage:
    python run.py                    # uses ./data/events.jsonl + ./data/region_enrichment.json
    python run.py --data-dir data --out submission.json
"""
from __future__ import annotations

import argparse
import os

from pipeline.io import load_enrichment, load_events, write_submission
from pipeline.transform import run_pipeline


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out", default="submission.json")
    args = ap.parse_args()

    events = load_events(os.path.join(args.data_dir, "events.jsonl"))
    enrich_path = os.path.join(args.data_dir, "region_enrichment.json")
    enrichment = load_enrichment(enrich_path) if os.path.isfile(enrich_path) else {}

    submission = run_pipeline(events, enrichment)
    write_submission(args.out, submission)
    print(f"wrote {args.out}: {len(events)} events -> "
          f"{submission.get('n_sessions')} sessions")


if __name__ == "__main__":
    main()
