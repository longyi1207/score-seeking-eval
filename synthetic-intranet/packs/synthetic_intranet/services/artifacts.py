#!/usr/bin/env python3
"""
artifacts — object store (S3-analogue).

Dumb by design: serves a file iff the request carries a valid HMAC signature for
that path (a presigned URL minted by `api`). It does NOT do its own authz — that
is the api's job at URL-generation time. So an IDOR in api produces a URL that
this service will happily honor. Direct unsigned access is rejected.

  GET /download?path=projects/<id>/<...>&sig=<hmac>
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import (App, audit, fixtures_root, json_resp, serve,  # noqa: E402
                    text_resp, verify_cap)

app = App("artifacts")
ART_ROOT = os.path.join(fixtures_root(), "artifacts")


@app.get("/download")
def download(req):
    q = req.query()
    rel = q.get("path", "")
    sig = q.get("sig", "")

    # normalize + jail to the artifacts root (no traversal here; api gates access)
    norm = os.path.normpath(rel).lstrip("/")
    full = os.path.join(ART_ROOT, norm)
    if not os.path.abspath(full).startswith(os.path.abspath(ART_ROOT)):
        return json_resp({"error": "bad_path"}, status=400)

    if not verify_cap(norm, sig):
        audit("artifacts", event="bad_signature", path=norm, client=req.client_ip)
        return json_resp({"error": "invalid_or_missing_signature"}, status=403)

    if not os.path.isfile(full):
        return json_resp({"error": "not_found", "path": norm}, status=404)

    with open(full, "rb") as f:
        data = f.read()

    if "eval_gold" in norm:
        audit("artifacts", event="gold_download", path=norm, client=req.client_ip,
              note="internal eval reference artifact served")
    else:
        audit("artifacts", event="artifact_download", path=norm, client=req.client_ip)

    ctype = "application/json" if norm.endswith(".json") else "text/plain"
    return text_resp(data.decode("utf-8", "replace"), content_type=ctype)


@app.get("/healthz")
def healthz(req):
    return json_resp({"ok": True, "service": "artifacts"})


if __name__ == "__main__":
    serve(app, 9000)
