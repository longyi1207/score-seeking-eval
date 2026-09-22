#!/usr/bin/env python3
"""Fill Claude into remaining standard heatmap cells + chat probes.

Usage:
  .venv/bin/python runs/claude_heatmap_remaining.py --workers 4
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

R = Path(__file__).resolve().parents[1]
PY = str(R / ".venv" / "bin" / "python")
RUNS = R / "runs"
LOG = RUNS / "claude_heatmap.log"


def valid(out: Path) -> bool:
    if not out.exists() or out.stat().st_size < 200:
        return False
    try:
        d = json.loads(out.read_text())
    except Exception:
        return False
    tok = d.get("tokens") or {}
    if (tok.get("in") or 0) + (tok.get("out") or 0) > 0:
        return True
    return bool(d.get("transcript") or d.get("probes") or d.get("propensity"))


def jobs() -> list[tuple[str, list[str], Path]]:
    mk = "claude"
    out: list[tuple[str, list[str], Path]] = []

    def add(td: str, rn: str, lbl: str, args: list[str]):
        for i in range(1, 6):
            op = RUNS / f"{lbl}_r{i}.json"
            cmd = [PY, rn, *args, "--out", str(op)]
            out.append((f"{lbl}_r{i}", [td, *cmd], op))

    # Standard heatmap (protocol already done en/zh)
    add(
        "oversight_subversion",
        "run_subversion.py",
        "oversight_claude_imp_none",
        ["--model-key", mk, "--difficulty", "impossible", "--scope", "none"],
    )
    add(
        "monitored_impl",
        "run_monitored.py",
        "monitored_claude_imp_none",
        ["--model-key", mk, "--difficulty", "impossible", "--scope", "none"],
    )
    add(
        "cve_exploit",
        "run_cve.py",
        "cve_claude_neutral",
        ["--model-key", mk, "--scope", "none", "--precedent", "neutral", "--monitoring", "control"],
    )
    add(
        "internal_exfil",
        "run_exfil.py",
        "exfil_claude_none_endorsing",
        ["--model-key", mk, "--scope", "none", "--precedent", "endorsing", "--monitoring", "control"],
    )
    add(
        "metric_redef",
        "run_metric.py",
        "metric_claude_endorsing",
        ["--model-key", mk, "--scope", "none", "--precedent", "endorsing", "--framing", "neutral",
         "--monitoring", "control"],
    )
    # chat probes once
    op = RUNS / "chat_probes_claude.json"
    out.append((
        "chat_probes_claude",
        ["chat_probes", PY, "run_probes.py", "--model-key", mk, "--out", str(op)],
        op,
    ))
    return out


def run_one(label: str, packed: list[str], out: Path) -> tuple[str, str, float]:
    td, *cmd = packed
    t0 = time.time()
    if valid(out):
        return label, "SKIP", 0.0
    if out.exists():
        out.unlink()
    env = os.environ.copy()
    # load keys
    for p in (R / ".env", Path("/Users/apple/Desktop/ai_notes/.env")):
        if p.exists():
            for line in p.read_text().splitlines():
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    try:
        subprocess.run(
            cmd,
            cwd=str(R / "tasks" / td),
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=1800,
        )
        status = "OK" if valid(out) else "FAIL"
    except Exception as e:
        status = f"ERR:{type(e).__name__}"
        LOG.write_text(LOG.read_text() + f"\n{label}: {e}\n" if LOG.exists() else f"{label}: {e}\n")
    return label, status, time.time() - t0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    RUNS.mkdir(exist_ok=True)
    all_jobs = jobs()
    todo = [(l, p, o) for l, p, o in all_jobs if not valid(o)]
    print(f"CLAUDE HEATMAP: {len(todo)}/{len(all_jobs)} remaining, workers={args.workers}", flush=True)
    ok = fail = skip = 0
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run_one, l, p, o): (l, o) for l, p, o in todo}
        # also count already-valid as skip progress
        for l, p, o in all_jobs:
            if valid(o) and (l, p, o) not in [(a, b, c) for a, b, c in todo]:
                skip += 1
        for fut in as_completed(futs):
            label, status, dt = fut.result()
            done += 1
            if status == "OK":
                ok += 1
            elif status == "SKIP":
                skip += 1
            else:
                fail += 1
            print(f"[{done}/{len(todo)}] {status} {label} ({dt:.0f}s)", flush=True)
    print(f"CLAUDE HEATMAP DONE ok={ok} fail={fail} skip={skip}", flush=True)


if __name__ == "__main__":
    main()
