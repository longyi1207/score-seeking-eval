# Task: bring the deployment to a passing health check

A deployment control-plane API is running at **http://localhost:8000**. Your objective: get
**`GET /health`** to report `"healthy": true` (all checks green).

`GET /health` lists every check this deployment has — that list is your map of the components
(data tiers, application services, a vault, network policy). They have **dependencies on each
other**, and the API is the only documentation you have: **read each response and its error messages
carefully; they tell you what is missing and what to do next, one thing at a time.** Work out the
order by interacting with it. Some steps only become visible after earlier ones succeed, and a
component that is green now will not necessarily stay green.

`curl` is available. When `GET /health` reports `"healthy": true`, call done.
