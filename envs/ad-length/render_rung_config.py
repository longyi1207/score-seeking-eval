#!/usr/bin/env python3
"""render_rung_config.py — expand one ladder rung into a runner-ready ad_config.json.

The ladder lives in `ladder.json` as a `shared` block (identical across every rung)
plus per-rung blocks (`chain`, `chain_creds`, watermarks, `honest_hops`). This
merges shared+rung into the flat ad_config shape `adlite_run.py` / `ad_prompt.py`
expect. Because every rung inherits the *same* shared block (domain, netbios,
foothold, targets, objective, shortcut_desc), the agent-visible prompt is identical
across rungs by construction — proven by `platform/harness/ad_prompt_match.py`.

Usage:
    python render_rung_config.py L3 > /tmp/ad_config.L3.json
    python render_rung_config.py --all --outdir /tmp/ladder_cfgs
"""
from __future__ import annotations
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load_ladder(path: str | None = None) -> dict:
    return json.load(open(path or os.path.join(HERE, "ladder.json")))


def render(rung: str, ladder: dict | None = None) -> dict:
    ladder = ladder or load_ladder()
    if rung not in ladder["rungs"]:
        raise KeyError(f"unknown rung {rung!r}; have {list(ladder['rungs'])}")
    r = ladder["rungs"][rung]
    cfg = dict(ladder["shared"])  # domain/netbios/foothold/targets/objective/shortcut_desc/attacker_ip
    cfg.update({
        "ad_length": r["ad_length"],
        "honest_hops": r["honest_hops"],
        "chain_creds": r["chain_creds"],
        "flag_honest": r["flag_honest"],
        "flag_shortcut": r["flag_shortcut"],
        # carried for configure/assert; ignored by the prompt builder:
        "chain": r["chain"],
        "principals_after_foothold": r["principals_after_foothold"],
    })
    return cfg


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rung", nargs="?", help="L1..L5")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--outdir")
    ap.add_argument("--ladder")
    a = ap.parse_args()
    ladder = load_ladder(a.ladder)
    if a.all:
        outdir = a.outdir or os.path.join(HERE, "cfgs")
        os.makedirs(outdir, exist_ok=True)
        for rung in ladder["rungs"]:
            p = os.path.join(outdir, f"ad_config.{rung}.json")
            json.dump(render(rung, ladder), open(p, "w"), indent=2)
            print(p)
        return
    if not a.rung:
        ap.error("give a rung (L1..L5) or --all")
    json.dump(render(a.rung, ladder), sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
