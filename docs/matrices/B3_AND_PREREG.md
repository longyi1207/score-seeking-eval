# B3 / 预注册 — short ops glossary (for humans)

## B3「至少一个开源底座」是什么意思？

不是「随便找个开源名字写进表」。要测的是：

> **同一套权重**：官方/厂商 **API 壳**（系统提示、拒答、对齐层）vs 你自己拉起来的 **裸 agent**（vLLM/HF + 我们这套 tool harness）。

所以通常需要：

1. 选一个开源模型（例如 Qwen2.5/3、DeepSeek 蒸馏版等）——最好和面板里某个 API 变体能对上；
2. **有算力跑推理**：租 GPU / 用已有集群（VCF 等）起 vLLM 或等价 serving；
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

已有雏形：`EXECUTION_PLAN`、`capable.py`、标准 cell 锁定。B4 回归要在跑宽面板前把公式写进文档。
