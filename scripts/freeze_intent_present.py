#!/usr/bin/env python3
"""Rewrite docs/matrices/intent_present_freeze.json from current heatmap cells + intent jsonl."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "matrices" / "intent_present_freeze.json"
JSONL = ROOT / "docs" / "matrices" / "cot_contemplate_codes.jsonl"


def main() -> None:
    spec = importlib.util.spec_from_file_location(
        "h", ROOT / "scripts" / "render_task_heatmap.py"
    )
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)

    by = {}
    for line in JSONL.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("file"):
            by[r["file"]] = r

    present = []
    missing = []
    for _short, tid in h.TASKS:
        for mk in h.MODEL_KEYS:
            for p in h.cell_files(tid, mk):
                present.append(p)
                if p.name not in by:
                    missing.append(p.name)

    rows = [by[p.name] for p in present if p.name in by]
    c = Counter(r.get("intent_behavior_cell") for r in rows)
    yy = c.get("intent_yes_behavior_yes", 0)
    yn = c.get("intent_yes_behavior_no", 0)
    ny = c.get("intent_no_behavior_yes", 0)
    nn = c.get("intent_no_behavior_no", 0)
    unknown = sum(1 for r in rows if not r.get("intent_behavior_cell"))
    payload = {
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "filter": "present heatmap standard cells (render_task_heatmap.cell_files)",
        "n_present_files": len(present),
        "n_judged": len(rows),
        "n_missing": len(missing),
        "yy": yy,
        "yn": yn,
        "ny": ny,
        "nn": nn,
        "unknown": unknown,
        "reasoning_available": sum(1 for r in rows if r.get("reasoning_available")),
        "declined_after_notice": sum(1 for r in rows if r.get("declined_after_notice")),
        "cell_counts": {
            "intent_no_behavior_no": nn,
            "intent_yes_behavior_yes": yy,
            "intent_yes_behavior_no": yn,
            "intent_no_behavior_yes": ny,
        },
        "missing_files": missing[:50],
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({k: payload[k] for k in (
        "n_present_files", "n_judged", "n_missing", "yy", "yn", "ny", "nn"
    )}, indent=2))
    if missing:
        print(f"missing sample: {missing[:10]}")


if __name__ == "__main__":
    main()
