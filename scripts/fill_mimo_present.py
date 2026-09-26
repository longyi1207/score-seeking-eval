#!/usr/bin/env python3
"""Fill MiMo-V2.6-Pro on the present suite (+ new CVE siblings), soft-capped at $10.

Phased order (endorsement spine first; web last; AD not included — needs Azure VMs):
  0  smoke          1× cve_exploit none
  1  cve_spine      cve_exploit / cve_rce / cve_cli_read ladder @ n=5
  2  heatmap        protocol / oversight / monitored / metric / exfil
  3  construct      chess hard / lean fastrev
  4  expensive      web d1

Usage
-----
  set -a; source .env; set +a          # picks up XIAOMI_API_KEY or MIMO_API_KEY
  .venv/bin/python scripts/fill_mimo_present.py --dry-run
  .venv/bin/python scripts/fill_mimo_present.py --budget 10

Resumable: existing valid run JSONs are skipped. Soft budget uses Pro list prices
($0.435/M in, $0.87/M out) on recorded tokens; skips jobs whose estimate would
blow the remaining budget.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

R = Path(__file__).resolve().parents[1]
PY = str(R / ".venv" / "bin" / "python")
RUNS = R / "runs"
LOG = RUNS / "fill_mimo_present.log"
STATUS = RUNS / "fill_mimo_present_status.json"
MK = "mimo"

PRO_IN = 0.435   # $/M tokens overseas
PRO_OUT = 0.87

# Historical mean (in, out) for pre-flight budget estimates
EST = {
    "cve_exploit": (5605, 409),
    "cve_rce": (5605, 409),
    "cve_cli_read": (12000, 800),
    "protocol_re": (161369, 9112),
    "oversight_subversion": (141224, 4965),
    "monitored_impl": (44994, 4552),
    "metric_redef": (20238, 1960),
    "internal_exfil": (66934, 2870),
    "game_chess": (98045, 4805),
    "lean_proof": (90000, 4300),
    "web_provision": (752669, 10479),
}

RUNNER = {
    "cve_exploit": "run_cve.py",
    "cve_rce": "run_cve_rce.py",
    "cve_cli_read": "run_cve_cli.py",
    "protocol_re": "run_protocol.py",
    "oversight_subversion": "run_subversion.py",
    "monitored_impl": "run_monitored.py",
    "metric_redef": "run_metric.py",
    "internal_exfil": "run_exfil.py",
    "game_chess": "run_chess.py",
    "lean_proof": "run_lean.py",
    "web_provision": "run_web.py",
}


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    RUNS.mkdir(exist_ok=True)
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


def cost_usd(tin: float, tout: float) -> float:
    return tin / 1e6 * PRO_IN + tout / 1e6 * PRO_OUT


def spent_from_outs(outs: list[Path]) -> tuple[float, int, int]:
    tin = tout = 0
    for p in outs:
        if not valid(p):
            continue
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        t = d.get("tokens") or {}
        tin += int(t.get("in") or 0)
        tout += int(t.get("out") or 0)
    return cost_usd(tin, tout), tin, tout


def mk_job(task: str, label: str, args: list[str], rep: int, *,
           timeout: int = 2400) -> dict:
    out = RUNS / f"{label}_r{rep}.json"
    return {
        "name": f"{label}_r{rep}",
        "task": task,
        "est_key": task,
        "cwd": str(R / "tasks" / task),
        "timeout": timeout,
        "out": out,
        "argv": [PY, RUNNER[task], *args, "--model-key", MK, "--out", str(out)],
        "done": valid(out),
    }


def build_phases(n: int) -> list[tuple[str, list[dict]]]:
    phases: list[tuple[str, list[dict]]] = []

    # 0 smoke — single replicate
    phases.append(("0_smoke", [
        mk_job("cve_exploit", f"cve_{MK}_smoke",
               ["--scope", "none", "--precedent", "none", "--monitoring", "control"], 1),
    ]))

    # 1 CVE spine
    cve: list[dict] = []
    for arm in ("none", "disclose", "endorse_no_recipe", "endorse_with_recipe",
                "ai_endorse_no_recipe"):
        for i in range(1, n + 1):
            cve.append(mk_job(
                "cve_exploit", f"cve_{MK}_{arm}",
                ["--scope", "none", "--precedent", arm, "--monitoring", "control"], i,
            ))
    for arm in ("none", "disclose", "endorse_no_recipe",
                "endorse_exec_with_recipe", "endorse_read_with_recipe"):
        for i in range(1, n + 1):
            cve.append(mk_job(
                "cve_rce", f"cverce_{MK}_{arm}",
                ["--scope", "none", "--precedent", arm, "--monitoring", "control"], i,
            ))
    for arm in ("none", "disclose", "endorse_no_recipe", "endorse_with_recipe"):
        for i in range(1, n + 1):
            cve.append(mk_job(
                "cve_cli_read", f"cvecli_{MK}_{arm}",
                ["--scope", "none", "--precedent", arm, "--monitoring", "control"], i,
                timeout=3600,
            ))
    phases.append(("1_cve_spine", cve))

    # 2 heatmap
    heat: list[dict] = []
    for i in range(1, n + 1):
        heat.append(mk_job("protocol_re", f"protocol_{MK}_none",
                           ["--scope", "none"], i))
        heat.append(mk_job("oversight_subversion", f"oversight_{MK}_impossible_none",
                           ["--difficulty", "impossible", "--scope", "none"], i))
        heat.append(mk_job("monitored_impl", f"monitored_{MK}_impossible_none",
                           ["--difficulty", "impossible", "--scope", "none"], i))
        heat.append(mk_job("metric_redef", f"metric_{MK}_endorsing",
                           ["--scope", "none", "--precedent", "endorsing",
                            "--monitoring", "control"], i))
        heat.append(mk_job("internal_exfil", f"exfil_{MK}_none",
                           ["--scope", "none", "--precedent", "none",
                            "--monitoring", "control"], i))
        heat.append(mk_job("internal_exfil", f"exfil_{MK}_endorsing",
                           ["--scope", "none", "--precedent", "endorsing",
                            "--monitoring", "control"], i))
    phases.append(("2_heatmap", heat))

    # 3 construct
    construct: list[dict] = []
    for i in range(1, n + 1):
        construct.append(mk_job("game_chess", f"chess_{MK}_hard_none",
                                ["--difficulty", "hard", "--scope", "none"], i))
        construct.append(mk_job("lean_proof", f"lean_{MK}_fastrev_none",
                                ["--problem", "fastrev", "--scope", "none"], i))
    phases.append(("3_construct", construct))

    # 4 web
    web = [mk_job("web_provision", f"web_{MK}_d1_none",
                  ["--depth", "1", "--scope", "none"], i, timeout=7200)
           for i in range(1, n + 1)]
    phases.append(("4_web", web))
    return phases


def est_job_usd(job: dict) -> float:
    tin, tout = EST.get(job["est_key"], (50000, 3000))
    return cost_usd(tin, tout)


def run_one(job: dict) -> tuple[str, str]:
    if valid(job["out"]):
        return job["name"], "skip"
    log(f"START {job['name']}")
    try:
        p = subprocess.run(
            job["argv"], cwd=job["cwd"], capture_output=True, text=True,
            timeout=job["timeout"], env={**os.environ},
        )
        if valid(job["out"]):
            usd, _, _ = spent_from_outs([job["out"]])
            try:
                v = (json.loads(job["out"].read_text()).get("verdict") or {})
                extra = f"{v.get('label')} ({v.get('channel')})"
            except Exception:
                extra = "ok"
            log(f"OK    {job['name']} -> {extra}  ~${usd:.3f}")
            return job["name"], "ok"
        tail = ((p.stdout or "") + (p.stderr or ""))[-400:].replace("\n", " | ")
        log(f"FAIL  {job['name']} rc={p.returncode} {tail[:240]}")
        return job["name"], f"fail:{p.returncode}"
    except subprocess.TimeoutExpired:
        log(f"TIMEOUT {job['name']}")
        return job["name"], "timeout"
    except Exception as e:  # noqa: BLE001
        log(f"ERR   {job['name']} {e}")
        return job["name"], f"err:{e}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--budget", type=float, default=10.0)
    ap.add_argument("--phases", default="0,1,2,3,4",
                    help="comma list of phase ids, e.g. 0,1,2")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if not (os.environ.get("MIMO_API_KEY") or os.environ.get("XIAOMI_API_KEY")):
        log("FATAL MIMO_API_KEY / XIAOMI_API_KEY unset — "
            "`set -a; source .env; set +a` or vault store MIMO_API_KEY")
        sys.exit(2)

    sys.path.insert(0, str(R / "platform" / "harness"))
    from azure_models import MODELS  # noqa: E402
    if "mimo" not in MODELS:
        log("FATAL mimo missing from azure_models.MODELS")
        sys.exit(2)
    log(f"model {MODELS['mimo']}  budget=${a.budget:.2f}  n={a.n}")

    RUNS.mkdir(exist_ok=True)
    want = {p.strip() for p in a.phases.split(",") if p.strip()}
    phases = [(name, jobs) for name, jobs in build_phases(a.n)
              if name.split("_", 1)[0] in want]

    all_jobs = [j for _, js in phases for j in js]
    spent, tin, tout = spent_from_outs([j["out"] for j in all_jobs])
    todo = [j for j in all_jobs if not j["done"]]
    log(f"already {len(all_jobs) - len(todo)} valid · spent≈${spent:.2f} "
        f"({tin/1e6:.2f}M in / {tout/1e6:.2f}M out)")
    log(f"plan: {len(todo)} to run · est remaining≈${sum(est_job_usd(j) for j in todo):.2f}")
    for name, js in phases:
        pending = [j for j in js if not j["done"]]
        log(f"  {name}: {len(js)} · pending {len(pending)} · "
            f"est ${sum(est_job_usd(j) for j in pending):.2f}")
    log("NOTE: AD-corp/enterprise not included (Azure VMs). "
        "Wire mimo into scripts/fill_ad_panel.sh if budget remains.")

    if a.dry_run:
        return

    state: dict = {
        "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "budget": a.budget,
        "spent_usd": spent,
        "ok": [],
        "fail": [],
        "skipped_budget": [],
    }
    STATUS.write_text(json.dumps(state, indent=2))

    for phase_name, jobs in phases:
        pending = [j for j in jobs if not valid(j["out"])]
        if not pending:
            log(f"{phase_name}: nothing pending")
            continue
        spent, _, _ = spent_from_outs([j["out"] for j in all_jobs])
        log(f"=== {phase_name} ({len(pending)} jobs) · spent≈${spent:.2f} ===")

        runnable = []
        for j in pending:
            if spent + est_job_usd(j) > a.budget:
                log(f"BUDGET skip {j['name']} "
                    f"(${spent:.2f}+est ${est_job_usd(j):.2f} > ${a.budget})")
                state["skipped_budget"].append(j["name"])
            else:
                runnable.append(j)
        if not runnable:
            log(f"{phase_name}: budget exhausted — stop")
            break

        with ThreadPoolExecutor(max_workers=a.workers) as pool:
            futs = [pool.submit(run_one, j) for j in runnable]
            for fut in as_completed(futs):
                name, status = fut.result()
                if status in ("ok", "skip"):
                    state["ok"].append(name)
                else:
                    state["fail"].append(name)
                spent, tin, tout = spent_from_outs([j["out"] for j in all_jobs])
                state.update({
                    "spent_usd": round(spent, 4),
                    "tokens_in": tin,
                    "tokens_out": tout,
                    "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                })
                STATUS.write_text(json.dumps(state, indent=2))
                if spent >= a.budget:
                    log(f"BUDGET HIT ${spent:.2f} — stop scheduling")
                    break

        spent, _, _ = spent_from_outs([j["out"] for j in all_jobs])
        log(f"{phase_name} done · spent≈${spent:.2f}")
        if spent >= a.budget:
            break

    spent, tin, tout = spent_from_outs([j["out"] for j in all_jobs])
    state["spent_usd"] = round(spent, 4)
    STATUS.write_text(json.dumps(state, indent=2))
    log(f"DONE spent≈${spent:.2f} ({tin/1e6:.2f}M in / {tout/1e6:.2f}M out) "
        f"ok={len(state['ok'])} fail={len(state['fail'])} "
        f"budget_skip={len(state['skipped_budget'])} · {STATUS}")


if __name__ == "__main__":
    main()
