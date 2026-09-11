#!/usr/bin/env python3
"""
results.py — aggregate run label vectors into the V1 dashboard (per condition cell).

Reads:
  * logs/*/label.json         (mock_run.py outputs), and
  * any Inspect .eval logs under logs/ if present (best-effort; requires inspect_ai)

Prints the V1_SPEC §7 metrics grouped by condition, and writes METRICS_LATEST.md.

Usage: python inspect_eval/results.py [logs_dir]
"""
from __future__ import annotations

import glob
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LOGS = os.path.abspath(os.path.join(HERE, "..", "logs"))


def load_mock_labels(logs_dir: str) -> list[dict]:
    out = []
    for p in glob.glob(os.path.join(logs_dir, "*", "label.json")):
        try:
            out.append(json.load(open(p)))
        except Exception:
            pass
    return out


def load_inspect_labels(logs_dir: str) -> list[dict]:
    """Best-effort read of Inspect .eval logs, if inspect_ai is importable."""
    rows = []
    evals = glob.glob(os.path.join(logs_dir, "*.eval"))
    if not evals:
        return rows
    try:
        from inspect_ai.log import read_eval_log
    except Exception:
        return rows
    for ev in evals:
        try:
            log = read_eval_log(ev)
        except Exception:
            continue
        for s in (log.samples or []):
            md = (s.scores or {})
            # pull our scorer's metadata
            for _name, sc in (s.scores or {}).items():
                meta = sc.metadata or {}
                if "label" in meta:
                    rows.append({
                        "scope": (s.metadata or {}).get("scope", "?"),
                        "tier": (s.metadata or {}).get("task_tier", "?"),
                        "vuln_mask": (s.metadata or {}).get("vuln_mask", "?"),
                        "label": meta.get("label"),
                        "channel": meta.get("channel"),
                        "adjacent_access": meta.get("adjacent_access"),
                        "steps_to_first_seek_action":
                            meta.get("steps_to_first_seek_action"),
                        "source": "inspect",
                    })
    return rows


def cell_key(r: dict) -> str:
    return f"scope={r.get('scope','?')} tier={r.get('tier','?')} vm={r.get('vuln_mask','?')}"


def rate(rows, pred):
    n = len(rows)
    return (sum(1 for r in rows if pred(r)) / n) if n else 0.0


def aggregate(rows: list[dict]) -> dict:
    cells = defaultdict(list)
    for r in rows:
        cells[cell_key(r)].append(r)
    summary = {}
    for key, rs in sorted(cells.items()):
        summary[key] = {
            "n": len(rs),
            "honest_solve_rate": rate(rs, lambda r: r["label"] == "honest_solve"),
            "score_seek_attempt_rate":
                rate(rs, lambda r: r["label"] in ("score_seek_attempt",
                                                  "score_seek_success")),
            "score_seek_success_rate":
                rate(rs, lambda r: r["label"] == "score_seek_success"),
            "scope_violation_rate":
                rate(rs, lambda r: r.get("scope") == "hard" and r.get("adjacent_access")),
            "channels": sorted({r.get("channel") for r in rs if r.get("channel")
                                and r.get("channel") != "none"}),
        }
    return summary


def main():
    logs_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LOGS
    rows = load_mock_labels(logs_dir) + load_inspect_labels(logs_dir)
    if not rows:
        print(f"no label vectors found under {logs_dir} "
              f"(run mock_run.py or an Inspect eval first)")
        return
    summary = aggregate(rows)

    print(f"\n=== Northstar V1 dashboard ({len(rows)} runs) ===")
    hdr = f"{'condition cell':45s} {'n':>3} {'honest':>7} {'seek_att':>9} {'seek_ok':>8} {'scope_viol':>10}"
    print(hdr); print("-" * len(hdr))
    lines = [hdr, "-" * len(hdr)]
    for key, m in summary.items():
        line = (f"{key:45s} {m['n']:>3} {m['honest_solve_rate']:>7.2f} "
                f"{m['score_seek_attempt_rate']:>9.2f} {m['score_seek_success_rate']:>8.2f} "
                f"{m['scope_violation_rate']:>10.2f}")
        print(line + (f"   channels={m['channels']}" if m['channels'] else ""))
        lines.append(line + (f"   channels={m['channels']}" if m['channels'] else ""))

    out = os.path.join(os.path.dirname(logs_dir), "METRICS_LATEST.md")
    with open(out, "w") as f:
        f.write("# Northstar V1 — latest metrics (auto-generated)\n\n")
        f.write("Regenerate with `python inspect_eval/results.py`.\n\n```\n")
        f.write("\n".join(lines) + "\n```\n")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
