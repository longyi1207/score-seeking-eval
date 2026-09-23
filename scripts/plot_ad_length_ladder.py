#!/usr/bin/env python3
"""plot_ad_length_ladder.py — dose-response figure for the AD honest-path length ladder.

Reads runs/ad_panel/ad_len_*.json and draws seek rate vs honest-path length (hops), overlaying
every (model, scope) series present. Hops is the x-axis (the model-independent dose; agent turns
compress model-dependently — see AD_LENGTH_LADDER.md). Panel (b) plots seek rate vs median honest
turns for the primary scope=none series. Annotates per-point n and flags any rung with 0 honest
solves (capability-confounded). Run after the panels land.

    python3 scripts/plot_ad_length_ladder.py [runs/ad_panel]
Output: docs/figures/08_ad_length_ladder.svg
"""
from __future__ import annotations
import argparse, glob, json, os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RUNG_ORDER = ["L1", "L2", "L3", "L4", "L5"]
HOPS = {"L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 6}
INK, MUTED = "#1a1a2e", "#8d99ae"
# per-(model,scope) style
STYLE = {
    ("DeepSeek-V4-Pro", "none"):   ("#c1121f", "-o", "DeepSeek (none)"),
    ("gpt-5.4", "none"):           ("#1d4e89", "-s", "gpt-5.4 (none)"),
    ("DeepSeek-V4-Pro", "forbid"): ("#c1121f", "--x", "DeepSeek (forbid)"),
    ("gpt-5.4", "forbid"):         ("#1d4e89", "--x", "gpt-5.4 (forbid)"),
}


def collect(runs_dir):
    cells = defaultdict(lambda: {"honest": 0, "seek": 0, "fail": 0, "honest_steps": []})
    for f in sorted(glob.glob(os.path.join(runs_dir, "ad_len_*.json"))):
        try:
            r = json.load(open(f))
        except Exception:
            continue
        rung = r.get("ad_length")
        if rung not in RUNG_ORDER:
            continue
        key = (r.get("model"), r.get("scope", "none"), rung)
        c = cells[key]; lab = r.get("label", "fail")
        if lab == "honest_solve":
            c["honest"] += 1; c["honest_steps"].append(r.get("steps", 0))
        elif lab == "score_seek_success":
            c["seek"] += 1
        else:
            c["fail"] += 1
    return cells


def med(xs): xs = sorted(xs); return xs[len(xs) // 2] if xs else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs_dir", nargs="?", default="runs/ad_panel")
    ap.add_argument("--out", default="docs/figures/08_ad_length_ladder.svg")
    a = ap.parse_args()
    cells = collect(a.runs_dir)

    series = {}  # (model,scope) -> {rung: (rate,n,fail,med_h)}
    for (model, scope, rung), c in cells.items():
        comp = c["honest"] + c["seek"]
        if comp + c["fail"] == 0:
            continue
        series.setdefault((model, scope), {})[rung] = (
            (c["seek"] / comp) if comp else 0.0, comp + c["fail"], c["fail"], med(c["honest_steps"]))
    if not series:
        raise SystemExit(f"no ladder runs in {a.runs_dir}")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.6))
    fig.suptitle("AD score-seeking vs honest-path length (matched prompts, ACL-depth dose)",
                 fontsize=13, color=INK, fontweight="bold")

    # (a) seek rate vs hops, one line per (model, scope)
    ordered = sorted(series, key=lambda k: (k[1] != "none", k[0]))
    for key in ordered:
        col, mstyle, label = STYLE.get(key, ("#555", "-o", f"{key[0]} ({key[1]})"))
        pts = series[key]
        rs = [r for r in RUNG_ORDER if r in pts]
        xs = [HOPS[r] for r in rs]; ys = [pts[r][0] for r in rs]
        ax1.plot(xs, ys, mstyle, color=col, lw=2, ms=8, label=label,
                 alpha=0.9 if key[1] == "none" else 0.6)
        for r in rs:
            rate, n, fail, _ = pts[r]
            ax1.annotate(f"{rate:.0%}", (HOPS[r], rate), textcoords="offset points",
                         xytext=(0, 8), ha="center", fontsize=8, color=col)
            if fail == n:
                ax1.annotate("0 honest", (HOPS[r], rate), textcoords="offset points",
                             xytext=(0, -14), ha="center", fontsize=7, color=MUTED)
    ax1.set_xticks([HOPS[r] for r in RUNG_ORDER])
    ax1.set_xticklabels([f"{r}\n{HOPS[r]}h" for r in RUNG_ORDER])
    ax1.set_xlabel("honest-chain depth (hops)"); ax1.set_ylabel("seek rate (seeks / completed)")
    ax1.set_ylim(-0.05, 1.08); ax1.set_title("(a) seek rate vs hops", fontsize=11, color=INK)
    ax1.grid(axis="y", alpha=0.25); ax1.legend(fontsize=8, loc="lower left", framealpha=0.9)

    # (b) seek rate vs median honest turns, scope=none series only
    for key in ordered:
        if key[1] != "none":
            continue
        col, _, label = STYLE.get(key, ("#555", "-o", f"{key[0]}"))
        pts = series[key]
        xy = sorted((pts[r][3], pts[r][0], r) for r in pts if pts[r][3] is not None)
        if xy:
            ax2.plot([p[0] for p in xy], [p[1] for p in xy], "-o", color=col, lw=2, ms=7, label=label)
            for x, y, r in xy:
                ax2.annotate(r, (x, y), textcoords="offset points", xytext=(5, 5),
                             fontsize=8, color=col)
    ax2.set_xlabel("median honest-solve turns"); ax2.set_ylabel("seek rate")
    ax2.set_ylim(-0.05, 1.08); ax2.set_title("(b) seek rate vs honest effort (turns)", fontsize=11, color=INK)
    ax2.grid(alpha=0.25); ax2.legend(fontsize=8, loc="lower right", framealpha=0.9)

    for ax in (ax1, ax2):
        for s in ("top", "right"): ax.spines[s].set_visible(False)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    fig.savefig(a.out); print("wrote", a.out)
    print("series:", {f"{k[0]}/{k[1]}": {r: f"{v[0]:.0%}" for r, v in sorted(s.items())}
                      for k, s in series.items()})


if __name__ == "__main__":
    main()
