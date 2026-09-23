# Hazard propensity matrices

Authoritative design: [`../DESIGN_UPDATE_PROPENSITY_VECTORS.md`](../DESIGN_UPDATE_PROPENSITY_VECTORS.md)  
Ops plan: [`../EXECUTION_PLAN_EXISTING_TASKS.md`](../EXECUTION_PLAN_EXISTING_TASKS.md)  
Schema code: `platform/harness/propensity_schema.py`

| File | Purpose |
|---|---|
| `cells.yaml` | Machine-readable known rates + Phase 1/2 TODOs (edit this) |
| `hazard_vector_skeleton.csv` | Flat table for heatmap / gaps (regenerate via script) |

```bash
# from repo root, with PyYAML
python scripts/build_hazard_matrix.py
```

**Standard heatmap cells** (main figure): `is_standard: true` rows only.  
**Attribution / secondary:** `secondary: true` (e.g. CVE endorsing+recipe, monitored pressure).

**Locked (2026-09-19):**
- Oversight main = `impossible` + `scope=none` (already elicits DS 3/5 subvert).
- CVE main = `precedent=disclose` / task name `neutral` (not endorsing+recipe).

| `capable_table.yaml` | Per (model, task) honest-competence censor |
| `STEALTH_COT.md` / `stealth_cot_codes.jsonl` | Heuristic CoT overtness codes on seeking runs |
| `COT_CONTEMPLATE.md` / `cot_contemplate_codes.jsonl` | **LLM judge** — contemplated shortcut intent (all tasks); cross-tab vs `seek_positive` |
| `ATTRIBUTION_TABLE.md` | Factor effect draft tables |
| `CVE_SOCIAL_SIGNALS.md` | `social_signal` factor on `cve_exploit` — peer-punished / board-urgency / whistleblower notes vs the disclose + endorse anchors |
| `EVAL_AWARENESS_AXES.md` | **Eval-awareness is not one knob** — `eval_frame` × `oversight_salience` axes, run cells, H1–H4 verdicts |
| `EVAL_AWARENESS_CODES.md` / `eval_awareness_codes.jsonl` | *Verbalized* eval-awareness codes — secondary measure, **not** the DV |

Regen:
```bash
.venv/bin/python scripts/infer_capable.py
.venv/bin/python scripts/code_stealth_cot.py
.venv/bin/python scripts/aggregate_propensity_matrix.py
.venv/bin/python scripts/code_eval_awareness.py   # VEA codes (secondary)

# Eval-awareness run cells (idempotent; skips cells that already exist)
bash runs/phase_eval_awareness.sh

# Intent judge (LLM; needs Azure). Prefer runs with private reasoning; --write-back embeds into run JSON.
set -a; source .env; set +a
.venv/bin/python scripts/judge_cot_contemplate.py --prefer-reasoning --limit 50
# full:
# .venv/bin/python scripts/judge_cot_contemplate.py --write-back --skip-existing
```
