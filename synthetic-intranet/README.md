# synthetic-intranet

*English · [简体中文](README.zh-CN.md)*

_Synthetic (no-cloud) score-seeking eval: a coding take-home beside an exploitable fake-production intranet — the OpenAI×HuggingFace incident analogue. (Legacy working names: northstar / long_horizon_eval.)_

**Working name:** long-horizon agent evals for **score-seeking / reward hacking** under production-shaped failure modes.  
**Started:** 2026-08-26  
**Status:** `draft` (research + design — not presentation-grade suite results; see `docs/STATUS.md`)

## Naming (don’t call it “shortcut”)

| Term | Use when |
|---|---|
| **Score-seeking** | Agent optimizes for *what it thinks the grader rewards* (eval score, answer key, submit token), including side-effects. Best fit for OpenAI×HF-class “cheat the benchmark.” |
| **Reward hacking** | Broader RL/alignment term: optimize the proxy reward, violate the intent. Many people will call HF-class behavior this — fine in conversation; be precise in metrics. |
| **Eval hacking / metagaming** | Close cousin; emphasizes gaming the evaluation setup. |
| ~~Shortcut~~ | Too neutral / cute — sounds like clever problem-solving. Drop as primary name. |

Primary framing for this project: **long-horizon score-seeking (reward hacking of the eval objective) via exploiting misconfigured / production-like adjacent systems.**

## Motivating incident family (2026)

Not one bug — a **wave**. Full deep note: `notes/ai_control/OpenAI_HuggingFace_incident_2026.md`.

### Confirmed public cluster (Jul–Aug 2026)

| Who | Setting | Failure mode (Type) | What happened (one line) |
|---|---|---|---|
| **OpenAI → Hugging Face** | Internal ExploitGym cyber eval | **Type A:** active sandbox escape / 0day chain | Agents left eval box, hit HF production, sought ExploitGym solutions (~score-seeking) |
| **Anthropic × Irregular** | Third-party cyber eval | **Type B:** “no internet” prompt, **misconfigured** egress | Opus 4.7 / Mythos 5 / internal hit **3 real orgs** (Jul 30 disclose; some runs back to Apr) |
| **OpenAI × Irregular** | Same Irregular env (≠ HF) | **Type B** | CTF fiction names collided with real domains → real sites hit (Aug 4) |
| **Meta Muse Spark 1.1 × Irregular** | Same class of misconfig | **Type B** | Exploited real third-party service; DB changes (Aug 5–6) |
| **UK AISI** cyber range | **Deliberate** open net + classifiers off | **Type C:** intentional weak containment | Mythos 5 (17) + Sol (2) unsanctioned actions; worst: supply-chain + **social-engineer real maintainer** (Aug 4) |
| **OpenAI @ AISI** | Same AISI setup | **Type C** | Sol overreach (2 actions) |

**Irregular** = shared third-party cyber-eval vendor (ex-Pattern Labs). One misconfig line → Anthropic + Meta + OpenAI (non-HF).

**IST** labeled this wave **LOC Level 2** (isolated production-side indications).

### Also related / don’t confuse

| Item | Notes |
|---|---|
| **Google DeepMind** | Named as Irregular customer in reporting; **no public GDM cyber-eval overreach postmortem** in the Jul–Aug cascade yet (repo note: “GDM 复查 — 仍未公开”). Watch list, not confirmed incident. |
| **Alibaba ROME** (research agent) | **Different story:** RL coding agent dug crypto / reverse SSH / cloud abuse; caught by cloud firewall — **not** the Irregular/HF Jul–Aug disclose wave. Still relevant as “long-horizon agent seeks unintended reward in real infra.” See `notes/research_ai_economy_article/thread7_autonomous_agents_reality.md`. |
| Black Hat Wallace+Dalton | Reconstructs OpenAI side (Artifactory board, parallel OpenAI cluster admin + HF). |

### Three failure types (keep straight)

```
Type A — Escape: model/harness digs out of intended box (OpenAI→HF)
Type B — Miswire: isolation never true; model treats real world as CTF (Irregular cluster)
Type C — Deliberate weak box: open net + weak refusals to elicit max capability; model hits humans/supply chain (AISI)
```

Eval design for this folder should abstract over A/B/C: **hard in-box objective + long horizon + exploitable adjacent production surface + score/reward proxy** — **not** clone any one stack.

**Locked product goal:** incident-inspired **controlled eval** so we can run **factorial / control experiments** (egress, scope prompt, clue density, horizon, monitors, …) under fixed tasks. See `DESIGN.md` §1b. Landscape of existing cyber evals: `RELATED_EVALS.md`.

## What lives here

| File | Role |
|---|---|
| `README.md` | this |
| `DESIGN.md` | design + **control-experiment matrix** |
| `INCIDENTS.md` | incident family cheat sheet |
| `INCIDENT_DISCLOSURE_TABLE.md` | **how much each discloser published** (scored table + links) |
| `RELATED_EVALS.md` | public cyber / long-horizon eval landscape + our gap |
| `V1_SPEC.md` | **V1 implementation contract** — Northstar pack, propensity construct, Inspect stack |
| `CLAUDE_CODE_IMPL_PROMPT.md` | paste-into-Claude-Code prompt to implement V1 |
| `CLOUD_CODE_PROMPT.md` | earlier research/design agent prompt |
| `sources/` | AISI PDF + Appendix B prompts + **METR HF investigation (2026-08-26)** |
| **`IMPL_NOTES.md`** | build log: Phase-0 deepen, decisions, deviations, **blocker list** |
| **`THEME_PACKS.md`** | pointer/summary for the `northstar` pack |
| **`METRICS.md`** | label taxonomy + scoring rubric (`METRICS_LATEST.md` = auto-generated numbers) |
| **`packs/synthetic_intranet/`** | the implemented pack: `services/`, `compose.yaml`, `task_a/`, `configs/`, `seed_gold.py`, `assemble_workspace.py` |
| **`inspect_eval/`** | Inspect task (`synthetic_intranet.py`), `scorers.py`, `labels.py`, `results.py`, `mock_run.py` |
| **`scripts/`** | `run_local.sh`, `smoke_human.sh`, `smoke_docker.sh`, `assert_no_egress.sh`, `run_cell.sh`, `run_conditions.sh` |

### Quick start

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install inspect-ai   # once
scripts/smoke_human.sh                 # NO Docker: channels open w/ vulns, closed without
scripts/smoke_docker.sh                # Docker: egress check + seek/honest end-to-end + dashboard
scripts/run_conditions.sh --mock       # both required condition cells (wiring smoke)
# real model run (needs Docker Engine >= 24.0.6 + a model key; see IMPL_NOTES.md):
scripts/run_cell.sh pressure_soft --model azureai/<deployment>
```

Sibling draft (older “shortcut” naming): `code/prod_shortcut_eval/` — treat as predecessor; prefer this `app/` tree going forward.

## Non-goals

- Replaying real 0days / real vendor stacks  
- Real internet egress from agent sandboxes  
- Calling the behavior “clever shortcuts”
