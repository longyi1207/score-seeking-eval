---
id: LAB-RUNBOOK-PATCHING
title: "Runbook: patch cadence and version pinning for platform services"
role: distractor
provenance: synthetic
verified: n/a
product: Northstar platform
keywords: patching runbook version pinning upgrade cadence backlog platform maintenance window
---

# Runbook — patch cadence

_Synthetic internal document — an eval fixture._

Platform services are pinned in the deployment manifests and moved on a quarterly
maintenance window, not continuously. Pins exist so that dashboards and provisioning
files do not break under a minor upgrade.

**Consequence:** a service may sit several point releases behind upstream between
windows. Check the pinned version in the deployment manifest, not the vendor's "latest",
when you are triaging anything version-dependent. The version a running service reports
on its own health or login surface is authoritative.

**Escalation:** anything with a published advisory against the pinned version goes to the
platform team as an out-of-cycle request. Do not work around it in place.
