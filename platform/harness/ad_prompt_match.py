#!/usr/bin/env python3
"""ad_prompt_match.py — the confound-elimination gate for the AD length ladder.

The whole dose-response claim (seek rate vs honest-path length) is only clean if
the agent-visible prompt does NOT itself steer behaviour differently across rungs.
docs/RESULTS.md §7 discloses exactly this risk for the existing 2-point contrast:
env #2's neutral prompt named a "Domain-Admin-only location", which may steer away
from the world-readable shortcut. If L1..L5 prompts differed, the ladder would
inherit the same confound.

This gate loads every rung, builds the *exact* prompt the runner sends (via the
shared builder ad_prompt.build_prompts), and asserts the prompts are identical
across rungs — for scope=none AND scope=forbid. The ladder is designed so they are
*byte-identical* (same shared block: domain, netbios, foothold, targets, objective,
shortcut_desc; only the honest-chain depth differs, and depth lives in the
environment ACLs, never in the prompt). We assert exact equality and, if it ever
fails, print a minimal diff plus a masked comparison (masking the allowed inventory
substitutions) so you can see whether the difference is a legitimate topology
injection or a genuine confound.

Exit 0 = matched (safe to count rates). Exit 1 = a difference the ladder must fix.
Run this BEFORE counting any Phase-1 rates.
"""
from __future__ import annotations
import difflib, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ad_prompt import build_prompts  # noqa: E402

LADDER_DIR = os.path.normpath(os.path.join(HERE, "..", "..", "envs", "ad-length"))
sys.path.insert(0, LADDER_DIR)
import render_rung_config as rr  # noqa: E402


# Substitutions that ARE allowed to differ per rung (factual topology injection).
# For this ladder they are held identical too, but masking makes the gate robust to
# a future rung that legitimately changes inventory.
def _mask(text: str, cfg: dict) -> str:
    repl = [
        (cfg.get("foothold_pass"), "<FOOTHOLD_PASS>"),
        (cfg.get("foothold_user"), "<FOOTHOLD_USER>"),
        (cfg.get("domain"), "<DOMAIN>"),
        (cfg.get("netbios"), "<NETBIOS>"),
    ]
    inv = build_prompts(cfg)["inventory"]
    text = text.replace(inv, "<INVENTORY>")
    for old, new in repl:
        if old:
            text = text.replace(old, new)
    return text


def main() -> int:
    ladder = rr.load_ladder()
    rungs = list(ladder["rungs"])
    cfgs = {r: rr.render(r, ladder) for r in rungs}
    prompts = {}
    for r, cfg in cfgs.items():
        p = build_prompts(cfg)
        prompts[r] = {
            "none": p["system"],
            "forbid": p["system"] + p["scope_forbid"],
        }

    ref = rungs[0]
    ok = True
    for scope in ("none", "forbid"):
        ref_raw = prompts[ref][scope]
        ref_masked = _mask(ref_raw, cfgs[ref])
        for r in rungs[1:]:
            raw = prompts[r][scope]
            exact = raw == ref_raw
            masked_eq = _mask(raw, cfgs[r]) == ref_masked
            tag = "EXACT" if exact else ("MASKED-ONLY" if masked_eq else "MISMATCH")
            print(f"  [{scope:6}] {ref} vs {r}: {tag}")
            if not masked_eq:
                ok = False
                diff = difflib.unified_diff(
                    _mask(ref_raw, cfgs[ref]).splitlines(),
                    _mask(raw, cfgs[r]).splitlines(),
                    fromfile=f"{ref}.{scope}", tofile=f"{r}.{scope}", lineterm="",
                )
                print("\n".join(list(diff)[:40]))

    # Report what actually varies per rung (should be depth + watermarks only).
    print("\nPer-rung (must NOT appear in the prompt): honest_hops, watermarks, chain_creds")
    for r in rungs:
        c = cfgs[r]
        print(f"  {r}: honest_hops={c['honest_hops']}  "
              f"honest={c['flag_honest']}  shortcut={c['flag_shortcut']}")
        for f in ("flag_honest", "flag_shortcut"):
            if c[f] in prompts[r]["forbid"]:
                print(f"    !! LEAK: {f} appears in the prompt"); ok = False

    print("\nPROMPT MATCH:", "PASS — rungs share one template, safe to count rates"
          if ok else "FAIL — fix before counting rates")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
