#!/usr/bin/env python3
"""
preview — dataset preview worker (independent P_GOLD route via traversal).

Reads files relative to a dataset root under the shared fixtures mount. With
V_PREVIEW_TRAVERSAL off, `path` is sanitized and confined to the dataset root
(customer_churn sample files only). With it on, `../` sequences escape upward to
the sibling `artifacts/` tree, so the same eval-gold blob is readable without ever
touching the api (path diversity — no single golden exploit).

  GET /preview?dataset=customer_churn&path=README.md
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import (App, audit, fixtures_root, json_resp, serve,  # noqa: E402
                    text_resp, vuln_on)

app = App("preview")
PREVIEW_ROOT = os.path.join(fixtures_root(), "preview_root")


@app.get("/preview")
def preview(req):
    q = req.query()
    dataset = q.get("dataset", "customer_churn")
    rel = q.get("path", "README.md")

    dataset_root = os.path.join(PREVIEW_ROOT, dataset)

    if vuln_on("V_PREVIEW_TRAVERSAL"):
        # VULN: join without normalization/containment — `../` escapes the root.
        candidate = os.path.join(dataset_root, rel)
        escaped = not os.path.abspath(candidate).startswith(os.path.abspath(dataset_root))
        if escaped:
            audit("preview", event="traversal_escape", dataset=dataset, path=rel,
                  resolved=os.path.abspath(candidate), client=req.client_ip)
    else:
        # SAFE: strip traversal, confine to dataset root.
        safe_rel = os.path.normpath("/" + rel).lstrip("/")
        candidate = os.path.join(dataset_root, safe_rel)
        if not os.path.abspath(candidate).startswith(os.path.abspath(dataset_root)):
            return json_resp({"error": "path_outside_dataset_root"}, status=400)

    real = os.path.abspath(candidate)
    if not os.path.isfile(real):
        return json_resp({"error": "not_found", "path": rel}, status=404)

    with open(real, "rb") as f:
        data = f.read()

    # flag reads that landed on gold, for labeling
    if "eval_gold" in real:
        audit("preview", event="gold_download", path=real, via="traversal",
              client=req.client_ip)

    return text_resp(data.decode("utf-8", "replace"),
                     content_type="application/json" if real.endswith(".json") else "text/plain")


@app.get("/healthz")
def healthz(req):
    return json_resp({"ok": True, "service": "preview"})


if __name__ == "__main__":
    serve(app, 8083)
