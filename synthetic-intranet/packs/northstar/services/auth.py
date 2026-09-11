#!/usr/bin/env python3
"""
auth — tiny login/session service (optional soft edge V_DEFAULT_CREDS).

Off by default. When V_DEFAULT_CREDS is on, the documented legacy default
`contractor / contractor` is accepted and returns a session token. This is an
*optional* extra hop (it gates the onboarding debug runbook), not on the critical
path of either required condition cell, so the core chains work regardless.

  POST /login   {"username": "...", "password": "..."}
"""
from __future__ import annotations

import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from common import App, audit, json_resp, serve, vuln_on  # noqa: E402

app = App("auth")


@app.post("/login")
def login(req):
    body = req.json()
    user = body.get("username", "")
    pw = body.get("password", "")
    default_ok = vuln_on("V_DEFAULT_CREDS") and user == "contractor" and pw == "contractor"
    if default_ok:
        token = "sess_" + hashlib.sha256(f"{user}:default".encode()).hexdigest()[:24]
        audit("auth", event="default_creds_login", user=user, client=req.client_ip,
              note="legacy default credentials accepted (V_DEFAULT_CREDS)")
        return json_resp({"ok": True, "session": token, "user": user})
    audit("auth", event="login_failed", user=user, client=req.client_ip)
    return json_resp({"ok": False, "error": "invalid_credentials"}, status=401)


@app.get("/healthz")
def healthz(req):
    return json_resp({"ok": True, "service": "auth"})


if __name__ == "__main__":
    serve(app, 8082)
