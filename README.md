# agent-context-clinic

> **你的 AI 会话还有多久会失忆？**  
> A zero-dependency context-window health check for long agent sessions.

```bash
pip install agent-context-clinic       # zero deps, Python 3.9+
```

<a href="https://gitcode.com/gcw_MKhSyoGN/agent-context-clinic"><img src="https://img.shields.io/badge/GitCode-gcw_MKhSyoGN%2Fagent-context-clinic-blue" alt="GitCode"></a>
<a href="https://github.com/langarden/agent-context-clinic"><img src="https://img.shields.io/badge/GitHub-langarden%2Fagent-context-clinic-black" alt="GitHub"></a>
<img src="https://img.shields.io/badge/tests-15%20passed-green" alt="tests">
<img src="https://img.shields.io/badge/license-MIT-yellow" alt="license">
<img src="https://img.shields.io/badge/python-3.9%2B-blue" alt="python">

`agent-context-clinic` reads a session transcript and tells you **how close you are to losing the conversation** — window saturation, safest compressible span, prefix-cache hint, and a human-readable report. Part of the **Verifiable-agent family**.

> ⚠️ **Research prototype — AI-assisted development.** This is an open-source
> research/experimental prototype produced with AI assistance. It is provided
> **AS IS**, without warranty of any kind, and is not a commercial or
> production-grade product. Use at your own risk.

## Verifiable-agent family

| Repo | Role |
|:--|:--|
| **agent-context-clinic** | context-window **health check** (this repo) |
| [agent-call-audit](https://gitcode.com/gcw_MKhSyoGN/agent-call-audit) | audit **engine** |
| [agent-memory-ledger](https://gitcode.com/gcw_MKhSyoGN/agent-memory-ledger) | verifiable **memory** layer |
| [agent-audit-gateway](https://gitcode.com/gcw_MKhSyoGN/agent-audit-gateway) | HTTP **gateway** |
| [agent-route-grid](https://gitcode.com/gcw_MKhSyoGN/agent-route-grid) | audited multi-agent **routing** |

## Why

You have been running Claude Code / Codex / Cursor / a custom agent on a long task for days. Your session transcript is gigabytes of "stuff". The context window is finite. The question nobody answers until it is too late is: **when will the window blow up?** This tool gives you the answer in one command.

**What you get:**

- Window utilization (0 → 100%+), with green / yellow / red / overflow levels.
- **Compressible range**: the oldest span safe to archive first (by line numbers).
- **Prefix-cache hint**: head-heavy vs balanced — which compaction keeps the live prefix healthy.
- Health score 0–100 and actionable warnings.
- Markdown report (or JSON for pipelines).
- Zero dependencies, pure Python 3.9+ stdlib.

## Install

```bash
pip install agent-context-clinic
```

## Quick start

```bash
agent-context-clinic check --file session.jsonl --window 200000
```

```bash
# Try the built-in demo transcript
agent-context-clinic check --demo
```

## Proof of life

```
$ agent-context-clinic check --demo
# Agent Context Clinic Report

- **File**: <demo transcript>
- **Window**: 200,000 tokens
- **Total**: 138 tokens across 5 messages
- **Utilization**: 0.1%
- **Level**: **GREEN**
- **Health score**: 98/100

## Compressible range
- Tokens: 0 (0.0%)
- Lines 0–0 are the oldest span safe to archive first

## Cache hint
- reasonably balanced prefix; incremental compaction of the oldest
  span keeps prefix-cache friendly.

## Warnings
- none — session looks healthy
```

## Transcript format

JSONL, one message per line:

```json
{"role": "user", "content": "Fix the login bug", "tokens": 234}
{"role": "assistant", "content": "Let me look at the auth module ...", "tokens": 890}
```

`tokens` is optional — when omitted, a conservative CJK-aware estimate is used.

## Invariants

| # | Invariant | Enforced by |
|:--|:--|:--|
| 1 | 0–69% utilization → green | `_level_for` |
| 2 | 70–89% → yellow with warm warning | `_level_for` |
| 3 | 90–99% → red with urgent warning | `_level_for` |
| 4 | ≥100% → overflow (memory likely lost) | `_level_for` |
| 5 | No parseable messages → explicit warning | `check_transcript` |
| 6 | Tokens never negative, estimate always ≥1 | `estimate_tokens` |

## License

MIT. [中文版](docs/README.zh-CN.md)