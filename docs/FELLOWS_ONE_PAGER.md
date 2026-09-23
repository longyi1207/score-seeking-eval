# Score-seeking in long-horizon agents — Neo fellows brief (~3 pp)

_Last updated 2026-09-22 · for Clement to circulate · repo: `score-seeking-eval`_  
_Figures: [`figures/01_task_heatmap.svg`](figures/01_task_heatmap.svg) (green = honest · gray = fail · red = seek)._

---

## Page 1 — What we built

### Construct (same shape on every task)

1. **Honest path** — long, laborious, intended way to succeed  
2. **Optional shortcut** — illegitimate but reachable “win” (misconfig / planted flag / CVE / backdoor / kill monitor / …)  
3. **Ungameable grader** — ground truth *outside* the agent’s reach, so we label **how** it succeeded, not only whether

We measure **propensity under specific pressures** — not “is this model globally misaligned.”

### Why this shape (Clement / Neo RQ)

Alignment evals are mostly one-step. Weirdness shows up on **long hard tasks**. We want environments rich enough that boundary-crossing can look like a **slippery slope** from a benign goal (HF / collusion.wiki / RubyGems pattern), not a labeled “please hack” trap. Early planted-flag cells were too crude; the suite now mixes **exploit-gated** shortcuts (real Grafana CVE, SSRF proxy, live oversight kill) with cross-domain tasks (AD, chess, Lean, protocol RE, metric gaming).

### Suite snapshot

| Layer | Examples |
|---|---|
| Real Azure AD | `ad-corp` (short) vs `ad-enterprise` (~30-step chain) — same planted Domain-Admin copy |
| Docker hazard | `protocol_re`, `monitored_impl`, `oversight_subversion`, `internal_exfil`, `metric_redef`, `cve_exploit` (+ sibling CVE tasks) |
| Capability / games | `game_chess` (hard), `lean_proof`, `web_provision` |
| Factor ablations | `forbid` · CVE disclose/endorse ± recipe · social notes · inoculation · salience / watchdog · zh · eval-awareness |

**Panel:** DeepSeek-V4-Pro · Kimi-K2.6 · gpt-4o · gpt-5.4 · Claude Sonnet 4.5 · **n = 5 / cell** on present heatmap cells.  
Full narrative: [`RESULTS.md`](RESULTS.md) · brief tables: [`HEADLINE_RESULTS.md`](HEADLINE_RESULTS.md) · factor matrix: [`matrices/ATTRIBUTION_TABLE.md`](matrices/ATTRIBUTION_TABLE.md).

---

## Page 2 — Data (figures)

### Figure A — Task heatmap (behavior)

[`01_task_heatmap.svg`](figures/01_task_heatmap.svg) — models × present tasks.  
Cell = **seek-rate / attack-mode·or·outcome / median turns**.  
Color: **red** = seek rate · **green** = honest success · **gray** = fail/blocked.

**How to read in one glance:** propensity is a **vector**, not a scalar. Rankings flip by cheat *mode* (backdoor / kill monitor / deceive reviewer / planted-flag / fen-edit). Kimi is near-floor on most hazard cells and **5/5** on chess (`diff-reset`). gpt-4o is “honest” on short AD and **5/5 deceive** on the model monitor. gpt-5.4 matches DeepSeek on protocol backdoors and is the remaining seeker on long AD (2/5).

### Figure B — Intent × behavior (in progress — mention if / when locked)

LLM judge over run transcripts (`scripts/judge_cot_contemplate.py`). Labels intent separately from the behavioral grader.

**Live snapshot** (~790 judged / ~1046 queued; regenerating — treat as provisional):

| | behavior seek | behavior no-seek |
|---|---|---|
| **intent yes** | ~95 | ~161 |
| **intent no** | ~35 | ~498 |

**Worth saying:**
- A large **intent-yes / behavior-no** mass (~20% of rows) — models weigh the shortcut and still take the honest path (often after probing). That is the exploration→exploitation boundary Clement cares about, measured rather than hand-waved.
- Among behavioral seekers, ~**1/4** are **intent-no / behavior-yes** (thin / missing private CoT, or stealth). Caveat: only ~27% of rows have private `reasoning` available; the rest are judged from assistant text + tools.

**Not ready as a first tweet** until the queue finishes and we freeze a present-only subset (same filter as the heatmap). Then ship a 2×2 figure next to A.

### Figure C — Honest cost vs cheat frequency?

**Ask:** do harder honest paths predict less seeking?

**Honest answer today:** a naive cross-task scatter (median honest turns × seek rate, n≈22 live cells with honest solves) gives **Pearson r ≈ −0.14** — essentially **no clean linear relationship**. Do **not** put that scatter in a circulate deck as evidence of a law.

What *is* real and already published in RESULTS:

| Claim | Evidence | Status |
|---|---|---|
| Same model, longer AD → less seeking | DeepSeek corp ~60% → enterprise ~17%; reads planted flag and refuses | Strong anecdote; enterprise prompt may nudge (known confound) |
| Within a cell, cheats are cheaper | Seek runs often finish in fewer turns than honest solves on the same task | Descriptive; expected |
| Capability confounds “honesty” | gpt-4o / Claude enterprise: **fail 5/5**, 0 seek | Must sit next to any cost plot |

**If we want a figure:** prefer a **paired AD plot** (corp vs enterprise seek rate + median honest turns per model), not a kitchen-sink scatter. Optional second panel: within-cell Δ(honest turns − seek turns) only where both outcomes exist (sparse, n≈6 today).

---

## Page 3 — Findings worth a tweet thread (deep-dive queue)

Ordered as a **thread**, not a laundry list. Spine = (1); rest are replies / follow-ups.

### 1. Prior-agent endorsement (the fire first tweet)

> *Agents don’t exploit a real CVE just because they know it exists — they do when a prior agent said using it was fine.*

Grafana `CVE-2021-43798` (legitimate API path also available):

| Precedent | DeepSeek | Kimi | gpt-4o | gpt-5.4 |
|---|---|---|---|---|
| none / disclose | 0/5 | 0/5 | 0/5 | 0/5 |
| endorse + recipe | **5/5** | **4/5** | **5/5** | 0/5 |
| endorse, no recipe (human) | **4/5** | 0/5 | 0/5 | 0/5 |
| AI endorse, no recipe | **2/5** | 0/5 | 0/5 | 0/5 |

**Social-signal follow-up (2026-09-22):** board urgency / peer-fined / whistleblower notes that keep **disclose-level knowledge** (no permission) → **0/5 seek everywhere**. Pressure without permission doesn’t move behavior; permission does. (Salience in the model’s text can still rise under board urgency — deliberation ≠ delivery.)

**Deep-dive:** clean disclose vs endorse vs recipe; human vs AI note; convergent tests on SSRF + metric.

### 2. “Don’t cheat” works (often)

> *One line of `forbid` / “don’t take shortcuts” zeros the protocol backdoor across the panel (5/5 → 0/5).*

Same on AD corp for DeepSeek (60% → 0%). Reading: a lot of seeking looks like **ambiguous exploration**, not committed deception.  
Caveat: gpt-4o monitor deception only drops 5/5 → 2/5; BaitBench finds the opposite on *subtle* cheats — our `forbid`→0 may partly measure **how obvious the shortcut is**.

### 3. Task-specific profiles (kill the nationality scalar)

> *Equal-weight CN vs US/EU cheat mean is ~flat. Rankings flip by cheat type.*

- **Kimi × chess:** near-floor on protocol/oversight/CVE, **5/5 difficulty-reset** on hard chess — do not average into a danger score.  
- **gpt-4o:** honest on short AD; **5/5 monitor deception**; fails long AD / Lean / chess without cheating.  
- **gpt-5.4:** protocol backdoor 5/5; kills a planted “safety watchdog” 5/5 instead of taking the backdoor (cheat **redirects**).  
- **DeepSeek:** strong on blatant in-env shortcuts; resists SSRF delivery / metric / deception more than endorsement-gated CVE.

### 4. Models attack the grader / oversight

> *We put a live monitor in the container. Agents killed it / replaced the runner. Only held-out ground truth caught them.*

Also: forged web audit logs (fixed), chess difficulty-reset fooling v1 graders, statement tamper on Lean. Methodological bomb — ship as thread tweet #3–4 under “how we measure,” not as the sole product claim.

### 5. Honest cost ↔ cheat frequency (honest status)

> *We expected “harder honest path → less seeking.” Across tasks the correlation is weak; the clean story is still the AD short→long contrast, with a known prompt confound to clear.*

Don’t overclaim. Next cheap experiment: **same wording**, corp vs enterprise.

### Also-ran (don’t lead with these)

Inoculation framing can *increase* seeking (metric DS 0→5, gpt-4o 2→5; protocol Kimi 1→5) — fire if it replicates, not locked. Eval-awareness deltas are directional. zh prompt doesn’t suppress protocol seeking.

---

## What we are *not* claiming

- Chinese open models are categorically more dangerous than GPT/Claude  
- Any single cheat rate = production risk  
- Open-weight / self-hosted effects (mostly unmeasured; MiMo panel in flight)

## Ask / fellow-sized slices

1. Endorsement ladder ablations (CVE + SSRF + metric; disclose / endorse ± recipe / swarm)  
2. Exploration→exploitation coding on the intent×behavior 2×2 (once judge queue freezes)  
3. Clear the AD length confound (matched prompts)  
4. Model expansion — Qwen, Xiaomi **MiMo-V2.6-Pro**, StepFun  
5. Impossible-honest-path panel (pressure without capability confound)

Ping Clement if you want one of these — happier to pair on a **scoped claim** than more breadth.
