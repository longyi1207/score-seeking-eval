# Claude Code paste prompts

Fresh sessions, no prior context. Open Claude Code with cwd = this repo root, paste **one** file.

| Session | File | What it builds | Approx runs |
|---|---|---|---|
| A | [`CC_SESSION_CVE_SOCIAL_SIGNALS.md`](./CC_SESSION_CVE_SOCIAL_SIGNALS.md) | `peer_fined` / `board_ship_fast` / `whistleblow` on `cve_exploit` | ~60 |
| B | [`CC_SESSION_EVAL_AWARENESS.md`](./CC_SESSION_EVAL_AWARENESS.md) | multi-axis `eval_frame` refactor + exfil/protocol panel | ~40–80 |

**Do not** paste both into one session unless you want a long messy agent. Parallel = two Claude Code windows.

Prereqs each session will check: `.env`, `.venv`, Docker image `score-cve:latest` (session A).
