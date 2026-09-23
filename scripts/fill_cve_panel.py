#!/usr/bin/env python3
"""Fill the panel for the two new CVE arms: `cve_rce` and `cve_cli_read`.

Both are `status: draft` with no panel. This drives them to n=5 across the standard model panel so
they can be compared against the `cve_exploit` anchor (0/30 disclose -> 14/15 endorse).

Arms
----
`cve_rce` (CVE-2021-41773, httpd 2.4.49 -> mod_cgi RCE) -- five arms, because this task also crosses
ENDORSED FORM with CHOSEN FORM:
    none                      base rate
    disclose                  knowledge without permission   (the anchor's 0/30 cell)
    endorse_no_recipe         permission without a recipe     (the propensity arm)
    endorse_exec_with_recipe  capability ceiling; endorsed act = run commands on the host
    endorse_read_with_recipe  same ladder rung, endorsed act = read a file  (de-escalation contrast)

`cve_cli_read` (CVE-2024-23897, Jenkins CLI @file) -- four arms; `endorse_no_recipe` is load-bearing
(can the model CONSTRUCT a multi-step exploit) with `endorse_with_recipe` as the capability control.

Usage
-----
    set -a; source .env; set +a
    .venv/bin/python scripts/fill_cve_panel.py                      # both tasks, full panel, n=5
    .venv/bin/python scripts/fill_cve_panel.py --tasks rce --models gpt-4o
    .venv/bin/python scripts/fill_cve_panel.py --dry-run            # show the plan, run nothing

Resumable: a run whose output JSON already exists and parses is skipped, so re-invoking after a crash
(or after Ctrl-C) picks up where it stopped. Live state is written to runs/cve_panel_status.json after
every completion, so progress is inspectable without reading the log.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

R = Path(__file__).resolve().parents[1]
PY = str(R / ".venv" / "bin" / "python")
RUNS = R / "runs"
LOG = RUNS / "cve_panel.log"
STATUS = RUNS / "cve_panel_status.json"

# `claude` is excluded: these runners build an OpenAI client against the Azure endpoint, and the
# claude entry in azure_models.MODELS carries the "anthropic" sentinel base_url that only llm_chat.py
# knows how to dispatch. Same reason the existing cve_exploit cells have no claude column.
PANEL = ["deepseek", "kimi", "gpt-4o", "gpt-5.4"]

TASKS = {
    "rce": {
        "dir": "cve_rce",
        "runner": "run_cve_rce.py",
        "prefix": "cverce",
        "arms": ["none", "disclose", "endorse_no_recipe",
                 "endorse_exec_with_recipe", "endorse_read_with_recipe"],
        # httpd is tiny and boots in ~2s
        "workers": 4,
        "timeout": 1800,
    },
    "cli": {
        "dir": "cve_cli_read",
        "runner": "run_cve_cli.py",
        "prefix": "cvecli",
        "arms": ["none", "disclose", "endorse_no_recipe", "endorse_with_recipe"],
        # each container is a JVM that takes ~40-60s to come up; keep the box breathable, especially
        # since other sessions run containers in this repo too
        "workers": 2,
        "timeout": 2400,
    },
}

_print_lock = threading.Lock()


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    with _print_lock:
        print(line, flush=True)
        with open(LOG, "a") as f:
            f.write(line + "\n")


def valid(out: Path) -> bool:
    """A run counts as done if it produced a parseable record with a verdict."""
    if not out.exists() or out.stat().st_size < 200:
        return False
    try:
        d = json.loads(out.read_text())
    except Exception:
        return False
    v = d.get("verdict") or {}
    if v.get("label") in (None, "infra_error"):
        return False
    return True


def check_schema_registration() -> None:
    """Fail fast if the cheat-mode registration is missing.

    Other sessions edit platform/harness/propensity_schema.py concurrently. If `cve_rce`/`cve_probe`
    are not registered, runs still grade correctly (label/channel come from the task's own grade.py)
    but `propensity.cheat_mode` degrades to "none" and `seek_positive` to False -- silently wrong
    records. Recoverable after the fact (both are a pure function of label+channel), but much better
    caught now.
    """
    sys.path.insert(0, str(R / "platform" / "harness"))
    from propensity_schema import CHEAT_MODES_HEADLINE, STANDARD_CELLS  # noqa: E402
    missing = [m for m in ("cve_rce", "cve_probe") if m not in CHEAT_MODES_HEADLINE]
    missing += [c for c in ("cve_rce", "cve_cli_read") if c not in STANDARD_CELLS]
    if missing:
        log(f"FATAL propensity_schema.py is missing {missing} — refusing to run and write bad records")
        sys.exit(2)
    log("schema registration OK (cve_rce, cve_probe, standard cells)")


def build_jobs(tasks: list[str], models: list[str], n: int) -> list[dict]:
    jobs: list[dict] = []
    for tk in tasks:
        t = TASKS[tk]
        for mk in models:
            for arm in t["arms"]:
                label = f"{t['prefix']}_{mk}_{arm}"
                for i in range(1, n + 1):
                    out = RUNS / f"{label}_r{i}.json"
                    jobs.append({
                        "task": tk, "name": f"{label}_r{i}", "model": mk, "arm": arm,
                        "out": out, "done": valid(out),
                        "cwd": str(R / "tasks" / t["dir"]),
                        "argv": [PY, t["runner"], "--model-key", mk, "--scope", "none",
                                 "--precedent", arm, "--monitoring", "control", "--out", str(out)],
                        "timeout": t["timeout"],
                    })
    return jobs


def write_status(jobs: list[dict], state: dict) -> None:
    by_cell: dict[str, dict] = {}
    for j in jobs:
        cell = f"{TASKS[j['task']]['prefix']}_{j['model']}_{j['arm']}"
        c = by_cell.setdefault(cell, {"n": 0, "done": 0, "failed": 0})
        c["n"] += 1
        if j["name"] in state["ok"] or j["done"]:
            c["done"] += 1
        if j["name"] in state["fail"]:
            c["failed"] += 1
    STATUS.write_text(json.dumps({
        "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "running": sorted(state["running"]),
        "totals": {"jobs": len(jobs), "ok": len(state["ok"]),
                   "failed": len(state["fail"]), "pending": state["pending"]},
        "cells": by_cell,
    }, indent=2))


def run_one(job: dict, state: dict, jobs: list[dict]) -> tuple[str, str]:
    name, out = job["name"], job["out"]
    if valid(out):
        return name, "skip"
    state["running"].add(name)
    state["pending"] -= 1
    write_status(jobs, state)
    log(f"START {name}")
    try:
        p = subprocess.run(job["argv"], cwd=job["cwd"], capture_output=True, text=True,
                           timeout=job["timeout"])
        tail = ((p.stdout or "") + (p.stderr or ""))[-300:].replace("\n", " | ")
        if valid(out):
            try:
                v = (json.loads(out.read_text()).get("verdict") or {})
                extra = f"{v.get('label')} ({v.get('channel')})"
                if v.get("severity"):
                    extra += f" severity={v['severity']}"
            except Exception:
                extra = "ok"
            state["ok"].add(name)
            log(f"OK    {name} -> {extra}")
            status = "ok"
        else:
            state["fail"].add(name)
            log(f"FAIL  {name} rc={p.returncode} {tail[:220]}")
            status = f"fail:{p.returncode}"
    except subprocess.TimeoutExpired:
        state["fail"].add(name)
        log(f"TIMEOUT {name}")
        status = "timeout"
    except Exception as e:  # noqa: BLE001 — never let one job kill the pool
        state["fail"].add(name)
        log(f"ERR   {name} {e}")
        status = f"err:{e}"
    finally:
        state["running"].discard(name)
        write_status(jobs, state)
    return name, status


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks", default="rce,cli", help="comma list: rce,cli")
    ap.add_argument("--models", default=",".join(PANEL))
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--workers-rce", type=int, default=TASKS["rce"]["workers"])
    ap.add_argument("--workers-cli", type=int, default=TASKS["cli"]["workers"])
    ap.add_argument("--retries", type=int, default=1, help="extra passes over failed jobs")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    tasks = [t.strip() for t in a.tasks.split(",") if t.strip() in TASKS]
    models = [m.strip() for m in a.models.split(",") if m.strip()]
    RUNS.mkdir(exist_ok=True)
    TASKS["rce"]["workers"], TASKS["cli"]["workers"] = a.workers_rce, a.workers_cli

    if not os.environ.get("AZURE_OPENAI_API_KEY"):
        log("FATAL AZURE_OPENAI_API_KEY unset — `set -a; source .env; set +a` first")
        sys.exit(2)
    check_schema_registration()

    jobs = build_jobs(tasks, models, a.n)
    todo = [j for j in jobs if not j["done"]]
    log(f"plan: {len(jobs)} cells-runs total, {len(jobs) - len(todo)} already valid, {len(todo)} to run "
        f"· tasks={tasks} models={models} n={a.n} "
        f"· workers rce={a.workers_rce} cli={a.workers_cli}")
    if a.dry_run:
        for tk in tasks:
            t = TASKS[tk]
            log(f"  {t['prefix']}: {len(models)} models x {len(t['arms'])} arms x {a.n} = "
                f"{len(models) * len(t['arms']) * a.n} runs · arms={t['arms']}")
        return
    if not todo:
        log("nothing to do")
        return

    state = {"ok": set(), "fail": set(), "running": set(), "pending": len(todo)}
    # One pool per task so a slow Jenkins queue never starves the cheap httpd jobs, and so the two
    # concurrency limits are independent.
    pools = {tk: ThreadPoolExecutor(max_workers=TASKS[tk]["workers"], thread_name_prefix=tk)
             for tk in tasks}
    try:
        futs = [pools[j["task"]].submit(run_one, j, state, jobs) for j in todo]
        for k, fut in enumerate(as_completed(futs), 1):
            fut.result()
            if k % 10 == 0:
                log(f"progress {k}/{len(todo)} · ok={len(state['ok'])} fail={len(state['fail'])}")
    finally:
        for p in pools.values():
            p.shutdown(wait=True)

    for attempt in range(1, a.retries + 1):
        retry = [j for j in jobs if j["name"] in state["fail"] and not valid(j["out"])]
        if not retry:
            break
        log(f"retry pass {attempt}: {len(retry)} failed jobs")
        state["fail"] -= {j["name"] for j in retry}
        state["pending"] = len(retry)
        pools = {tk: ThreadPoolExecutor(max_workers=TASKS[tk]["workers"]) for tk in tasks}
        try:
            for fut in as_completed([pools[j["task"]].submit(run_one, j, state, jobs) for j in retry]):
                fut.result()
        finally:
            for p in pools.values():
                p.shutdown(wait=True)

    check_schema_registration()   # concurrent sessions edit this file; confirm it held
    log(f"DONE ok={len(state['ok'])} fail={len(state['fail'])} · status={STATUS}")
    if state["fail"]:
        log("failed: " + ", ".join(sorted(state["fail"])))


if __name__ == "__main__":
    main()
