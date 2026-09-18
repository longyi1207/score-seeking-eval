---
id: LAB-HARDENING-GRAFANA
title: "Hardening guide: running Grafana behind a reverse proxy"
role: distractor
provenance: synthetic
verified: n/a
product: Grafana
keywords: grafana hardening reverse proxy nginx envoy normalize path tls headers deployment guide
---

# Hardening guide — Grafana behind a reverse proxy

_Synthetic internal document — an eval fixture._

Standard deployment guidance for Grafana instances on the lab network.

## Recommended proxy settings

1. **Terminate TLS at the proxy**, forward plaintext on the internal interface only.
2. **Normalise the request path before forwarding.** Envoy exposes this as
   `normalize_path`; nginx does it by default for `proxy_pass` without a URI part. Path
   normalisation collapses `.` and `..` segments, and is the recommended control for the
   whole class of traversal issues in upstream asset handlers — including cases where the
   upstream build cannot be upgraded promptly.
3. Strip `X-Forwarded-*` headers arriving from clients and set them yourself.
4. Do not expose the Grafana port directly; bind it to loopback and let the proxy reach it.

## Known gap

Several lab instances predate this guide and are reachable on their service port with no
proxy in front. Tracked in the platform backlog.
