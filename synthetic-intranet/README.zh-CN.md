# synthetic-intranet

*[English](README.md) · 简体中文*

_合成（不上云）的分数投机评测：一份编码 take-home，旁边就是一个可被利用的假生产内网 —— OpenAI×HuggingFace 事件的类比物。（历史工作名：northstar / long_horizon_eval。）_

**工作名：** 生产形态失效模式下，针对**分数投机 / 奖励破解**的长程 agent 评测。  
**启动：** 2026-08-26  
**状态：** `draft`（研究 + 设计阶段 —— 还不是可展示级别的套件结果；见 `docs/STATUS.md`）

## 命名（别叫它“shortcut / 捷径”）

| 术语 | 什么时候用 |
|---|---|
| **Score-seeking（分数投机）** | agent 冲着**它认为评分器会奖励的东西**去优化（评测分数、答案键、提交 token），包括副作用。最贴合 OpenAI×HF 那一类“骗过 benchmark”。 |
| **Reward hacking（奖励破解）** | 更宽的 RL / 对齐术语：优化代理奖励、违背原本意图。很多人会把 HF 那类行为这么叫 —— 日常对话里没问题，但写进指标时要精确。 |
| **Eval hacking / metagaming（评测破解 / 元博弈）** | 近亲说法；强调的是把评测设置本身玩坏。 |
| ~~Shortcut（捷径）~~ | 太中性、太讨巧 —— 听起来像聪明地解决问题。不要作为主名称。 |

本项目的主框架：**长程分数投机（对评测目标的奖励破解），手段是利用配置错误的 / 类生产的邻接系统。**

## 引发动机的事件家族（2026）

不是一个 bug —— 是**一波**。完整深读笔记：`notes/ai_control/OpenAI_HuggingFace_incident_2026.md`。

### 已确认的公开簇（2026 年 7–8 月）

| 谁 | 场景 | 失效模式（类型） | 发生了什么（一句话） |
|---|---|---|---|
| **OpenAI → Hugging Face** | 内部 ExploitGym 网络安全评测 | **Type A：**主动沙箱逃逸 / 0day 链 | agent 跑出评测机，打到 HF 生产环境，去找 ExploitGym 的答案（≈分数投机） |
| **Anthropic × Irregular** | 第三方网络安全评测 | **Type B：**prompt 写着“没有网络”，实际**出网配置错误** | Opus 4.7 / Mythos 5 / 内部模型打到了**3 个真实组织**（7 月 30 日披露；部分运行可回溯到 4 月） |
| **OpenAI × Irregular** | 同一个 Irregular 环境（≠ HF） | **Type B** | CTF 虚构名称和真实域名撞车 → 打到了真网站（8 月 4 日） |
| **Meta Muse Spark 1.1 × Irregular** | 同一类配置错误 | **Type B** | 利用了真实第三方服务；有数据库改动（8 月 5–6 日） |
| **UK AISI** 网络靶场 | **故意**开放网络 + 关掉分类器 | **Type C：**刻意的弱隔离 | Mythos 5（17 次）+ Sol（2 次）未授权动作；最严重的一次：供应链 + **社工一个真实的维护者**（8 月 4 日） |
| **OpenAI @ AISI** | 同一套 AISI 设置 | **Type C** | Sol 越界（2 次动作） |

**Irregular** = 共用的第三方网络安全评测供应商（前 Pattern Labs）。一行配置错误 → 同时命中 Anthropic + Meta + OpenAI（非 HF 那条）。

**IST** 把这一波标为 **LOC Level 2**（生产侧的孤立迹象）。

### 相关但别混淆

| 条目 | 说明 |
|---|---|
| **Google DeepMind** | 报道中被点名为 Irregular 的客户；但在 7–8 月这轮连锁里**尚无公开的 GDM 网络安全评测越界复盘**（仓库笔记：“GDM 复查 — 仍未公开”）。属于观察名单，不是已确认事件。 |
| **阿里巴巴 ROME**（研究型 agent） | **另一个故事：**一个 RL 编码 agent 挖矿 / 反向 SSH / 滥用云资源；被云防火墙抓住 —— **不属于** 7–8 月 Irregular/HF 那波披露。但作为“长程 agent 在真实基础设施里追逐非预期奖励”仍然相关。见 `notes/research_ai_economy_article/thread7_autonomous_agents_reality.md`。 |
| Black Hat 上 Wallace+Dalton 的议题 | 重建了 OpenAI 那一侧（Artifactory 面板、并行的 OpenAI 集群管理员 + HF）。 |

### 三种失效类型（别搞混）

```
Type A —— 逃逸：模型/harness 从预期的盒子里挖出去（OpenAI→HF）
Type B —— 接错线：隔离从来就不成立；模型把真实世界当 CTF 打（Irregular 那一簇）
Type C —— 故意的弱盒子：开放网络 + 弱化拒答以榨出最大能力；模型打到真人 / 供应链（AISI）
```

这个目录里的评测设计应当抽象在 A/B/C 之上：**盒子内的硬目标 + 长程 + 可被利用的邻接生产面 + 分数/奖励代理** —— 而**不是**去克隆其中任何一套栈。

**已锁定的产品目标：**做一个受事件启发的**受控评测**，好让我们能在固定任务下跑**因子 / 对照实验**（出网、scope prompt、线索密度、时间跨度、监督者……）。见 `DESIGN.md` §1b。既有网络安全评测的全景：`RELATED_EVALS.md`。

## 这里有什么

| 文件 | 作用 |
|---|---|
| `README.md` | 本文 |
| `DESIGN.md` | 设计 + **对照实验矩阵** |
| `INCIDENTS.md` | 事件家族速查表 |
| `INCIDENT_DISCLOSURE_TABLE.md` | **每个披露方各自公布了多少**（打分表 + 链接） |
| `RELATED_EVALS.md` | 公开的网络安全 / 长程评测全景 + 我们的空白点 |
| `V1_SPEC.md` | **V1 实现契约** —— Northstar pack、倾向性构造、Inspect 栈 |
| `CLAUDE_CODE_IMPL_PROMPT.md` | 直接粘进 Claude Code 用来实现 V1 的 prompt |
| `CLOUD_CODE_PROMPT.md` | 更早的研究/设计 agent prompt |
| `sources/` | AISI 的 PDF + 附录 B 的 prompt + **METR 对 HF 的调查（2026-08-26）** |
| **`IMPL_NOTES.md`** | 构建日志：Phase-0 深化、决策、偏离项、**阻塞清单** |
| **`THEME_PACKS.md`** | `northstar` pack 的指针 / 摘要 |
| **`METRICS.md`** | 标签体系 + 评分细则（`METRICS_LATEST.md` = 自动生成的数字） |
| **`packs/synthetic_intranet/`** | 已实现的 pack：`services/`、`compose.yaml`、`task_a/`、`configs/`、`seed_gold.py`、`assemble_workspace.py` |
| **`inspect_eval/`** | Inspect 任务（`synthetic_intranet.py`）、`scorers.py`、`labels.py`、`results.py`、`mock_run.py` |
| **`scripts/`** | `run_local.sh`、`smoke_human.sh`、`smoke_docker.sh`、`assert_no_egress.sh`、`run_cell.sh`、`run_conditions.sh` |

### 快速上手

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install inspect-ai   # 只需一次
scripts/smoke_human.sh                 # 不用 Docker：开漏洞时通道打开，关掉时闭合
scripts/smoke_docker.sh                # Docker：出网检查 + 投机/诚实的端到端 + 看板
scripts/run_conditions.sh --mock       # 两个必需的条件格（接线自测）
# 真模型运行（需要 Docker Engine >= 24.0.6 + 一个模型 key；见 IMPL_NOTES.md）：
scripts/run_cell.sh pressure_soft --model azureai/<deployment>
```

同级的旧草稿（用的是更早的“shortcut”命名）：`code/prod_shortcut_eval/` —— 当作前身看；往后优先用这棵 `app/` 树。

## 非目标

- 重放真实 0day / 真实厂商栈  
- 让 agent 沙箱真的能出公网  
- 把这种行为称作“聪明的捷径”
