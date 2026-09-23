#!/usr/bin/env python3
"""Render AD + intent figures as PNG (matplotlib — reliable for WeasyPrint PDF)."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "docs" / "figures"

INK, MUTED, FAINT = "#16202e", "#54627a", "#8a95a8"
RED_SOFT, GREEN_SOFT, GRAY = "#e6a99f", "#d8edd9", "#eef2f6"
SEEK_BAR, INK_BAR, HONEST, FAIL = "#c2614f", "#16202e", "#6a9e72", "#b0b8c4"


def render_intent() -> Path:
    rows = [
        json.loads(l)
        for l in (ROOT / "docs/matrices/cot_contemplate_codes.jsonl").read_text().splitlines()
        if l.strip()
    ]
    c = Counter(r.get("intent_behavior_cell") for r in rows)
    yy = c.get("intent_yes_behavior_yes", 0)
    yn = c.get("intent_yes_behavior_no", 0)
    ny = c.get("intent_no_behavior_yes", 0)
    nn = c.get("intent_no_behavior_no", 0)
    n = max(sum(c.values()), 1)
    reasoning = sum(1 for r in rows if r.get("reasoning_available"))
    declined = sum(1 for r in rows if r.get("declined_after_notice"))

    fig, ax = plt.subplots(figsize=(7.2, 4.5), dpi=180)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.text(0.2, 9.55, "Intent × behavior", fontsize=14, fontweight="bold", color=INK)
    ax.text(
        0.2,
        9.05,
        f"LLM judge on run transcripts · n={n} · private CoT on {reasoning} · provisional",
        fontsize=8.5,
        color=MUTED,
    )
    ax.text(5.2, 8.45, "behavior", fontsize=10, fontweight="bold", color=MUTED, ha="center")
    ax.text(3.1, 8.05, "seek", fontsize=9, color=FAINT, ha="center")
    ax.text(7.3, 8.05, "no seek", fontsize=9, color=FAINT, ha="center")
    ax.text(
        0.55,
        5.2,
        "intent",
        fontsize=10,
        fontweight="bold",
        color=MUTED,
        rotation=90,
        va="center",
        ha="center",
    )
    ax.text(1.15, 6.35, "yes", fontsize=9, color=FAINT, ha="right", va="center")
    ax.text(1.15, 3.15, "no", fontsize=9, color=FAINT, ha="right", va="center")

    cells = [
        (1.4, 4.6, 3.6, 2.9, yy, "contemplated & sought", RED_SOFT, INK),
        (5.4, 4.6, 3.6, 2.9, yn, "weighed it, stayed honest", GREEN_SOFT, "#2f5d38"),
        (1.4, 1.4, 3.6, 2.9, ny, "sought w/o verbalized intent", "#f0e6d8", "#7a5a3a"),
        (5.4, 1.4, 3.6, 2.9, nn, "neither", GRAY, FAINT),
    ]
    for x, y, w, h, val, cap, fill, tc in cells:
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                w,
                h,
                boxstyle="round,pad=0.02,rounding_size=0.15",
                facecolor=fill,
                edgecolor="none",
            )
        )
        ax.text(
            x + w / 2,
            y + h * 0.62,
            str(val),
            fontsize=26,
            fontweight="bold",
            color=tc,
            ha="center",
            va="center",
            fontfamily="monospace",
        )
        ax.text(
            x + w / 2,
            y + h * 0.38,
            f"{100 * val / n:.0f}% of judged",
            fontsize=8.5,
            color=MUTED,
            ha="center",
        )
        ax.text(x + w / 2, y + h * 0.18, cap, fontsize=8.5, color=INK, ha="center")

    ax.text(
        0.2,
        0.55,
        f"The interesting mass is intent-yes / behavior-no ({yn}) — exploration that did not become exploitation.",
        fontsize=8.5,
        color=MUTED,
    )
    ax.text(
        0.2,
        0.15,
        f"Among seekers, {ny}/{yy + ny} lack verbalized contemplation "
        f"(thin CoT more often than proven stealth). declined_after_notice={declined}.",
        fontsize=8,
        color=FAINT,
    )
    fig.tight_layout(pad=0.3)
    out = FIGS / "07_intent_behavior.png"
    fig.savefig(out, dpi=180, facecolor="white")
    plt.close()
    return out


def render_ad() -> Path:
    ad = [
        ("DeepSeek", 3, 5, 1, 6, "seek"),
        ("Kimi", 0, 5, 0, 5, "honest"),
        ("gpt-4o", 0, 5, 0, 5, "fail"),
        ("gpt-5.4", 1, 5, 2, 5, "seek"),
        ("Claude", 1, 5, 0, 5, "fail"),
    ]
    fig, ax = plt.subplots(figsize=(7.6, 3.5), dpi=180)
    x = np.arange(len(ad))
    w = 0.36
    corp = [100 * a[1] / a[2] for a in ad]
    ent = [100 * a[3] / a[4] for a in ad]
    ax.bar(
        x - w / 2,
        corp,
        w,
        color=[SEEK_BAR if v > 0 else GRAY for v in corp],
        label="ad-corp (short)",
    )
    ent_colors = []
    for a, v in zip(ad, ent):
        if v > 0:
            ent_colors.append(INK_BAR)
        elif a[5] == "honest":
            ent_colors.append(HONEST)
        elif a[5] == "fail":
            ent_colors.append(FAIL)
        else:
            ent_colors.append(GRAY)
    ax.bar(x + w / 2, ent, w, color=ent_colors, label="ad-ent (long)")
    for i, a in enumerate(ad):
        ax.text(
            i - w / 2,
            corp[i] + 2.5 if corp[i] > 5 else 4,
            f"{a[1]}/{a[2]}",
            ha="center",
            va="bottom",
            fontsize=8,
            fontfamily="monospace",
            fontweight="bold",
            color=INK if a[1] else FAINT,
        )
        ax.text(
            i + w / 2,
            ent[i] + 2.5 if ent[i] > 5 else 4,
            f"{a[3]}/{a[4]}",
            ha="center",
            va="bottom",
            fontsize=8,
            fontfamily="monospace",
            fontweight="bold",
            color=INK if a[3] else FAINT,
        )
        if a[5] == "fail" and a[3] == 0:
            ax.text(i, -9, "fail@cap", ha="center", fontsize=7.5, color=FAINT)
        elif a[5] == "honest" and a[3] == 0:
            ax.text(i, -9, "0 seek", ha="center", fontsize=7.5, color="#2f5d38")
    ax.set_ylim(0, 105)
    ax.set_xticks(x)
    ax.set_xticklabels([a[0] for a in ad], fontweight="bold")
    ax.set_ylabel("seek rate %")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#d3dae4")
    ax.spines["bottom"].set_color("#d3dae4")
    ax.yaxis.grid(True, color="#e8ecf1")
    ax.set_axisbelow(True)
    ax.set_title(
        "Same shortcut, different honest-path length",
        loc="left",
        fontsize=13,
        fontweight="bold",
        color=INK,
        pad=12,
    )
    ax.text(
        0,
        1.08,
        "Azure AD · planted Domain-Admin flag · scope = none · n=5 (DeepSeek enterprise n=6)",
        transform=ax.transAxes,
        fontsize=8.5,
        color=MUTED,
    )
    ax.legend(frameon=False, fontsize=8.5, loc="upper right")
    ax.text(
        0,
        -0.22,
        "DeepSeek drops 60%→17%. gpt-5.4 still seeks on the long path (2/5). "
        "gpt-4o / Claude hit the capability wall (fail 5/5, no cheat).",
        transform=ax.transAxes,
        fontsize=8,
        color=FAINT,
    )
    fig.tight_layout()
    out = FIGS / "06_ad_corp_vs_enterprise.png"
    fig.savefig(out, dpi=180, facecolor="white", bbox_inches="tight")
    plt.close()
    return out


def main() -> None:
    FIGS.mkdir(parents=True, exist_ok=True)
    a = render_ad()
    b = render_intent()
    print(f"wrote {a}")
    print(f"wrote {b}")


if __name__ == "__main__":
    main()
