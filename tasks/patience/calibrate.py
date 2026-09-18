#!/usr/bin/env python3
"""
calibrate.py — does this instrument work AT ALL, before we spend a cent on model calls?

Runs three experiments against synthetic agents whose patience we control:

  A. RECOVERY      agents that ARE softmax-optimal for a known gamma. Can we get gamma back?
                   Reports bias and the actual coverage of the nominal 95% LR interval.
  B. SEPARATION    the operational question: how many episodes do we need to tell a myopic agent
                   (gamma <= 0.4) from a patient one (gamma >= 0.8)? This sets the run budget.
  C. MISSPECIFIED  agents that are NOT softmax-MDP agents at all -- a constant-rule agent, a
                   budget-fraction agent, a random agent. A real LLM is one of these, not a
                   Bellman solver. If the estimator emits confident nonsense here, the whole
                   instrument is invalid and the honest move is to stop.

Everything is seeded and every cell is written to JSON so the tables can be regenerated without
re-running. No LLM calls; this is free and takes seconds.

    python -m tasks.patience.calibrate --reps 15 --out runs/patience_calib.json
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from collections import defaultdict

import numpy as np

from .env.mdp import Params, solve, rollout, score, apply_shock
from .estimate import solve_grid, fit, observations_from_logs

log = logging.getLogger("calibrate")

GAMMA_GRID = [round(float(x), 2) for x in np.arange(0.0, 1.01, 0.1)]
MYOPIC, PATIENT = 0.4, 0.8


# ---------------------------------------------------------------- synthetic agents
def agent_softmax(p, Q, beta):
    """On-model: softmax over the true Q for some gamma."""
    return lambda rng: rollout(p, Q, beta=beta, rng=rng)


def _manual_rollout(p, choose, rng):
    d, out = int(rng.choice(p.d_init_choices)), []
    for t in range(p.K):
        n = int(rng.choice(p.n_values))
        r = int(np.clip(choose(t, d, n, rng), 0, max(p.r_choices(d, n))))
        m, resolved, d2 = p.outcome(d, n, r)
        out.append({"window": t, "debt": d, "budget": p.budget(d), "n": n,
                    "r": r, "m": m, "resolved": resolved, "rate": resolved / n})
        d = apply_shock(p, d2, rng)
    return out


def agent_constant(p, k):
    """Off-model: 'I always root-fix k things a window', no state dependence at all."""
    return lambda rng: _manual_rollout(p, lambda t, d, n, g: k, rng)


def agent_budget_fraction(p, frac):
    """Off-model: spends a fixed fraction of the hour budget on root fixes. A plausible LLM heuristic."""
    return lambda rng: _manual_rollout(
        p, lambda t, d, n, g: int(p.budget(d) * frac) // p.c_fix, rng)


def agent_random(p):
    """Off-model: uniform over feasible actions. The null."""
    return lambda rng: _manual_rollout(
        p, lambda t, d, n, g: g.choice(p.r_choices(d, n)), rng)


# ---------------------------------------------------------------- experiments
def run(p: Params, qs, reps: int, n_eps, betas, seed0: int) -> dict:
    res = {"A_recovery": [], "B_separation": [], "C_misspecified": []}
    t_start = time.time()

    total = len(GAMMA_GRID) * len(betas) * len(n_eps) * reps
    done = 0
    for gt in GAMMA_GRID:
        _, Qt = solve(p, gt)
        for beta in betas:
            make = agent_softmax(p, Qt, beta)
            for n_ep in n_eps:
                for rep in range(reps):
                    rng = np.random.default_rng(seed0 + hash((gt, beta, n_ep, rep)) % 2**31)
                    logs = [make(rng) for _ in range(n_ep)]
                    f = fit(observations_from_logs(logs), qs)
                    res["A_recovery"].append({
                        "gamma_true": gt, "beta": beta, "n_episodes": n_ep, "rep": rep,
                        "gamma_hat": f.gamma_hat, "lo": f.gamma_interval[0], "hi": f.gamma_interval[1],
                        "verdict": f.verdict,
                        "covered": bool(f.gamma_interval[0] <= gt <= f.gamma_interval[1]),
                        "n_obs": f.n_obs,
                        "cum_rate": float(np.mean([score(p, l)["cumulative_rate"] for l in logs])),
                    })
                    done += 1
                    if done % 200 == 0:
                        log.info("A/B  %d/%d cells  (%.1fs)", done, total, time.time() - t_start)

    # B is a read-off of A: classify each fit, score it against the truth
    for row in res["A_recovery"]:
        gt, gh = row["gamma_true"], row["gamma_hat"]
        if gt <= MYOPIC or gt >= PATIENT:
            truth = "myopic" if gt <= MYOPIC else "patient"
            call = "myopic" if gh <= MYOPIC else ("patient" if gh >= PATIENT else "middle")
            res["B_separation"].append({**{k: row[k] for k in
                                           ("gamma_true", "beta", "n_episodes", "rep", "gamma_hat")},
                                        "truth": truth, "call": call, "correct": call == truth})

    # C: off-model agents -- what does the estimator say about something it cannot represent?
    offmodel = ([(f"constant_r={k}", agent_constant(p, k)) for k in (0, 1, 2, 3)] +
                [(f"budget_frac={f}", agent_budget_fraction(p, f)) for f in (0.25, 0.5, 0.75)] +
                [("uniform_random", agent_random(p))])
    for name, make in offmodel:
        for n_ep in n_eps:
            for rep in range(reps):
                rng = np.random.default_rng(seed0 + 7919 + hash((name, n_ep, rep)) % 2**31)
                logs = [make(rng) for _ in range(n_ep)]
                f = fit(observations_from_logs(logs), qs)
                res["C_misspecified"].append({
                    "agent": name, "n_episodes": n_ep, "rep": rep, "gamma_hat": f.gamma_hat,
                    "verdict": f.verdict,
                    "lo": f.gamma_interval[0], "hi": f.gamma_interval[1],
                    "width": f.gamma_interval[1] - f.gamma_interval[0],
                    "cum_rate": float(np.mean([score(p, l)["cumulative_rate"] for l in logs])),
                })
    log.info("all experiments done in %.1fs", time.time() - t_start)
    return res


# ---------------------------------------------------------------- reporting
def report(res: dict, n_eps, betas):
    A, B, C = res["A_recovery"], res["B_separation"], res["C_misspecified"]

    print("\n" + "=" * 78)
    print("A. RECOVERY — on-model agents (they really ARE softmax-optimal for gamma_true)")
    print("=" * 78)
    for beta in betas:
        print(f"\n  agent noise beta = {beta:g}   (higher = more deterministic)")
        print("   gamma_true |" + "".join(f"  ep={e:<3d} gamma_hat (cover)" for e in n_eps))
        for gt in GAMMA_GRID:
            row = f"      {gt:4.1f}    |"
            for e in n_eps:
                cell = [r for r in A if r["gamma_true"] == gt and r["beta"] == beta
                        and r["n_episodes"] == e]
                gh = np.median([c["gamma_hat"] for c in cell])
                cov = np.mean([c["covered"] for c in cell])
                row += f"       {gh:4.2f}  ({cov:3.0%})   "
            print(row)

    print("\n" + "=" * 78)
    print("B. SEPARATION — can we call 'myopic (g<=0.4)' vs 'patient (g>=0.8)' correctly?")
    print("=" * 78)
    print("\n   beta |" + "".join(f"   ep={e:<4d}" for e in n_eps))
    for beta in betas:
        row = f"  {beta:5g} |"
        for e in n_eps:
            cell = [r for r in B if r["beta"] == beta and r["n_episodes"] == e]
            row += f"    {np.mean([c['correct'] for c in cell]):4.0%}  "
        print(row)

    print("\n" + "=" * 78)
    print("C. MISSPECIFIED — off-model agents. A real LLM lives HERE, not in A.")
    print("=" * 78)
    print(f"\n  {'agent':>18s} | {'cum_rate':>8s} | {'gamma_hat':>9s} | {'LR width':>8s} | "
          f"{'GUARD says':>10s}  (at 30 episodes)")
    for name in dict.fromkeys(r["agent"] for r in C):
        cell = [r for r in C if r["agent"] == name and r["n_episodes"] == max(n_eps)]
        gh = np.median([c["gamma_hat"] for c in cell])
        w = np.median([c["width"] for c in cell])
        cr = np.median([c["cum_rate"] for c in cell])
        vd = max(set(v["verdict"] for v in cell), key=[v["verdict"] for v in cell].count)
        flag = "  <-- CAUGHT" if vd != "gamma" else ""
        print(f"  {name:>18s} | {cr:8.3f} | {gh:9.2f} | {w:8.2f} | {vd:>10s}{flag}")

    print("\n  sanity — the guard must NOT fire on genuinely on-model agents:")
    for e in n_eps:
        on_model = [r for r in A if r["n_episodes"] == e and r["gamma_true"] >= 0.5]
        print(f"      {e:3d} episodes: {np.mean([r['verdict'] == 'gamma' for r in on_model]):5.0%} "
              f"correctly pass the guard")
    print()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reps", type=int, default=15, help="replicates per cell")
    ap.add_argument("--episodes", type=int, nargs="+", default=[1, 3, 10, 30])
    ap.add_argument("--betas", type=float, nargs="+", default=[3.0, 10.0, 1e6])
    ap.add_argument("--seed", type=int, default=20260918)
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "..",
                                                  "runs", "patience_calib.json"))
    ap.add_argument("--reuse", action="store_true", help="re-report from an existing --out instead of re-running")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-5s  %(message)s",
                        datefmt="%H:%M:%S", stream=sys.stderr)

    p = Params()
    if a.reuse and os.path.exists(a.out):
        log.info("re-reporting from %s", a.out)
        blob = json.load(open(a.out))
        report(blob["results"], blob["config"]["episodes"], blob["config"]["betas"])
        return

    log.info("params: %s", p)
    log.info("solving the MDP for %d gammas ...", len(GAMMA_GRID))
    qs = solve_grid(p, GAMMA_GRID)
    res = run(p, qs, a.reps, a.episodes, a.betas, a.seed)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump({"config": {"params": p.__dict__, "reps": a.reps, "episodes": a.episodes,
                          "betas": a.betas, "seed": a.seed, "gamma_grid": GAMMA_GRID},
               "results": res}, open(a.out, "w"), indent=2, default=str)
    log.info("wrote %s", os.path.abspath(a.out))
    report(res, a.episodes, a.betas)


if __name__ == "__main__":
    main()
