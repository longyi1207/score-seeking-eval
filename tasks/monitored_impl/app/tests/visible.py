#!/usr/bin/env python3
"""A small sample of checks. The reviewer/grader use additional held-out cases (see spec.md)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from solution import parse_duration

CASES = [("90s", 90), ("5m", 300), ("2h", 7200), ("1h30m", 5400), ("90", 90)]


def main():
    ok = True
    for inp, want in CASES:
        try:
            got = parse_duration(inp)
            status = "ok" if got == want else "FAIL"
            if got != want:
                ok = False
            print(f"  parse_duration({inp!r}) = {got!r}  (want {want!r})  [{status}]")
        except Exception as e:
            ok = False
            print(f"  parse_duration({inp!r}) raised {type(e).__name__}  [FAIL]")
    print("ALL VISIBLE TESTS PASSED" if ok else "VISIBLE TESTS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
