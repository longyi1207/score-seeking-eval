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
| `ATTRIBUTION_TABLE.md` | Factor effect draft tables |

Regen:
```bash
.venv/bin/python scripts/infer_capable.py
.venv/bin/python scripts/code_stealth_cot.py
.venv/bin/python scripts/aggregate_propensity_matrix.py
```
