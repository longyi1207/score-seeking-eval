#!/usr/bin/env python3
"""Refresh docs/FILL_STATUS.md from runs/ — called by the fill monitor."""
from __future__ import annotations
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
OUT = ROOT / "docs" / "FILL_STATUS.md"
MKS = ["deepseek", "kimi", "gpt-4o", "gpt-5.4", "claude"]
LABEL = {
    "deepseek": "DeepSeek-V4-Pro",
    "kimi": "Kimi-K2.6",
    "gpt-4o": "gpt-4o",
    "gpt-5.4": "gpt-5.4",
    "claude": "Claude Sonnet 4.5",
}

def count(pat: str) -> int:
    return len(list(RUNS.glob(pat)))

def chess_row(mk: str) -> str:
    files = sorted(RUNS.glob(f"chess_{mk}_hard_none_r*.json"))
    labs, modes = [], []
    for p in files:
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        if (d.get("verdict") or {}).get("label") == "infra_error":
            continue
        labs.append((d.get("verdict") or {}).get("label") or d.get("label"))
        modes.append(
            (d.get("propensity") or {}).get("cheat_mode")
            or (d.get("verdict") or {}).get("channel")
        )
    n = len(labs)
    seek = sum(1 for l in labs if l in ("score_seek_success", "score_seek"))
    mode = Counter(m for m in modes if m and m != "none").most_common(1)
    mode_s = mode[0][0] if mode else ("fail" if seek == 0 else "seek")
    return f"| {LABEL[mk]} | {seek}/{n or 5} | `{mode_s}` |"

chess = {mk: count(f"chess_{mk}_hard_none_r*.json") for mk in MKS}
lean = {mk: count(f"lean_{mk}_fastrev_none_r*.json") for mk in MKS}
web = {mk: count(f"web_{mk}_d1_none_r*.json") for mk in MKS}
ad = sorted((RUNS / "ad_panel").glob("*.json")) if (RUNS / "ad_panel").exists() else []

lines = [
    "# Fill status (auto)",
    "",
    f"_Updated {datetime.now().strftime('%Y-%m-%d %H:%M')}_",
    "",
    "Live while chess / lean / web + AD-corp fills run. Hero figure:",
    "[`figures/01_task_heatmap.svg`](figures/01_task_heatmap.svg) "
    "(row labels: DeepSeek-V4-Pro · Kimi-K2.6 · gpt-4o · gpt-5.4 · Claude Sonnet 4.5).",
    "",
    "## Container panel (target n=5 / model)",
    "",
    "| Task | DeepSeek-V4-Pro | Kimi-K2.6 | gpt-4o | gpt-5.4 | Claude Sonnet 4.5 |",
    "|---|---|---|---|---|---|",
    f"| chess hard | {chess['deepseek']}/5 | {chess['kimi']}/5 | {chess['gpt-4o']}/5 | {chess['gpt-5.4']}/5 | {chess['claude']}/5 |",
    f"| lean fastrev | {lean['deepseek']}/5 | {lean['kimi']}/5 | {lean['gpt-4o']}/5 | {lean['gpt-5.4']}/5 | {lean['claude']}/5 |",
    f"| web d1 | {web['deepseek']}/5 | {web['kimi']}/5 | {web['gpt-4o']}/5 | {web['gpt-5.4']}/5 | {web['claude']}/5 |",
    "",
    f"## AD-corp (kimi / gpt-5.4 / claude × n=5) — {len(ad)}/15",
    "",
]
for p in ad:
    try:
        d = json.loads(p.read_text())
        lab = (d.get("verdict") or {}).get("label") or d.get("label")
        lines.append(f"- `{p.name}`: **{lab}** (steps={d.get('steps')})")
    except Exception as e:
        lines.append(f"- `{p.name}`: unreadable ({e})")

lines += ["", "## Chess hard — landed", "", "| Model | Seek | Dominant mode |", "|---|---|---|"]
lines += [chess_row(mk) for mk in MKS]
lines += [
    "",
    "Full narrative: [`RESULTS.md`](RESULTS.md) §5.",
]
OUT.write_text("\n".join(lines) + "\n")
print(f"wrote {OUT}")
