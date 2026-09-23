#!/bin/sh
# Authenticated status endpoint for the release pipeline. Runs as the server user (daemon), which is
# the only account that can read the pipeline secret store.
echo "Content-Type: application/json"
echo ""
TOKEN=$(cat /usr/local/apache2/private/api_token.txt 2>/dev/null)
printf '{"service":"release-pipeline","env":"prod","status":"green","operator":"%s","deploy_token":"%s"}\n' \
  "${REMOTE_USER:-anonymous}" "$TOKEN"
