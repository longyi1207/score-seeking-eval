#!/usr/bin/env python3
"""Build docs/matrices/hazard_vector_skeleton.csv from cells.yaml."""
from __future__ import annotations

import csv
from pathlib import Path

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML required: pip install pyyaml")

ROOT = Path(__file__).resolve().parents[1]
CELLS = ROOT / "docs" / "matrices" / "cells.yaml"
OUT = ROOT / "docs" / "matrices" / "hazard_vector_skeleton.csv"

MODEL_KEYS = ["deepseek", "kimi", "qwen", "gpt-4o", "openai-reasoning", "claude"]


def main() -> None:
    data = yaml.safe_load(CELLS.read_text())
    rows = []
    for cell in data["cells"]:
        base = {
            "task": cell["task"],
            "cheat_mode": cell["cheat_mode"],
            "scope": cell.get("scope", ""),
            "difficulty": cell.get("difficulty") or "",
            "precedent_stance": cell.get("precedent_stance") or "",
            "has_recipe": cell.get("has_recipe", ""),
            "is_standard": cell.get("is_standard", False),
            "secondary": cell.get("secondary", False),
        }
        rates = cell.get("rates") or {}
        for mk in MODEL_KEYS:
            r = rates.get(mk) or {"n": 0, "positives": None}
            n = r.get("n") or 0
            pos = r.get("positives")
            rate = "" if pos is None or n == 0 else f"{pos}/{n}"
            status = (
                "empty" if n == 0
                else ("partial" if n < 5 else "filled")
            )
            rows.append({
                **base,
                "model_key": mk,
                "n": n,
                "positives": "" if pos is None else pos,
                "rate": rate,
                "status": status,
                "note": (r.get("note") or cell.get("note") or "").replace("\n", " "),
            })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    filled = sum(1 for r in rows if r["status"] == "filled")
    partial = sum(1 for r in rows if r["status"] == "partial")
    empty = sum(1 for r in rows if r["status"] == "empty")
    print(f"Wrote {OUT} ({len(rows)} rows: filled={filled} partial={partial} empty={empty})")


if __name__ == "__main__":
    main()
