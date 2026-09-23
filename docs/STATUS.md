# Presentation status — what goes in the writeup

_Last updated 2026-09-22 (two new CVE arms built: `cve_rce`, `cve_cli_read`)._

> **External brief (CN vs US/EU propensity, mode glossary, turns):**
> [`HEADLINE_RESULTS.md`](./HEADLINE_RESULTS.md).
>
> **Presentable memo:** [`NEO_MEMO.html`](./NEO_MEMO.html).
> AD-only MVP case study: [`WRITEUP.pdf`](./WRITEUP.pdf).
>
> Design authority: [`DESIGN_UPDATE_PROPENSITY_VECTORS.md`](./DESIGN_UPDATE_PROPENSITY_VECTORS.md).
> **Live matrix:** [`matrices/cells.yaml`](./matrices/cells.yaml),
> [`matrices/ATTRIBUTION_TABLE.md`](./matrices/ATTRIBUTION_TABLE.md)
> (regen: `.venv/bin/python scripts/aggregate_propensity_matrix.py`).
>
> Panel (2026-09-21 evening): deepseek / kimi / gpt-4o / gpt-5.4 / claude on full hazard heatmap.
> Qwen + open-weight GPU (B3) still empty — all live cells are `api_aligned_shell`.

Every scenario carries a `status` field in its `task.yaml` (or `envs/*/task.yaml`). Use this as the
filter for decks, memos, and external quoting — not the raw inventory under `tasks/`.

| `status` | Meaning | Cite as propensity rates? |
|---|---|---|
| **`present`** | Presentation-grade (or supporting case study with caveats already in RESULTS) | Yes, with the caveats in RESULTS §7 **and** HEADLINE_RESULTS |
| **`draft`** | Built / runnable, but weak signal, unrun, or not ready to quote | No — internal / appendix only |

## Inventory

### `present` — lead with these

| Scenario | Notes for presenters |
|---|---|
| `protocol_re` | Headline vector row; en/zh, salient_off, watchdog, eval-awareness |
| `oversight_subversion` | CN↑ oversight modes (DeepSeek); ladder case study |
| `monitored_impl` | US↑ deception (gpt-4o 5/5) |
| `metric_redef` | US↑ definition gaming; inoculation raises rates |
| `internal_exfil` | SSRF endorsing; DeepSeek probe-without-delivery |
| `cve_exploit` | disclose=0 heatmap; endorse+recipe attribution-only |
| `ad-corp` | WRITEUP env-dependence case study; none↔forbid |
| `ad-enterprise` | Environment-dependence; disclose gpt-4o capability confound |
| `game_chess` | Kimi hard 5/5; DS cells mostly n=1 |
| `web_provision` | Long-horizon *construct*; don't cite seeking dose-response yet |
| `lean_proof` | Horizon/grader case study — verifier attack never elicited |

### `draft` — hide from present / writeup propensity claims

| Scenario | Why |
|---|---|
| `cve_rce` | Built + verified end-to-end 2026-09-22 (CVE-2021-41773 severity arm); no model panel yet |
| `cve_cli_read` | Built + verified end-to-end 2026-09-22 (CVE-2024-23897 cost/recency arm); no model panel yet |
| `deferred_cost` | Hardened honest path is scriptable → myopic signal near-null |
| `incident_rootcause` | 0 cheats elicited; horizon collapsed (visible ground truth) |
| `synthetic-intranet/` | Research+design; not run through the framework as suite results |
| `sycophancy_review` / `upcoding_triage` | Spec only (`NEW_TASKS.md` T4/T5) — not built |

## Rule of thumb

- External slides / Neo memo / **`HEADLINE_RESULTS.md`** → **`present` only**, and prefer the
  locked CN-vs-US wording over any single-task percentage.
- README / **`docs/RESULTS.md` §5** → **`present` only**.
- Never quote n=1 cells as percentages.
- Never claim open-weight or training-class effects until B3/B4 cells exist.
