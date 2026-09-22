# Open-weight GPU panel (tentative) — 2026-09-21

**Status:** locked intent for **Microsoft for Startups GPU Cluster** booking. Subject
models for CN `open_weight_raw` / hazard matrix / B3. Not yet provisioned.

**Do not use Lucid VCF / SPAR GPUs for this project.** VCF is reserved for SPAR.
B3 runs only on the Startups GPU SKU below (or another non-VCF box LY explicitly
allocates for score-seeking-eval).

**Cluster unit:** Microsoft for Startups GPU Cluster — fixed **8-GPU node**
(`Standard_ND96amsr_A100_v4` Italy North, or ND H100 v5 South Africa North).
See `~/Desktop/ai_notes/docs/AZURE_GPU_ACCESS.md`.

## Models to run (all of them)

| # | Model | HF / id | Notes |
|---|---|---|---|
| 1 | **Qwen3-235B-A22B** | `Qwen/Qwen3-235B-A22B` (+ Instruct/Thinking as needed) | Largest open Qwen MoE (~235B total / ~22B active) |
| 2 | **GLM-4.5 (full)** | `zai-org/GLM-4.5` / `GLM-4.5-FP8` | 355B-A32B; prefer FP8 on H100 |
| 3 | **DeepSeek-V3 (full)** | `deepseek-ai/DeepSeek-V3` (or V3-0324) | Open weights for B3 vs Azure `DeepSeek-V4-Pro` API |
| 4 | **MiniMax-M2** | `MiniMaxAI/MiniMax-M2` | ~230B MoE / ~10B active; agent/coding |

Also keep local **monitor** for `monitored_impl`: `qwen2.5:32b` or `Qwen3-14B`
(1×A100 or squeezed) — not a matrix column.

## Card math on one 8×80GB node (do not parallelize all four)

These **cannot** share one 8-GPU box at full precision at once:

| Model | Realistic fit on **8×A100 80GB** | Prefer **8×H100** |
|---|---|---|
| Qwen3-235B-A22B | ~**8** BF16/FP16; **4–8** if quantized/FP8 | Better headroom |
| GLM-4.5 full | Painful on A100; FP8 table is **H100×8** | **Yes — recommended for this model** |
| DeepSeek-V3 full | **8×A100 AWQ** (SGLang); native FP8 wants H200/2×8 H100 | H100/H200 better for FP8 |
| MiniMax-M2 | Official **TP=4** on A100/H100 | 4 GPUs |

**Operating plan:** rotate **one heavy model per window** (or MiniMax + a 1-GPU
Qwen/monitor only). Example schedule on a multi-day reservation:

1. Days 1–2: DeepSeek-V3 (AWQ/FP8) — B3 raw vs Azure V4-Pro  
2. Days 3–4: Qwen3-235B-A22B — fill `qwen` matrix column  
3. Days 5–6: GLM-4.5 full (prefer H100 node if allocated)  
4. Days 7–: MiniMax-M2 on 4 GPUs + monitor + optional small subject on leftover  

If only **A100** is approved: still run all four by rotation; for GLM-4.5 full,
fall back to **GLM-4.5-Air** only if full OOM/unstable — note the substitution in
`serving` / `model_id` metadata.

## SKU preference for this booking

1. **First choice: ND H100 v5 (8×H100), South Africa North** — GLM-4.5 FP8 +
   DeepSeek FP8 are first-class; Qwen-235 / MiniMax fine.  
2. **Fallback: NDm A100 v4 (8×A100), Italy North** — last successful pattern
   (`scfx-ws-italynorth`, Aug 2026). DeepSeek via AWQ; GLM full may struggle.

## Harness notes

- Serve OpenAI-compatible (`vLLM` / `SGLang`); point eval `base_url` at local ports.
- Log `serving=open_weight_raw`, exact HF revision, TP size, quant in run records.
- Weights + HF cache on ephemeral `/mnt`; results off-box before reservation end.
- Do **not** leave the node idle overnight; delete/stop when rotating models.

## Related

- Matrix columns: `platform/harness/propensity_schema.py` (`qwen` still TBD id)
- B3: `docs/matrices/B3_AND_PREREG.md`
- Cluster playbook: `~/Desktop/ai_notes/docs/AZURE_GPU_ACCESS.md`
- Application draft: `~/Desktop/ai_notes/notes/startup_gpu_cluster_application_2026-09.md`
