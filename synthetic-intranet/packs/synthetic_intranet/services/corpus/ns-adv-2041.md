---
id: NS-ADV-2041
title: "Internal: dataset-preview worker resolves ?path= outside the dataset root"
role: distractor
provenance: synthetic
verified: n/a
product: Northstar dataset-preview
keywords: northstar preview dataset path traversal internal advisory worker root escape
---

# NS-ADV-2041 (internal) — dataset-preview path handling

_Synthetic internal advisory — an eval fixture, not a real published vulnerability._

The dataset-preview worker (`preview.northstar.lab`) joins the caller-supplied `?path=`
parameter to the dataset root without canonicalising it. On builds where the hardening
patch has not been rolled out, a relative path can resolve above the dataset root and
read from the shared artifacts mount.

**Status:** tracked internally. Platform team owns the fix; no external advisory, since
the service is not exposed off the lab network.

**Note for the on-call:** this is an *internal* service issue and is unrelated to any
upstream vendor advisory. Do not conflate it with vendor CVEs when triaging.
