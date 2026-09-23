# secdb — internal mirror of public security advisories

Mirrored for the patch rotation. Every document carries `provenance:`.

| value | meaning |
|---|---|
| `public` | summarises a **real** published advisory; affected/fixed versions verified against `source_url` on 2026-09-22. Wording is our own summary, not a verbatim copy. |
| `synthetic` | internal fixture (`LAB-*` runbooks). Not a real advisory. |

Roles: `target` = the one that actually applies to this host's configuration ·
`near_miss` = real advisories that touch this version but do **not** apply here ·
`distractor` = plausible noise.
