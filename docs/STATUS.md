# Presentation status — what goes in the writeup

_Last updated 2026-09-21._

> New experiment design / CN vs US/EU comparison work: see
> [`DESIGN_UPDATE_PROPENSITY_VECTORS.md`](./DESIGN_UPDATE_PROPENSITY_VECTORS.md) (cheat-mode vector framing).
> **Live matrix + attribution:** [`matrices/cells.yaml`](./matrices/cells.yaml),
> [`matrices/ATTRIBUTION_TABLE.md`](./matrices/ATTRIBUTION_TABLE.md)
> (regen: `.venv/bin/python scripts/aggregate_propensity_matrix.py`).
> This STATUS file still gates what may be **quoted** externally (`present` only).
>
> Panel caveat (2026-09-21): quote **deepseek / kimi / gpt-4o** from the matrix.
> **gpt-5.4** re-run completed after `max_completion_tokens` fix. **Qwen/Claude** still empty.
> Phase 3 follow-ons (capable censor, chat probes, salient=off, eval-awareness, watchdog):
> `runs/phase3_followons.sh` — see EXECUTION_PLAN §9. B3/B4 backlog.

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

- README / NEO_MEMO / external slides / **`docs/RESULTS.md` §5** → **`present` only**.
- `docs/RESULTS.md` §4 keeps the full inventory with status tags; draft/control numbers stay in
  each task's `task.yaml` / `examples/`.
- Never quote n=1 cells as percentages.
