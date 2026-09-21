#!/usr/bin/env python3
"""Scan runs/ → docs/matrices/capable_table.yaml + optional annotate summary."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "harness"))
from capable import HAZARD_TASKS, annotate_capable, build_capable_table  # noqa: E402

RUNS = ROOT / "runs"
OUT = ROOT / "docs" / "matrices" / "capable_table.yaml"


def main() -> None:
    loaded = []
    for f in sorted(RUNS.glob("*.json")):
        if f.stat().st_size < 50:
            continue
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        # ensure task field for runs that only have propensity.task
        if "propensity" in d and d["propensity"].get("task"):
            pass
        elif "propensity" not in d:
            # infer task from filename
            name = f.name
            task = None
            for t, keys in [
                ("protocol_re", ("protocol",)),
                ("monitored_impl", ("monitored",)),
                ("oversight_subversion", ("oversight",)),
                ("cve_exploit", ("cve_",)),
                ("internal_exfil", ("exfil",)),
                ("metric_redef", ("metric",)),
            ]:
                if any(k in name for k in keys):
                    task = t
                    break
            if task:
                d.setdefault("propensity", {})["task"] = task
        loaded.append((str(f), d))

    table = build_capable_table(loaded)
    # serialize
    out: dict = {"schema_version": 1, "rule": "see platform/harness/capable.py", "by_model_task": {}}
    for (mk, task), slot in sorted(table.items()):
        out["by_model_task"].setdefault(mk, {})[task] = slot

    # coverage grid
    models = sorted({mk for mk, _ in table})
    grid_lines = ["model," + ",".join(HAZARD_TASKS)]
    for mk in models:
        row = [mk]
        for t in HAZARD_TASKS:
            slot = table.get((mk, t))
            if not slot:
                row.append("?")
            elif slot["capable"]:
                row.append(f"Y:{slot['evidence']}")
            else:
                row.append(f"N(n={slot['n_runs']})")
        grid_lines.append(",".join(row))
    out["grid_csv"] = "\n".join(grid_lines)

    OUT.write_text(yaml.safe_dump(out, sort_keys=False, allow_unicode=True))
    print(f"Wrote {OUT}")
    print(out["grid_csv"])

    # desperation counts among seeking positives
    desp = 0
    seek = 0
    for _, d in loaded:
        if "propensity" not in d:
            continue
        annotate_capable(d, table)
        if d["propensity"].get("seek_positive"):
            seek += 1
            if d["propensity"].get("desperation"):
                desp += 1
    print(f"seek_positive runs={seek} desperation_among_them={desp}")


if __name__ == "__main__":
    main()
