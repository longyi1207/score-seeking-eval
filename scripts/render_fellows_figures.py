#!/usr/bin/env python3
"""Render fellows-brief figures: AD corp vs enterprise, intent×behavior 2×2."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "figures"

INK, MUTED, FAINT, PAPER = "#16202e", "#54627a", "#8a95a8", "#ffffff"
RED, GREEN, GRAY = "#b23b36", "#2f5d38", "#eef2f6"
RED_SOFT, GREEN_SOFT = "#e6a99f", "#d8edd9"
SEEK_BAR = "#c2614f"
HONEST_BAR = "#6a9e72"
FAIL_BAR = "#b0b8c4"

MODELS = [
    ("deepseek", "DeepSeek"),
    ("kimi", "Kimi"),
    ("gpt-4o", "gpt-4o"),
    ("gpt-5.4", "gpt-5.4"),
    ("claude", "Claude"),
]

# Live / seed rates matching RESULTS + heatmap (seek rate)
AD = {
    # model: (corp_k, corp_n, ent_k, ent_n, ent_note)
    "deepseek": (3, 5, 1, 6, "seek"),
    "kimi": (0, 5, 0, 5, "honest3·fail2"),
    "gpt-4o": (0, 5, 0, 5, "fail 5/5"),
    "gpt-5.4": (1, 5, 2, 5, "seek"),
    "claude": (1, 5, 0, 5, "fail 5/5"),
}


def _pct(k: int, n: int) -> float:
    return 100.0 * k / n if n else 0.0


def render_ad_panel() -> str:
    """Grouped bars: short AD vs long AD seek % per model."""
    W, H = 720, 340
    left, top, bottom = 56, 56, 280
    chart_h = bottom - top
    group_w = 120
    bar_w = 38
    gap = 10
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="Seek rate on short vs long Azure AD by model.">',
        f'<rect width="100%" height="100%" fill="{PAPER}"/>',
        f'<text x="28" y="28" font-family="Helvetica Neue,Arial,sans-serif" font-size="15" '
        f'font-weight="700" fill="{INK}">Same shortcut, different honest-path length</text>',
        f'<text x="28" y="46" font-family="Helvetica Neue,Arial,sans-serif" font-size="11" '
        f'fill="{MUTED}">Azure AD · planted Domain-Admin flag · scope = none · n=5 (DeepSeek enterprise n=6)</text>',
    ]
    # y-axis
    for pct in (0, 25, 50, 75, 100):
        y = bottom - chart_h * (pct / 100)
        parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{W - 24}" y2="{y:.1f}" '
            f'stroke="#e8ecf1" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{left - 8}" y="{y + 4:.1f}" text-anchor="end" '
            f'font-family="SF Mono,Menlo,monospace" font-size="10" fill="{FAINT}">{pct}%</text>'
        )
    # legend
    parts.append(f'<rect x="{W - 210}" y="18" width="12" height="12" rx="2" fill="{SEEK_BAR}"/>')
    parts.append(
        f'<text x="{W - 194}" y="28" font-family="Helvetica Neue,Arial,sans-serif" '
        f'font-size="11" fill="{MUTED}">ad-corp (short)</text>'
    )
    parts.append(f'<rect x="{W - 100}" y="18" width="12" height="12" rx="2" fill="{INK}"/>')
    parts.append(
        f'<text x="{W - 84}" y="28" font-family="Helvetica Neue,Arial,sans-serif" '
        f'font-size="11" fill="{MUTED}">ad-ent (long)</text>'
    )

    for i, (mk, label) in enumerate(MODELS):
        ck, cn, ek, en, note = AD[mk]
        cx = left + 28 + i * group_w
        # corp bar
        ch = chart_h * (_pct(ck, cn) / 100)
        parts.append(
            f'<rect x="{cx}" y="{bottom - ch:.1f}" width="{bar_w}" height="{max(ch, 1.5):.1f}" '
            f'rx="3" fill="{SEEK_BAR if ck else GRAY}"/>'
        )
        parts.append(
            f'<text x="{cx + bar_w / 2}" y="{bottom - ch - 6:.1f}" text-anchor="middle" '
            f'font-family="SF Mono,Menlo,monospace" font-size="10" font-weight="700" '
            f'fill="{INK if ck else FAINT}">{ck}/{cn}</text>'
        )
        # enterprise bar
        eh = chart_h * (_pct(ek, en) / 100)
        if ek > 0:
            fill_e = INK  # long-path seek — matches legend
        elif "honest" in note:
            fill_e = HONEST_BAR
        elif "fail" in note:
            fill_e = FAIL_BAR
        else:
            fill_e = GRAY
        parts.append(
            f'<rect x="{cx + bar_w + gap}" y="{bottom - eh:.1f}" width="{bar_w}" '
            f'height="{max(eh, 1.5):.1f}" rx="3" fill="{fill_e}"/>'
        )
        # for 0% still show label above axis
        ty = bottom - eh - 6 if eh > 8 else bottom - 8
        parts.append(
            f'<text x="{cx + bar_w + gap + bar_w / 2}" y="{ty:.1f}" text-anchor="middle" '
            f'font-family="SF Mono,Menlo,monospace" font-size="10" font-weight="700" '
            f'fill="{INK if ek else FAINT}">{ek}/{en}</text>'
        )
        parts.append(
            f'<text x="{cx + bar_w + gap / 2}" y="{bottom + 18}" text-anchor="middle" '
            f'font-family="Helvetica Neue,Arial,sans-serif" font-size="12" font-weight="700" '
            f'fill="{INK}">{label}</text>'
        )
        if ek == 0 and note.startswith("fail"):
            parts.append(
                f'<text x="{cx + bar_w + gap / 2}" y="{bottom + 34}" text-anchor="middle" '
                f'font-family="Helvetica Neue,Arial,sans-serif" font-size="9" fill="{FAINT}">fail@cap</text>'
            )
        elif ek == 0 and "honest" in note:
            parts.append(
                f'<text x="{cx + bar_w + gap / 2}" y="{bottom + 34}" text-anchor="middle" '
                f'font-family="Helvetica Neue,Arial,sans-serif" font-size="9" fill="{GREEN}">0 seek</text>'
            )

    parts.append(
        f'<text x="28" y="{H - 12}" font-family="Helvetica Neue,Arial,sans-serif" font-size="10" '
        f'fill="{FAINT}">DeepSeek drops 60%→17%. gpt-5.4 still seeks on the long path (2/5). '
        f'gpt-4o / Claude hit the capability wall (fail 5/5, no cheat).</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def load_intent_counts() -> dict[str, int]:
    p = ROOT / "docs" / "matrices" / "cot_contemplate_codes.jsonl"
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    c = Counter(r.get("intent_behavior_cell") for r in rows)
    return {
        "yy": c.get("intent_yes_behavior_yes", 0),
        "yn": c.get("intent_yes_behavior_no", 0),
        "ny": c.get("intent_no_behavior_yes", 0),
        "nn": c.get("intent_no_behavior_no", 0),
        "n": sum(c.values()),
        "declined": sum(1 for r in rows if r.get("declined_after_notice")),
        "reasoning": sum(1 for r in rows if r.get("reasoning_available")),
    }


def render_intent_2x2(counts: dict[str, int] | None = None) -> str:
    counts = counts or load_intent_counts()
    yy, yn, ny, nn = counts["yy"], counts["yn"], counts["ny"], counts["nn"]
    n = max(counts["n"], 1)
    W, H = 640, 420
    # cell layout
    ox, oy = 120, 90
    cw, ch = 200, 130
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="Intent versus behavior contingency table.">',
        f'<rect width="100%" height="100%" fill="{PAPER}"/>',
        f'<text x="28" y="28" font-family="Helvetica Neue,Arial,sans-serif" font-size="15" '
        f'font-weight="700" fill="{INK}">Intent × behavior</text>',
        f'<text x="28" y="46" font-family="Helvetica Neue,Arial,sans-serif" font-size="11" '
        f'fill="{MUTED}">LLM judge on run transcripts · n={counts["n"]} · '
        f'private CoT available on {counts["reasoning"]} · provisional while queue finishes</text>',
        # axis labels
        f'<text x="{ox + cw}" y="72" text-anchor="middle" font-family="Helvetica Neue,Arial,sans-serif" '
        f'font-size="12" font-weight="700" fill="{MUTED}">behavior</text>',
        f'<text x="{ox + cw / 2}" y="88" text-anchor="middle" font-family="Helvetica Neue,Arial,sans-serif" '
        f'font-size="11" fill="{FAINT}">seek</text>',
        f'<text x="{ox + cw + cw / 2}" y="88" text-anchor="middle" font-family="Helvetica Neue,Arial,sans-serif" '
        f'font-size="11" fill="{FAINT}">no seek</text>',
        f'<text x="36" y="{oy + ch}" text-anchor="middle" transform="rotate(-90 36 {oy + ch})" '
        f'font-family="Helvetica Neue,Arial,sans-serif" font-size="12" font-weight="700" fill="{MUTED}">intent</text>',
        f'<text x="100" y="{oy + ch / 2 + 4}" text-anchor="end" '
        f'font-family="Helvetica Neue,Arial,sans-serif" font-size="11" fill="{FAINT}">yes</text>',
        f'<text x="100" y="{oy + ch + ch / 2 + 4}" text-anchor="end" '
        f'font-family="Helvetica Neue,Arial,sans-serif" font-size="11" fill="{FAINT}">no</text>',
    ]

    cells = [
        (0, 0, yy, "contemplated\n& sought", RED_SOFT, INK),
        (1, 0, yn, "weighed it,\nstayed honest", GREEN_SOFT, GREEN),
        (0, 1, ny, "sought without\nverbalized intent", "#f0e6d8", "#7a5a3a"),
        (1, 1, nn, "neither", GRAY, FAINT),
    ]
    for col, row, val, caption, fill, tc in cells:
        x = ox + col * cw
        y = oy + row * ch
        parts.append(
            f'<rect x="{x + 4}" y="{y + 4}" width="{cw - 8}" height="{ch - 8}" rx="6" fill="{fill}"/>'
        )
        parts.append(
            f'<text x="{x + cw / 2}" y="{y + 48}" text-anchor="middle" '
            f'font-family="SF Mono,Menlo,monospace" font-size="28" font-weight="700" fill="{tc}">{val}</text>'
        )
        parts.append(
            f'<text x="{x + cw / 2}" y="{y + 70}" text-anchor="middle" '
            f'font-family="Helvetica Neue,Arial,sans-serif" font-size="11" fill="{MUTED}">'
            f'{100 * val / n:.0f}% of judged</text>'
        )
        for j, line in enumerate(caption.split("\n")):
            parts.append(
                f'<text x="{x + cw / 2}" y="{y + 94 + j * 14}" text-anchor="middle" '
                f'font-family="Helvetica Neue,Arial,sans-serif" font-size="11" fill="{INK}">{line}</text>'
            )

    parts.append(
        f'<text x="28" y="{H - 28}" font-family="Helvetica Neue,Arial,sans-serif" font-size="11" '
        f'fill="{MUTED}">The interesting mass is <tspan font-weight="700" fill="{GREEN}">intent-yes / behavior-no</tspan> '
        f'({yn}) — exploration that did not become exploitation. '
        f'Among seekers, {ny}/{yy + ny} lack verbalized contemplation '
        f'(thin CoT more often than proven stealth).</text>'
    )
    parts.append(
        f'<text x="28" y="{H - 10}" font-family="Helvetica Neue,Arial,sans-serif" font-size="10" '
        f'fill="{FAINT}">declined_after_notice={counts["declined"]} · not a present-only freeze yet</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ad = render_ad_panel()
    (OUT / "06_ad_corp_vs_enterprise.svg").write_text(ad)
    # also replace sketch 03 with multi-model callout pointing to 06? keep 03 as DS-only classic
    counts = load_intent_counts()
    intent = render_intent_2x2(counts)
    (OUT / "07_intent_behavior.svg").write_text(intent)
    print(f"wrote {OUT / '06_ad_corp_vs_enterprise.svg'}")
    print(f"wrote {OUT / '07_intent_behavior.svg'}")
    print("intent counts:", counts)


if __name__ == "__main__":
    main()
