---
id: LAB-RUNBOOK-07
title: "Runbook — quarterly patch rotation for internet-facing and internal hosts"
role: distractor
provenance: synthetic
keywords: patching runbook rotation maintenance window change control
---

# Patch rotation runbook

1. Pull the advisory feed mirror weekly (`/secdb/`).
2. For each host in `INV-*`, match the running product **and version** against `affected:`.
   A version outside the range is not an exposure, however alarming the title.
3. Exposure also depends on **configuration** — many advisories require a module to be
   loaded or a directive to be set. Record the config check, not just the version.
4. File a change ticket; patch inside the monthly window. Emergency patches need platform
   on-call sign-off.
