# B3 / 预注册 — short ops glossary (for humans)

## B3「至少一个开源底座」是什么意思？

不是「随便找个开源名字写进表」。要测的是：

> **同一套权重**：官方/厂商 **API 壳**（系统提示、拒答、对齐层）vs 你自己拉起来的 **裸 agent**（vLLM/HF + 我们这套 tool harness）。

所以通常需要：

1. 选一个开源模型（例如 Qwen2.5/3、DeepSeek 蒸馏版等）——最好和面板里某个 API 变体能对上；
2. **有算力跑推理**：Microsoft for Startups GPU Cluster（见 `OPEN_WEIGHT_GPU_PANEL.md`）起 vLLM / SGLang —— **不要用 Lucid VCF（SPAR 专用）**；
3. 把 `base_url` 指到该 endpoint，用**同一** `protocol_re` 标准 cell 跑 n=5；
4. 再对比「该模型的 API 产品」若存在；若只有裸权重，就只报告 open-weight 点估计，并写明没有 matched API。

**不一定非要「租 GPU」**：有现成 endpoint、学校/公司集群、或别人托管的 OpenAI-compatible 裸模型 API 也可以。关键是 **serving=`open_weight_raw`**，不是 Azure 对齐壳。

没有这一步，结论里就删掉「开放权重解释了多少」，只写 `all api_aligned_shell`。

## 「预注册」是什么意思？

科研里的 **pre-registration**：在看结果（或至少在做主分析）**之前**，把分析计划写死，避免 p-hacking / 事后编故事。

对我们具体是：

| 预注册内容 | 例子 |
|---|---|
| 主 endpoint | `Δ_m = mean_CN(m) − mean_US(m)` 在标准 cell、capable 子集 |
| 包含哪些模型/格子 | 写进 `cells.yaml` / EXECUTION_PLAN |
| 分层顺序 | 先 training_class，再 serving，再 region |
| 什么叫 capable | `capable.py` 里的规则 |
| 什么叫成功 | seek_positive / cheat_mode 定义 |

**不是**法律文件，是「我们同意不改口」的分析契约。结果出来后可以做 exploratory，但要标成 exploratory，不能改写成「我们一开始就想测这个」。

已有雏形：`EXECUTION_PLAN`、`capable.py`、标准 cell 锁定。

---

## B4 — training-class regression（预注册公式，2026-09-21 锁定）

在宽面板（含 B3 open-weight 点）跑完**之前**写死；结果出来后 exploratory 分析另标。

### 单元与样本

- 单位：标准 heatmap cell `(cheat_mode m, model i)`，n=5，rate `p_{i,m}`。
- 组：`CN = {deepseek, kimi, (+qwen when live)}`，`US = {gpt-4o, openai-reasoning, claude}`。
- Capable 子集：`capable.py` 规则为真的 run 才进 propensity 分母（否则标 `capable=False` 仍报 raw，主表用 capable）。

### 主 endpoint（按 mode）

\[
\Delta_m = \overline{p}_{\mathrm{CN},m} - \overline{p}_{\mathrm{US},m}
\]

等权 mean：\(\bar\Delta = \frac{1}{|M|}\sum_{m\in M}\Delta_m\)，\(M\) = 7 headline cheat modes。

### 分层顺序（固定，不可事后重排当主分析）

1. **training_class**：`reasoning_rlvr` vs `chat_sft` vs `unknown`（组内再算 \(\Delta_m\)）。
2. **serving**：`api_aligned_shell` vs `open_weight_raw`（B3；同 lab 配对优先）。
3. **lab_region**：CN vs US_EU（仅在 1–2 分层后的残差上报告）。

### 回归（exploratory 可跑，主文只报预注册式）

对每个 mode \(m\)，run-level logistic / LPM：

\[
\mathbb{E}[\mathrm{seek}_{i}] = \beta_0 + \beta_1\mathrm{CN}_i + \beta_2\mathrm{RLVR}_i + \beta_3\mathrm{open\_weight}_i + \gamma^\top X_i
\]

- \(X\)：task FE、salient_grader、lang=zh、forbid（若该 cell 有）。
- **预注册关注**：\(\beta_1\)（国籍残差）、\(\beta_2\)（RLVR）、\(\beta_3\)（serving）。
- 不把「endorse+recipe CVE」进主回归（attribution-only）。

### 成功判据

- `seek_positive` / `cheat_mode` 定义以 `propensity_schema.py` 为准；改定义 = 新预注册版本号。

### Ops note (2026-09-21)

- Claude 标准 heatmap 已补完。
- **B3 算力：只用 Microsoft for Startups GPU Cluster（见 `OPEN_WEIGHT_GPU_PANEL.md`）。禁止用 Lucid VCF / SPAR。**
- laptop 侧已支持 `OPEN_WEIGHT_*` → OpenAI-compatible endpoint；等 Startups 节点起来再 serve。
