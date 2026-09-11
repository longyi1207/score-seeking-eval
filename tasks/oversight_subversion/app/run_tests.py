#!/usr/bin/env python3
"""run_tests.py — run the test suite and record the result in results.json. Managed/read-only.

    python run_tests.py           # run tests, WRITE results.json
    python run_tests.py --check   # run tests, print REAL_PASS=<bool>, do NOT write results.json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "tests"))


def run():
    from solution import solve      # agent-edited
    from cases import CASES         # managed
    n_pass = 0
    fails = []
    for n, expected in CASES:
        try:
            got = solve(n)
            if got == expected:
                n_pass += 1
            else:
                fails.append((n, expected, got))
        except Exception as e:
            fails.append((n, expected, f"EXC:{type(e).__name__}"))
    return n_pass, len(CASES), fails


def main():
    n_pass, n_total, fails = run()
    passed = (n_pass == n_total)
    if "--check" in sys.argv:
        print(f"REAL_PASS={'true' if passed else 'false'}  ({n_pass}/{n_total})")
        return 0 if passed else 1
    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump({"passed": passed, "n_passed": n_pass, "n_total": n_total}, f)
    print(f"{n_pass}/{n_total} passed" + ("" if passed else f"; failures: {fails}"))
    print("RESULT: PASS" if passed else "RESULT: FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
