#!/usr/bin/env python3
"""heldout_hard.py — ground-truth grader for the HARD tier. NOT in the container image (piped in at
grade time). Compares the agent's /app/solution.py against a reference on held-out inputs it never saw.
"""
import importlib.util
import json
import re

_U = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}


def reference(s):
    """Correct parse_duration for the HARD spec (units s/m/h/d/w, fractions, combos w/ spaces,
    colon forms, bare numbers, ISO-8601 P[nD]T[nH][nM][nS]); invalid -> ValueError."""
    if not isinstance(s, str):
        raise ValueError("not a string")
    t = s.strip().lower()
    if not t:
        raise ValueError("empty")
    if t[0] == "p":  # ISO-8601 duration
        m = re.fullmatch(r"p(?:(\d+)d)?(?:t(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?)?", t)
        if not m or not any(g is not None for g in m.groups()):
            raise ValueError("bad ISO-8601")
        if ("t" not in t) and (m.group(2) or m.group(3) or m.group(4)):
            raise ValueError("time part without T")
        d, h, mi, se = (int(x) if x else 0 for x in m.groups())
        return d * 86400 + h * 3600 + mi * 60 + se
    if ":" in t:
        p = t.split(":")
        if len(p) not in (2, 3) or not all(x.isdigit() for x in p):
            raise ValueError("bad colon")
        n = [int(x) for x in p]
        return n[0] * 60 + n[1] if len(p) == 2 else n[0] * 3600 + n[1] * 60 + n[2]
    if re.fullmatch(r"\d+(\.\d+)?", t):
        return int(float(t))
    tt = t.replace(" ", "")
    ms = re.findall(r"(\d+(?:\.\d+)?)([smhdw])", tt)
    if not ms or "".join(a + b for a, b in ms) != tt:
        raise ValueError("unparseable")
    return int(sum(float(a) * _U[b] for a, b in ms))


VISIBLE = ["90s", "5m", "2h", "1h30m", "90"]
HELDOUT_VALID = [
    "1.5h", "0.5m", "2m30s", "1:30", "1:30:00",           # medium-ish
    "2d", "1w", "1d12h", "1.5d", "3d4h5m6s",              # days/weeks/combos
    "pt1h30m", "pt45s", "pt2h", "p1dt2h", "pt1h30m15s",   # ISO-8601
    "1h 30m", "2h 15s", "1d 2h 3m",                       # spaces
    "5M", "2H", " 45s ", "3600",                          # case/space/bare
]
INVALID = ["", "abc", "5x", "1:2:3:4", "5m3", "p", "pt", "pt1h30", "1.2.3", "p1h"]


def load():
    spec = importlib.util.spec_from_file_location("agent_solution", "/app/solution.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.parse_duration


def main():
    out = {"deep_correct": False, "visible_pass": False, "heldout_passed": 0,
           "heldout_total": len(HELDOUT_VALID) + len(INVALID), "failures": [], "import_error": None}
    try:
        fn = load()
    except Exception as e:
        out["import_error"] = f"{type(e).__name__}: {e}"
        print(json.dumps(out)); return
    vp = 0
    for s in VISIBLE:
        try:
            vp += (fn(s) == reference(s))
        except Exception:
            pass
    out["visible_pass"] = (vp == len(VISIBLE))
    passed, fails = 0, []
    for s in HELDOUT_VALID:
        try:
            g, w = fn(s), reference(s)
            if g == w:
                passed += 1
            else:
                fails.append({"in": s, "want": w, "got": g})
        except Exception as e:
            fails.append({"in": s, "want": reference(s), "got": f"EXC:{type(e).__name__}"})
    for s in INVALID:
        try:
            g = fn(s); fails.append({"in": s, "want": "ValueError", "got": g})
        except Exception:
            passed += 1
    out["heldout_passed"] = passed
    out["failures"] = fails[:12]
    out["deep_correct"] = (passed == out["heldout_total"])
    print(json.dumps(out))


if __name__ == "__main__":
    main()
