#!/usr/bin/env python3
"""Keep judging until every runs/*.json with a transcript has intent_judge.

More durable than bash+limit batches: one process, per-file try/except, heartbeat log.
"""
from __future__ import annotations

import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "platform" / "harness"))
sys.path.insert(0, str(ROOT / "scripts"))

from cot_contemplate import (  # noqa: E402
    intent_behavior_cell,
    judge_run,
    load_dotenv_files,
)
import judge_cot_contemplate as jcc  # noqa: E402

LOG = ROOT / "runs" / "logs" / "cot_contemplate_gpt54.log"
ERR = ROOT / "runs" / "logs" / "cot_contemplate_gpt54.err"
HEART = ROOT / "runs" / "logs" / "cot_contemplate_heartbeat.txt"
OUT_JSONL = jcc.OUT_JSONL
JUDGE_MODEL = "gpt-5.4"
SLEEP = 0.05


def log(msg: str) -> None:
    line = f"{msg}\n"
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as fh:
        fh.write(line)
    print(msg, flush=True)


def heartbeat(done: int, total: int, last: str) -> None:
    HEART.write_text(
        f"ts={datetime.now(timezone.utc).isoformat()} done={done}/{total} last={last}\n"
    )


def pending_paths() -> list[Path]:
    out: list[Path] = []
    for f in sorted((ROOT / "runs").glob("*.json")):
        if f.name.endswith(".events.json") or f.name in ("ad_corp_tf_output.json",):
            continue
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        tr = d.get("transcript")
        if not (isinstance(tr, list) and tr):
            continue
        ij = d.get("intent_judge")
        if isinstance(ij, dict) and not ij.get("dry_run"):
            continue
        out.append(f)
    return out


def count_done() -> tuple[int, int]:
    n = d = 0
    for f in (ROOT / "runs").glob("*.json"):
        try:
            x = json.loads(f.read_text())
        except Exception:
            continue
        if isinstance(x.get("transcript"), list) and x["transcript"]:
            n += 1
            ij = x.get("intent_judge")
            if isinstance(ij, dict) and not ij.get("dry_run"):
                d += 1
    return d, n


def append_jsonl(row: dict) -> None:
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    # rewrite full file periodically is heavy; append + dedupe at end via jcc.write_md
    with OUT_JSONL.open("a") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    load_dotenv_files()
    log(f"WORKER_START {datetime.now(timezone.utc).isoformat()} model={JUDGE_MODEL}")
    consecutive_fail = 0
    while True:
        pending = pending_paths()
        done, total = count_done()
        if not pending:
            log(f"WORKER_DONE {done}/{total} {datetime.now(timezone.utc).isoformat()}")
            # rebuild summary from all intent_judge
            rows = []
            for f in sorted((ROOT / "runs").glob("*.json")):
                try:
                    d = json.loads(f.read_text())
                except Exception:
                    continue
                ij = d.get("intent_judge")
                if not (isinstance(ij, dict) and not ij.get("dry_run")):
                    continue
                rows.append({
                    "file": f.name,
                    "model_key": jcc.model_key(d, f.name),
                    **ij,
                    "intent_behavior_cell": intent_behavior_cell(ij),
                })
            with OUT_JSONL.open("w") as fh:
                for r in rows:
                    fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            jcc.write_md(rows)
            log(f"WORKER_SUMMARY rows={len(rows)} -> {jcc.OUT_MD}")
            heartbeat(done, total, "DONE")
            return 0

        path = pending[0]
        try:
            d = json.loads(path.read_text())
            intent = judge_run(d, path, judge_model=JUDGE_MODEL, dry_run=False)
            d["intent_judge"] = intent
            path.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
            row = {
                "file": path.name,
                "model_key": jcc.model_key(d, path.name),
                **intent,
                "intent_behavior_cell": intent_behavior_cell(intent),
            }
            append_jsonl(row)
            done, total = count_done()
            msg = (
                f"[{done}/{total}] {path.name} contemplated={intent.get('contemplated')} "
                f"status={intent.get('intent_status')} cell={row['intent_behavior_cell']}"
            )
            log(msg)
            heartbeat(done, total, path.name)
            consecutive_fail = 0
            time.sleep(SLEEP)
        except Exception as e:
            consecutive_fail += 1
            err = f"ERR {path.name}: {type(e).__name__}: {e}"
            log(err)
            with ERR.open("a") as fh:
                fh.write(err + "\n")
                fh.write(traceback.format_exc() + "\n")
            heartbeat(done, total, f"ERR:{path.name}")
            # brief backoff; skip this file temporarily by touching a marker? better: sleep and retry later
            # move past poison files after 3 fails on same: write a failed stub
            if consecutive_fail >= 3:
                stub = {
                    "schema_version": 1,
                    "contemplated": False,
                    "declined_after_notice": False,
                    "intent_status": "none",
                    "evidence_quotes": [],
                    "rationale": f"judge_failed: {type(e).__name__}: {e}",
                    "shortcut_kinds": [],
                    "reasoning_available": False,
                    "judge_model": JUDGE_MODEL,
                    "judge_error": True,
                }
                try:
                    d = json.loads(path.read_text())
                    d["intent_judge"] = stub
                    path.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
                    log(f"STUB_FAIL {path.name}")
                    consecutive_fail = 0
                except Exception:
                    pass
            time.sleep(min(30, 2 ** consecutive_fail))


if __name__ == "__main__":
    raise SystemExit(main())
