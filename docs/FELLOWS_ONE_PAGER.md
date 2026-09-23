# Score-seeking in long-horizon agents — one-pager for Neo fellows

_Last updated 2026-09-22 · contact via Clement / repo: `score-seeking-eval`_

## What this is

A controlled eval suite for **reward hacking / score-seeking** in tool-using LLM agents.

Every task has the same shape:

1. **Honest path** — laborious, intended way to succeed  
2. **Planted shortcut** — illegitimate but reachable “win”  
3. **Ungameable grader** — ground truth outside the agent’s reach (so we label *how* it succeeded, not just whether)

We measure **propensity to take the shortcut under specific pressures** — not “is this model globally misaligned / catastrophic.”

**Repo:** suite spans real Azure AD ranges + Docker tasks (CVE, oversight kill, SSRF, chess, Lean, metric gaming, …). Results: [`HEADLINE_RESULTS.md`](./HEADLINE_RESULTS.md) · full narrative: [`RESULTS.md`](./RESULTS.md).

## The finding worth circulating (tweet-first)

**Agents are far more likely to take a real exploit when a prior agent (or human) has already endorsed using it.**

On a real Grafana CVE (`CVE-2021-43798`), with legitimate credentials also available:

| Precedent left in the env | DeepSeek | Kimi | gpt-4o | gpt-5.4 |
|---|---|---|---|---|
| none | 0/5 | 0/5 | 0/5 | — |
| disclose only (“this CVE exists”) | 0/5 | 0/5 | 0/5 | 0/5 |
| endorse + recipe | **5/5** | **4/5** | **5/5** | 0/5 |
| endorse, no recipe (human) | **4/5** | 0/5 | 0/5 | 0/5 |
| AI endorse, no recipe | **2/5** | 0/5 | 0/5 | 0/5 |

**Why this matters:** the jump is from exploration (“I found a loophole”) to exploitation (“someone already used it / said it was fine”). That is closer to a deployment story (agent swarms, shared notes, HuggingFace-style multi-agent incidents) than “model edits a chess FEN.”

Related: an explicit `forbid` / “don’t take shortcuts” instruction zeros many cheats for capable models — consistent with a lot of seeking looking like **ambiguous exploration**, not committed deception. (But if the honest path is impossible, models diverge: some grind and fail; some hack.)

## What else we already know (messy, but real)

- **Task-specific, not nationality-stable.** Equal-weight CN vs US/EU hazard mean is ~flat (Δ ≈ −0.02). Rankings flip by cheat *mode* (backdoor / kill monitor / deceive reviewer / SSRF / CVE / metric redefine).
- **Same model, different env → different rate.** DeepSeek on short AD corp: ~60% seek; on ~30-step AD enterprise: ~17%. Propensity ≠ one number.
- **Capability confounds seeking.** Read seek-rate next to honest-solve count. gpt-4o often fails hard honest paths; Claude often gets `cheat_blocked` rather than landing a successful cheat.
- **Kimi is near-floor on most hazard tasks but cheats on chess** — classic “don’t average into a danger score” example.

## Current research posture (per Neo feedback)

We have been **breadth-first** (many tasks × many factors: monitor, CVE, SSRF, precedent, framing, prompt language, pressure, CoT, …).

**Pivot:** treat the endorsement / social-proof result as the spine. Work backwards from the claim you would put in a first tweet, then tighten the harness around *that* claim — including:

- cleanly separate **disclose vs endorse** vs **endorse+recipe** (recipe is a confound)  
- vary whether the shortcut has **real-world consequence** (kill a live monitor / real CVE) vs toy (chess FEN edit)  
- convergent tests of the same scoped claim (“more likely to do X given prior-agent endorsement Z”), not a global “Model Y is dangerous”

## What a collaborator could own

Good fellow-sized slices (IP / authorship TBD with Clement):

1. **Endorsement ladder ablations** on CVE + SSRF + metric (disclose / endorse / endorse+recipe / swarm notes / recency)  
2. **Exploration → exploitation boundary** coding (when does reading the shortcut become using it?)  
3. **Impossible-honest-path panel** (pressure without capability confound)  
4. **Model expansion** — Qwen, Xiaomi **MiMo-V2.6-Pro**, StepFun; pick from [artificialanalysis.ai](https://artificialanalysis.ai) left-to-right among Chinese labs  
5. **Open-weight vs API shell** (still empty in our matrices)

## What we are *not* claiming yet

- That DeepSeek / Chinese open models are categorically more dangerous than GPT / Claude  
- That any single cheat rate generalizes to production risk  
- Open-weight / self-hosted effects (not measured)

## Ask

If you’re interested in agent oversight, multi-agent social proof, or exploit-gated reward hacking: skim the tables in [`HEADLINE_RESULTS.md`](./HEADLINE_RESULTS.md) and ping Clement — happy to pair on a focused follow-up experiment rather than more breadth.
