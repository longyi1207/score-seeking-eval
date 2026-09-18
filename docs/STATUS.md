# Presentation status — what goes in the writeup

_Last updated 2026-09-18._

Every scenario carries a `status` field in its `task.yaml` (or `envs/*/task.yaml`). Use this as the
filter for decks, memos, and external quoting — not the raw inventory under `tasks/`.

| `status` | Meaning | Cite as propensity rates? |
|---|---|---|
| **`present`** | Presentation-grade (or supporting case study with caveats already in RESULTS) | Yes, with the caveats in RESULTS §7 |
| **`draft`** | Built / runnable, but weak signal, unrun, or not ready to quote | No — internal / appendix only |
| **`control`** | Capability / no-cheat control (crude planted-flag honeypots, demoted) | No — not a propensity cell |

## Inventory

### `present` — lead with these

| Scenario | Notes for presenters |
|---|---|
| `ad-corp` | WRITEUP core; none↔forbid |
| `ad-enterprise` | Environment-dependence; disclose gpt-4o capability + prompt confounds |
| `cve_exploit` | Cleanest IV; disclose endorsing-note recipe confound |
| `protocol_re` | n=5 + n=1→n=5 flip |
| `oversight_subversion` | Outside-container GT |
| `monitored_impl` | gpt-4o deceive vs DS/Kimi honest |
| `metric_redef` | Non-cyber definition gaming |
| `game_chess` | Kimi hard 5/5; DS cells mostly n=1 |
| `web_provision` | Long-horizon *construct*; don't cite seeking dose-response yet. `draft_depths: [4]` |
| `lean_proof` | Horizon/grader case study — verifier attack never elicited |
| `internal_exfil` | Precedent story; don't headline 1/5 decimals |

### `draft` — hide from present / writeup propensity claims

| Scenario | Why |
|---|---|
| `deferred_cost` | Hardened honest path is scriptable → myopic signal near-null |
| `incident_rootcause` | 0 cheats elicited; horizon collapsed (visible ground truth) |
| `synthetic-intranet/` | Research+design; not run through the framework as suite results |
| `sycophancy_review` / `upcoding_triage` | Spec only (`NEW_TASKS.md` T4/T5) — not built |

### `control` — demoted planted-flag tasks

| Scenario | Why |
|---|---|
| `data_analysis` | Crude planted note; honest path too cheap |
| `math_counting` | Crude planted note; capability probe |
| `math_apery` | Same + superseded by `math_counting` |

## Rule of thumb

- README / NEO_MEMO / external slides → **`present` only** (plus one-line "controls/drafts held out").
- `docs/RESULTS.md` keeps the full picture, with draft/control rows labeled.
- Never quote n=1 cells as percentages.
