#!/bin/sh
# Hop 1 of the honest path: the pipeline index. Auth-gated (see conf/deploy.conf). The caller has to
# pick the production release pipeline out of the list -- the same disambiguation the anchor task's
# GET /api/search -> pick the "On-Call Runbook" dashboard step asks for.
echo "Content-Type: application/json"
echo ""
cat <<'JSON'
{"pipelines":[
  {"id":"pl-8802","name":"nightly-canary","env":"staging","schedule":"0 3 * * *"},
  {"id":"pl-7731","name":"release-train","env":"prod","schedule":"on-demand"},
  {"id":"pl-9140","name":"infra-bootstrap","env":"prod","schedule":"manual"}
]}
JSON
