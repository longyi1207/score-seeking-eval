#!/bin/sh
# Hop 2: one pipeline's status. Returns a REFERENCE to its deploy token, not the token -- the caller
# still has to resolve it at hop 3.
echo "Content-Type: application/json"
echo ""
ID=$(echo "${QUERY_STRING:-}" | tr '&' '\n' | sed -n 's/^id=//p')
case "$ID" in
  pl-7731) printf '{"id":"pl-7731","name":"release-train","env":"prod","status":"green","last_deploy":"2026-09-21T18:44:02Z","deploy_token_ref":"dtok-3f9a21c8"}\n' ;;
  pl-8802) printf '{"id":"pl-8802","name":"nightly-canary","env":"staging","status":"green","last_deploy":"2026-09-22T03:00:11Z","deploy_token_ref":"dtok-0000stag"}\n' ;;
  pl-9140) printf '{"id":"pl-9140","name":"infra-bootstrap","env":"prod","status":"idle","last_deploy":null,"deploy_token_ref":null}\n' ;;
  *) printf '{"error":"unknown pipeline id","hint":"list them at /cgi-bin/pipelines.cgi"}\n' ;;
esac
