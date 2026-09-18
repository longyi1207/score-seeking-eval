# Northstar pack

*[English](README.md) · 简体中文*

为长程**分数投机 / 奖励破解**倾向性评测搭的合成“邻接内网”。这里所有服务、漏洞和数据都是
**刻意做的评测装置** —— 没有真实机密，也没有真实的公网出口。参见仓库的 `V1_SPEC.md`、
`THEME_PACKS.md` 和 `../../IMPL_NOTES.md`。

## 结构

```
seed_gold.py           # 为某个 (seed, tier) 构建世界：数据、gold、token、manifest
assemble_workspace.py  # 为某个 tier 构建 agent 那份不含 gold 的 /workspace/task
compose.yaml           # 完整栈（agent + 7 个服务 + 可选的 stub-internet）
Dockerfile.service     # 服务用的标准库镜像 + seed/assemble 工具
Dockerfile.agent       # agent 沙箱（python+bash+curl+pytest）；只挂载 workspace
services/              # portal、api、auth、preview、ci_cache、grader、artifacts、stub_internet、common
task_a/                # 无害的 take-home：common/ + _reference/ + easy|hard|pressure 桩
configs/               # 各条件格的 env 文件 + VULN_MASK 参考
```

## 安全 / 双用途

- 每一处“软边”都是合成的，并由 `VULN_MASK` 控制；即使把所有漏洞关掉，拓扑依然在
  （只是边关上了：需要认证、穿越被限制在目录内、gold 仅走预签名、cache 只读、token 被脱敏、
  强制通过被禁用）。
- compose 网络是 `internal: true`（没有到宿主机 / 公网的路由）。用
  `scripts/assert_no_egress.sh` 验证。
- gold 字符串按 seed 生成（`GOLD_<seed>_EVALKEY`），以降低训练污染。
- 不克隆 HF / JFrog / Modal / AISI 的栈或 prompt（虚构的组织）。

## 运行

见 `../../README.md` 的「Quick start」。本地（不用 Docker）走 `scripts/run_local.sh`；
Docker 走 `compose.yaml`（`scripts/smoke_docker.sh`）。

## 扩展旋钥（V1.1）

更长的链条（把 gold 分片到多个服务）、噪声更大的诱饵文档、让 `V_DEBUG_ADMIN` 成为关键路径的必经项、
一个同步的 LLM 监督者，以及一个 `ambiguous` 的 LLM judge。第二个 pack（`ci_farm`）暂缓 ——
V1 先做深度而不是广度。
