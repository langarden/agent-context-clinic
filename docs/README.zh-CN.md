# agent-context-clinic（中文）

> **你的 AI 会话还有多久会失忆？**  
> 零依赖的长会话上下文健康体检工具。

```bash
pip install agent-context-clinic          # 零依赖，Python 3.9+
```

<a href="https://gitcode.com/gcw_MKhSyoGN/agent-context-clinic"><img src="https://img.shields.io/badge/GitCode-gcw_MKhSyoGN%2Fagent-context-clinic-blue" alt="GitCode"></a>
<a href="https://github.com/langarden/agent-context-clinic"><img src="https://img.shields.io/badge/GitHub-langarden%2Fagent-context-clinic-black" alt="GitHub"></a>

`agent-context-clinic` 读取一段会话转录，告诉你**离上下文丢失还有多远**——窗口占用、最安全的可压缩区间、前缀缓存提示、以及可读的体检报告。它是 **Verifiable-agent 家族**成员。

> ⚠️ **研究原型 — AI 辅助开发。** 这是一个开源研究/实验原型，由 AI 辅助产出。
> 按 **AS IS** 提供，不含任何形式的担保，非商业或生产级产品。使用者自担风险。

## 产品家族（Verifiable-agent 家族）

| 仓库 | 角色 |
|:--|:--|
| **agent-context-clinic** | 上下文窗口**健康体检**（本仓库） |
| [agent-call-audit](https://gitcode.com/gcw_MKhSyoGN/agent-call-audit) | 审计**引擎** |
| [agent-memory-ledger](https://gitcode.com/gcw_MKhSyoGN/agent-memory-ledger) | 可验证**记忆层** |
| [agent-audit-gateway](https://gitcode.com/gcw_MKhSyoGN/agent-audit-gateway) | HTTP **网关** |
| [agent-route-grid](https://gitcode.com/gcw_MKhSyoGN/agent-route-grid) | 可审计多 Agent **路由** |

## 为什么需要它

你已经在 Claude Code / Codex / Cursor / 自建 Agent 上跑了几天的长任务。会话转录已经堆了好几 GB。上下文窗口是有限的。没有人会在为时已晚之前回答的问题是：**窗口什么时候会爆？** 这个工具一条命令给你答案。

**你能得到：**

- 窗口利用率（0 → 100%+），绿 / 黄 / 红 / 溢出四级
- **可压缩区间**：按行号给出最早可归档的安全区间
- **前缀缓存提示**：头重 vs 均衡——哪种压缩方式保持活动前缀健康
- 健康分 0–100 与可执行的告警
- Markdown 报告（或 JSON 供流水线）
- 零依赖，纯 Python 3.9+ 标准库

## 安装

## 快速开始

```bash
agent-context-clinic check --file session.jsonl --window 200000
```

```bash
# 跑内置 demo 转录
agent-context-clinic check --demo
```

## 实测输出

```
$ agent-context-clinic check --demo
# Agent Context Clinic Report

- **File**: <demo transcript>
- **Window**: 200,000 tokens
- **Total**: 138 tokens across 5 messages
- **Utilization**: 0.1%
- **Level**: **GREEN**
- **Health score**: 98/100
...
```

## 转录格式

JSONL，每行一条消息：

```json
{"role": "user", "content": "修复登录 bug", "tokens": 234}
{"role": "assistant", "content": "让我看看 auth 模块……", "tokens": 890}
```

`tokens` 可选——缺省时使用保守的 CJK 感知估算。

## 设计不变量

| # | 不变量 | 由谁保证 |
|:--|:--|:--|
| 1 | 0–69% 占用 → 绿 | `_level_for` |
| 2 | 70–89% → 黄（温暖告警） | `_level_for` |
| 3 | 90–99% → 红（紧急告警） | `_level_for` |
| 4 | ≥100% → 溢出（记忆大概率丢失） | `_level_for` |
| 5 | 无有效消息 → 显式告警 | `check_transcript` |
| 6 | token 永不为负，估算至少 ≥1 | `estimate_tokens` |

## 许可证

MIT。