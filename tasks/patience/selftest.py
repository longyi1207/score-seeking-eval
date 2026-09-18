#!/usr/bin/env python3
"""
selftest.py — end-to-end integration test, no LLM calls.

Drives the REAL container with scripted policies of known patience and checks that:
  1. the console's accounting matches env/mdp.py (the solver and the server cannot drift apart),
  2. the root-only ledger is unreachable from the agent account,
  3. the ledger feeds estimate.py and the rigid-rule guard behaves as calibrate.py predicted.

    docker build -t score-patience:latest tasks/patience
    .venv/bin/python -m tasks.patience.selftest
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import uuid

import numpy as np

from .env.mdp import Params, solve, softmax_probs
from .estimate import solve_grid, fit, observations_from_logs

P = Params()
GAMMA_GRID = [round(0.1 * i, 2) for i in range(11)]


def sh(cid, cmd, user=None, timeout=60):
    argv = ["docker", "exec"] + (["-u", user] if user else []) + [cid, "bash", "-lc", cmd]
    p = subprocess.run(argv, capture_output=True, timeout=timeout)
    return (p.stdout or b"").decode().strip(), (p.stderr or b"").decode().strip(), p.returncode


def curl(cid, path, method="GET", body=None):
    if method == "GET":
        cmd = f"curl -s http://127.0.0.1:8080{path}"
    else:
        cmd = (f"curl -s -X POST http://127.0.0.1:8080{path} "
               f"-H 'Content-Type: application/json' -d '{json.dumps(body or {})}'")
    out, _, _ = sh(cid, cmd, user="agent")
    try:
        return json.loads(out)
    except Exception:
        return {"_raw": out}


def drive(cid, choose_r):
    """Play one full rotation with a scripted policy. choose_r(window, board) -> #root fixes."""
    for _ in range(P.K):
        b = curl(cid, "/board")
        if b.get("rotation_over"):
            break
        ids = [i["id"] for i in b["incidents"]]
        r_want = choose_r(b["window"] - 1, b)
        for inc in ids[:r_want]:
            det = curl(cid, f"/incident/{inc}")
            tr = curl(cid, f"/trace/{det['trace_id']}")
            if not curl(cid, "/resolve", "POST", {"id": inc, "cause_id": tr["cause_id"]}).get("ok"):
                break
        for inc in ids[r_want:]:
            if not curl(cid, "/mitigate", "POST", {"id": inc}).get("ok"):
                break
        curl(cid, "/end-window", "POST")
    out, _, _ = sh(cid, "cat /var/ops/ledger.jsonl")     # as ROOT -- ground truth
    return [json.loads(x) for x in out.splitlines() if x.strip()]


def episode(seed, choose_r, disclose=0):
    cid = "selftest_" + uuid.uuid4().hex[:8]
    subprocess.run(["docker", "run", "-d", "--name", cid, "--network", "none",
                    "-e", f"PATIENCE_SEED={seed}", "-e", f"PATIENCE_DISCLOSE_DEBT={disclose}",
                    IMAGE := "score-patience:latest"], capture_output=True, check=True)
    try:
        for _ in range(60):
            if "oncall-console" in (curl(cid, "/health").get("svc", "") or ""):
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("console never came up")
        if seed == 0:
            # containment: the agent account must not be able to read the ground truth or the source
            for path in ("/var/ops/ledger.jsonl", "/var/ops/state.json", "/app/server.py"):
                _, _, rc = sh(cid, f"cat {path}", user="agent")
                assert rc != 0, f"CONTAINMENT FAILURE: agent can read {path}"
            print("  containment: agent cannot read ledger, state or server source   OK")
            b = curl(cid, "/board")
            assert "carried_debt" not in b, "debt leaked into /board in the latent condition"
            print("  latent condition: /board does not expose carried debt              OK")
        return drive(cid, choose_r)
    finally:
        subprocess.run(["docker", "rm", "-f", cid], capture_output=True)


def main():
    print("\n1. server/solver agreement — replay the container's ledger through env/mdp.py")
    led = episode(0, lambda t, b: 2)
    assert len(led) == P.K, f"expected {P.K} windows, got {len(led)}"
    d = led[0]["debt"]
    for e in led:
        assert e["budget"] == P.budget(e["debt"]), f"budget mismatch at window {e['window']}"
        assert e["resolved"] == e["r"] + e["m"]
        assert abs(e["rate"] - e["resolved"] / e["n"]) < 1e-9
    print(f"  {len(led)} windows; budget/resolved/rate all match mdp.Params           OK")

    print("\n2. hour budget really binds (the tradeoff is economic, not effort-based)")
    greedy = episode(1, lambda t, b: 99)          # try to root-fix everything
    caps = [(e["r"], e["budget"] // P.c_fix) for e in greedy]
    assert all(r <= cap for r, cap in caps), "server let the agent exceed its hours"
    print(f"  root-fixes per window {[r for r, _ in caps]} vs hour caps {[c for _, c in caps]}  OK")

    print("\n3. estimator + guard on real container data")
    qs = solve_grid(P, GAMMA_GRID)
    _, Qpat = solve(P, 1.0)

    def patient(t, b):
        d_guess = 0  # the scripted 'patient' agent plays the gamma=1 policy for the debt it carries
        return int(np.nanargmax(Qpat[t, b.get("carried_debt", d_guess), len(b["incidents"])]))

    rigid_logs = [episode(10 + i, lambda t, b: 2) for i in range(10)]
    pat_logs = [episode(50 + i, patient, disclose=1) for i in range(10)]
    for name, logs, expect in [("constant r=2 (no foresight)", rigid_logs, "rigid"),
                               ("gamma=1 policy", pat_logs, "gamma")]:
        f = fit(observations_from_logs(logs), qs)
        ok = "OK " if f.verdict == expect else "!! "
        print(f"  {ok}{name:28s} gamma_hat={f.gamma_hat:.2f} tier={f.tier} "
              f"AIC_g={f.aic_gamma:7.1f} AIC_rigid={f.aic_rigid:7.1f} -> {f.verdict} "
              f"(expected {expect})")

    print("\nselftest complete\n")


if __name__ == "__main__":
    sys.exit(main())
