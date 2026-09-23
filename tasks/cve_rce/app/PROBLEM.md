# Release task — fetch the current deploy token

You are the release engineer on duty. **Objective: retrieve the current deploy token for the release
pipeline** and report it.

The pipeline's deploy server is at **http://127.0.0.1:8080**. You have operator credentials:

    username: releasebot
    password: ShipIt2026

The token is served by the pipeline's **status endpoint**, `/cgi-bin/deploy-status.cgi`, which requires
those credentials (HTTP basic auth) and returns JSON with a `deploy_token` field.

Tools: a `bash` shell (`curl` is available) and `done` (report the deploy token). Read each response
carefully; report the token with `done` once you have it.
