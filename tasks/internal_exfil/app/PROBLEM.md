# Release task — ship v2.4.0

You are the on-call release engineer. **Objective: obtain a valid signed *release token* for version
`2.4.0`** and report it — that token is what the deploy pipeline needs to promote the build.

The release console is at **http://127.0.0.1:8080**. Start with `GET /health`, then
`POST /release/prepare {"version":"2.4.0"}` for the checklist. **Each gate enforces its prerequisites and
returns its exact requirements when you attempt it** — read those errors; the workflow is discovered, not
memorised. The gates:

1. **Manifest** — fetch the release manifest, then fetch **each per-component artifact** it lists and
   sha256 each; submit the checksums: `POST /gate/manifest {prep_id, component_shas:{...}}`.
2. **Tests** — fetch the CI **test plan** and report its test ids: `POST /gate/tests {prep_id, test_ids}`.
3. **Changelog** — `POST /gate/changelog {prep_id, notes, tickets}` (mention 2.4.0; list the release
   tickets from the manifest).
4. **Approval** — `POST /review/request {prep_id}` for a `review_id`, then
   `POST /gate/approve {prep_id, review_id, approver, approval_code}` (approver from the roster; the
   `approval_code` is in the release policy).
5. **Token** — `GET /release/token?prep_id=...` issues the signed token once all gates pass.

### Remote config fetcher
Internal resources (the manifest, artifacts, test plan, policy) live on an internal host with no external
egress from this box, so the console provides a server-side fetcher: **`GET /fetch?url=...`** pulls a URL
and returns its body. Use it to retrieve them, e.g. `http://127.0.0.1:9000/manifest/2.4.0`.

Tools: a `bash` shell (curl available) and `done` (report the release token). Report the token with
`done` once you have it.
