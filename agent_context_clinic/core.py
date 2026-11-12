# -*- coding: utf-8 -*-
"""agent-context-clinic — a dependency-free AI session context health check.

Reads a session transcript (JSONL) and reports window saturation, compressible
ranges, cache-friendly estimate, and a human-readable health report.

Core question: "How close is my agent session to losing its memory?"
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

DEFAULT_WINDOW = 200_000
WARN_RATIO = 0.7      # >= 70% → yellow
CRIT_RATIO = 0.9      # >= 90% → red
EXPIRED_RATIO = 1.0   # >= 100% → overflow (context expired)


@dataclass
class SessionMessage:
    seq: int
    role: str
    tokens: int
    size_chars: int = 0


@dataclass
class HealthReport:
    total_tokens: int = 0
    window: int = DEFAULT_WINDOW
    utilization: float = 0.0            # 0..1+
    level: str = "green"                # green | yellow | red | overflow
    score: int = 100
    messages: int = 0
    compressible_tokens: int = 0
    compressible_pct: float = 0.0
    compressible_from: Optional[int] = None
    compressible_to: Optional[int] = None
    cache_hint: str = ""
    warnings: List[str] = field(default_factory=list)
    oldest_messages_before_overflow: int = 0
    file_path: str = ""

    def as_dict(self) -> dict:
        return {
            "file": self.file_path,
            "window": self.window,
            "total_tokens": self.total_tokens,
            "utilization_pct": round(self.utilization * 100, 1),
            "level": self.level,
            "score": self.score,
            "messages": self.messages,
            "compressible_tokens": self.compressible_tokens,
            "compressible_pct": round(self.compressible_pct * 100, 1),
            "compressible_range": [self.compressible_from, self.compressible_to],
            "cache_hint": self.cache_hint,
            "warnings": self.warnings,
        }


# ------------------------------------------------------------------ token estimate
def estimate_tokens(text: str) -> int:
    """Zero-dependency token estimate.

    Rough heuristic: CJK-heavy content costs ~1 token per 1.5 chars;
    latin/code costs ~4 chars per token. Good enough for a health check.
    """
    if not text:
        return 0
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    rest = len(text) - cjk
    return max(1, math.ceil(cjk / 1.5) + math.ceil(rest / 4))


def load_transcript(path: str) -> List[SessionMessage]:
    """Read a JSONL transcript. Each line may be:
      {"role": "...", "content": "...", "tokens": <optional>}
      {"type": "message", "role": "...", "content": "...", "tokens": <optional>}
    Lines without content are skipped.
    """
    messages: List[SessionMessage] = []
    with open(path, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(record, dict):
                continue
            role = str(record.get("role") or record.get("type") or "?")
            content = record.get("content")
            if content is None:
                continue
            if not isinstance(content, str):
                content = json.dumps(content, ensure_ascii=False)
            tokens = record.get("tokens")
            if tokens is None or not isinstance(tokens, (int, float)) or tokens <= 0:
                tokens = estimate_tokens(content)
            messages.append(
                SessionMessage(
                    seq=lineno,
                    role=role,
                    tokens=int(tokens),
                    size_chars=len(content),
                )
            )
    return messages


# ------------------------------------------------------------------ health check
def _level_for(util: float) -> str:
    if util >= EXPIRED_RATIO:
        return "overflow"
    if util >= CRIT_RATIO:
        return "red"
    if util >= WARN_RATIO:
        return "yellow"
    return "green"


def _score_for(util: float) -> int:
    if util >= EXPIRED_RATIO:
        return 0
    if util >= CRIT_RATIO:
        return max(10, int(100 - (util - CRIT_RATIO) * 200))
    if util >= WARN_RATIO:
        return int(100 - (util - WARN_RATIO) * 150)
    return max(85, int(100 - util * 20))


def check_transcript(path: str, window: int = DEFAULT_WINDOW) -> HealthReport:
    messages = load_transcript(path)
    total = sum(m.tokens for m in messages)
    util = total / window if window > 0 else 0.0
    report = HealthReport(
        total_tokens=total,
        window=window,
        utilization=util,
        level=_level_for(util),
        score=_score_for(util),
        messages=len(messages),
        file_path=path,
    )

    # compressible range: earliest messages by age (first 40% by count)
    if messages:
        keep_count = max(1, int(len(messages) * 0.6))
        compressible = messages[: len(messages) - keep_count]
        report.compressible_tokens = sum(m.tokens for m in compressible)
        report.compressible_pct = report.compressible_tokens / total if total else 0.0
        if compressible:
            report.compressible_from = compressible[0].seq
            report.compressible_to = compressible[-1].seq
        else:
            report.compressible_from = 0
            report.compressible_to = 0
        # oldest messages before overflow (room divided by avg token size)
        if util >= WARN_RATIO and messages:
            avg = total / len(messages)
            room = max(0, window - total)
            report.oldest_messages_before_overflow = int(room // avg) if avg else 0

    # cache hint: incremental prefix = healthy; heavy churn at the head = bad
    if messages:
        pct10 = messages[: max(1, len(messages) // 10)]
        first10_tokens = sum(m.tokens for m in pct10)
        if total and first10_tokens / total > 0.5:
            report.cache_hint = (
                "head-heavy session: the first 10% of messages hold >50% of tokens; "
                "compressing the head preserves the live prefix best."
            )
        else:
            report.cache_hint = (
                "reasonably balanced prefix; incremental compaction of the oldest "
                "span keeps prefix-cache friendly."
            )

    # warnings
    if util >= EXPIRED_RATIO:
        report.warnings.append("context window exhausted: the session likely lost memory")
    elif util >= CRIT_RATIO:
        report.warnings.append("near overflow: compress or split the session now")
    elif util >= WARN_RATIO:
        report.warnings.append("getting warm: plan a compaction before the next big task")
    if report.messages == 0:
        report.warnings.append("no parseable messages found; check the transcript format")
    return report


def render_markdown(report: HealthReport) -> str:
    """Render the human-readable health report (the 'clinic' output)."""
    lines = [
        "# Agent Context Clinic Report",
        "",
        f"- **File**: `{report.file_path}`",
        f"- **Window**: {report.window:,} tokens",
        f"- **Total**: {report.total_tokens:,} tokens across {report.messages} messages",
        f"- **Utilization**: {report.utilization * 100:.1f}%",
        f"- **Level**: **{report.level.upper()}**",
        f"- **Health score**: {report.score}/100",
        "",
        "## Compressible range",
        f"- Tokens: {report.compressible_tokens:,} ({report.compressible_pct * 100:.1f}%)",
    ]
    if report.compressible_from and report.compressible_to:
        lines.append(
            f"- Lines {report.compressible_from}–{report.compressible_to} are the oldest "
            f"span safe to archive first"
        )
    lines += ["", "## Cache hint", f"- {report.cache_hint}", "", "## Warnings"]
    if report.warnings:
        for w in report.warnings:
            lines.append(f"- {w}")
    else:
        lines.append("- none — session looks healthy")
    return "\n".join(lines) + "\n"