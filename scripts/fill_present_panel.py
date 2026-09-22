#!/usr/bin/env python3
"""Fill present-suite panel cells to n=5 for the 11-task heatmap.

Standard cells (propensity-facing):
  game_chess     hard / scope=none
  lean_proof     fastrev / scope=none   (hard but cheaper than isort)
  web_provision  depth=1 / scope=none
  ad-corp / ad-enterprise  — NOT here (Azure range; see runs/fill_ad_panel.sh)

Usage:
  set -a; source .env; set +a
  .venv/bin/python scripts/fill_present_panel.py --tasks chess,lean,web --workers 3
  .venv/bin/python scripts/fill_present_panel.py --tasks chess --models deepseek,gpt-4o,gpt-5.4,claude
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
LOG = RUNS / "fill_present_panel.log"
MODELS = ["deepseek", "kimi", "gpt-4o", "gpt-5.4", "claude"]


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def valid(out: Path) -> bool:
    if not out.exists() or out.stat().st_size < 200:
        return False
    try:
        d = json.loads(out.read_text())
    except Exception:
        return False
    if (d.get("verdict") or {}).get("label") == "infra_error":
        return False
    tok = d.get("tokens") or {}
    if (tok.get("in") or 0) + (tok.get("out") or 0) > 0:
        return True
    return bool(d.get("transcript") or d.get("verdict"))


def jobs(tasks: set[str], models: list[str]) -> list[tuple[str, list[str], Path]]:
    out: list[tuple[str, list[str], Path]] = []

    def add(task_dir: str, runner: str, label: str, args: list[str], model: str):
        for i in range(1, 6):
            op = RUNS / f"{label}_r{i}.json"
            # accept legacy kimi chess names without _r1
            if i == 1 and model == "kimi" and "chess" in label:
                legacy = RUNS / "kimi_chess_hard.json"
                if valid(legacy) and not op.exists():
                    continue  # count legacy as r1 via rename check below
            cmd = [PY, runner, *args, "--model-key", model, "--out", str(op)]
            out.append((f"{label}_r{i}", [str(R / "tasks" / task_dir), *cmd], op))

    for mk in models:
        if "chess" in tasks:
            # skip if already have 5 valid under either naming
            existing = list(RUNS.glob(f"chess_{mk}_hard_none_r*.json"))
            if mk == "kimi":
                existing += [p for p in RUNS.glob("kimi_chess_hard*.json") if valid(p)]
            if sum(1 for p in existing if valid(p)) >= 5:
                log(f"skip chess/{mk} — already ≥5 valid")
            else:
                add("game_chess", "run_chess.py", f"chess_{mk}_hard_none",
                    ["--difficulty", "hard", "--scope", "none"], mk)
        if "lean" in tasks:
            existing = list(RUNS.glob(f"lean_{mk}_fastrev_none_r*.json"))
            if sum(1 for p in existing if valid(p)) >= 5:
                log(f"skip lean/{mk} — already ≥5 valid")
            else:
                add("lean_proof", "run_lean.py", f"lean_{mk}_fastrev_none",
                    ["--problem", "fastrev", "--scope", "none"], mk)
        if "web" in tasks:
            existing = list(RUNS.glob(f"web_{mk}_d1_none_r*.json"))
            if mk == "kimi" and valid(RUNS / "kimi_web_none.json"):
                pass  # still need 4 more
            if sum(1 for p in existing if valid(p)) >= 5:
                log(f"skip web/{mk} — already ≥5 valid")
            else:
                add("web_provision", "run_web.py", f"web_{mk}_d1_none",
                    ["--depth", "1", "--scope", "none"], mk)
    # drop already-valid outs
    return [(n, c, o) for n, c, o in out if not valid(o)]


def run_one(name: str, cmd: list[str], out: Path) -> tuple[str, str]:
    if valid(out):
        return name, "skip"
    cwd, *argv = cmd
    log(f"START {name}")
    try:
        p = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=7200)
        tail = ((p.stdout or "") + (p.stderr or ""))[-400:]
        if valid(out):
            log(f"OK    {name}")
            return name, "ok"
        log(f"FAIL  {name} rc={p.returncode} {tail[:200]}")
        return name, f"fail:{p.returncode}"
    except subprocess.TimeoutExpired:
        log(f"TIMEOUT {name}")
        return name, "timeout"
    except Exception as e:
        log(f"ERR   {name} {e}")
        return name, f"err:{e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="chess,lean,web",
                    help="comma list: chess,lean,web")
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    tasks = {t.strip() for t in a.tasks.split(",") if t.strip()}
    models = [m.strip() for m in a.models.split(",") if m.strip()]
    RUNS.mkdir(exist_ok=True)
    # normalize kimi chess legacy → r1
    leg = RUNS / "kimi_chess_hard.json"
    dest = RUNS / "chess_kimi_hard_none_r1.json"
    if valid(leg) and not dest.exists():
        dest.write_bytes(leg.read_bytes())
        log(f"copied {leg.name} → {dest.name}")
    for i in range(2, 6):
        leg = RUNS / f"kimi_chess_hard_r{i}.json"
        dest = RUNS / f"chess_kimi_hard_none_r{i}.json"
        if valid(leg) and not dest.exists():
            dest.write_bytes(leg.read_bytes())

    todo = jobs(tasks, models)
    log(f"{len(todo)} jobs · workers={a.workers} · tasks={sorted(tasks)} · models={models}")
    if not todo:
        log("nothing to do")
        return
    ok = fail = 0
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = [ex.submit(run_one, n, c, o) for n, c, o in todo]
        for fut in as_completed(futs):
            _, st = fut.result()
            if st in ("ok", "skip"):
                ok += 1
            else:
                fail += 1
    log(f"DONE ok/skip={ok} fail={fail}")


if __name__ == "__main__":
    main()
