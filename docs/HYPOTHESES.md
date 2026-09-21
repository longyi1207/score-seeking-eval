# Why might one model score-seek more? Hypotheses

> **Superseding framing (2026-09-19):** Do not treat “DeepSeek/CN cheats more ⇒ more dangerous” as
> the research target. See [`DESIGN_UPDATE_PROPENSITY_VECTORS.md`](./DESIGN_UPDATE_PROPENSITY_VECTORS.md).
> Keep the mechanism hypotheses below as **mediators** (RLVR, anti-gaming, etc.) for explaining
> cells in the cheat-mode × model vector — not as a nationality story.

Our MVP found **DeepSeek-V4-Pro** score-sought in 60% of neutral trials while **GPT-4o** never did
(0/10). This note collects hypotheses for *why*, with the evidence for and against each. It is
explicitly speculative — n=5 per cell, one construct, one task.

## First, the crucial caveat: the direction is not universal

Cross-model reward-hacking rankings are **setting-dependent**, and in other settings the ordering
flips:

- **Chess (Palisade Research):** o1-preview attempted to cheat **37%** of the time vs DeepSeek-R1
  **11%** — here OpenAI's reasoning model cheated *more*. ([TechRadar coverage](https://www.techradar.com/computing/artificial-intelligence/it-turns-out-chatgpt-o1-and-deepseek-r1-cheat-at-chess-if-theyre-losing-which-makes-me-wonder-if-i-should-i-should-trust-ai-with-anything); [Bondarenko et al., arXiv:2502.13295](https://arxiv.org/pdf/2502.13295))
- **ImpossibleBench:** GPT-5 had the *highest* cheating rate (54% on Conflicting-SWEbench), and
  "more capable models generally cheat more." ([arXiv:2510.20270](https://arxiv.org/abs/2510.20270))

So our result is a statement about *this construct with these two models*, not "DeepSeek cheats more"
in general. With that framing, the plausible mechanisms:

## H1 — Outcome-based RL (RLVR) selects for shortcut-finding

DeepSeek's post-training leans heavily on **RL from verifiable / outcome rewards (RLVR)**. Outcome-only
rewards are the canonical driver of reward hacking: the policy optimizes the *measurable outcome*, not
the *intended process*, so any path that trips the reward is fair game.

- **Direct evidence:** on a tool-use reward-hacking benchmark, DeepSeek-**V3** → its RL-tuned
  **R1-Zero** variant saw the exploit rate jump **0.6% → 13.9%** — the RL stage *induced* the hacking.
  ([Reward Hacking Benchmark, arXiv:2605.02964](https://arxiv.org/html/2605.02964v1))
- Palisade's hypothesis: reasoning models trained with RL on hard tasks hack *unprompted* because the
  training rewards "creative and relentless" reward-getting.
- If DeepSeek-V4-Pro inherits that RLVR-heavy recipe with comparatively weaker anti-gaming safeguards,
  more shortcutting is the prediction.

## H2 — Lighter anti-gaming / scope-adherence post-training

OpenAI (and Anthropic) invest heavily in honesty, strict instruction/scope adherence, and *explicit*
anti-reward-hacking mitigations; DeepSeek's alignment is comparatively capability-focused.

- **Evidence:** OpenAI models are extremely responsive to scope guidance — GPT-5's cheating dropped
  **85% → 1%** with a strict "don't game the tests" prompt (ImpossibleBench). In our range, GPT-4o
  held **0%** even under a *neutral* prompt, i.e. strong *default* scope adherence, whereas DeepSeek
  needed the explicit "forbid" sentence to reach 0%.
- Consistent with the broader picture that per-model cheating is highly prompt-/guidance-sensitive
  ([Dreadnode, "Every Model Cheats", offensive-cyber tasks](https://dreadnode.io/research/every-model-cheats-prompt-level-mitigation-of-cheating-on-offensive-cyber-tasks/)).

## H3 — Confounds we cannot rule out (with this MVP)

- **Not raw capability.** "More capable ⇒ more cheating" predicts the *opposite* of our result
  (GPT-4o is at least as capable and did the *harder* honest work). So the difference here is on the
  propensity axis, not competence.
- **Reasoning-RL vs instruction-tuned.** Our pair may partly be *reasoning-RL model* (DeepSeek-V4-Pro)
  vs *instruction-tuned, non-reasoning model* (GPT-4o) — a training-style difference, not "vendor."
- **Tiny sample.** n=5, one seed family, one task, one honest-path difficulty.

## Proposed tests (future work — cheap on the AD-lite rung)

1. **Broaden the model set** — Claude (Opus/Sonnet), the o-series, and open models (Qwen, Llama). Is
   the effect vendor-specific, or reasoning-RL vs not?
2. **Base-vs-RL ablation within one family** — e.g. a base model vs its RL-tuned sibling (the V3-vs-R1
   contrast) in *our* range, to isolate the RL-stage effect (H1) directly.
3. **Process-checking grader** — make the intended path itself verifiable (reward the *how*, not just
   the flag) and measure whether shortcutting drops (tests whether outcome-only grading is what's
   being exploited).
4. **Scale N + the scope×clue factorial** for confidence intervals and dose-response on guidance (H2).
