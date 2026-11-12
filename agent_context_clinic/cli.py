# -*- coding: utf-8 -*-
"""agent-context-clinic — AI 会话上下文健康体检 CLI（零依赖）。

用法示例：

    agent-context-clinic check --file session.jsonl [--window 200000]
    python -m agent_context_clinic check --file session.jsonl --window 128000
"""

from __future__ import annotations

import argparse
import json
import sys

from .core import DEFAULT_WINDOW, check_transcript, render_markdown


def _demo_transcript() -> str:
    """Build a small synthetic transcript to demo the tool."""
    import json as _json

    lines = []
    blobs = [
        ("user", "Fix the login bug in auth.py and update tests."),
        ("assistant", "Let me look at the auth module first. I see the token refresh "
                      "logic and the middleware chain; the bug is likely a stale "
                      "refresh token being cached after expiry."),
        ("user", "Good. Also add a rate limiter and make sure the API stays "
                 "backward compatible with v1."),
        ("assistant", "Implemented RateLimiter with a fixed window, wired the "
                      "middleware, and kept the old endpoint signatures. All 42 "
                      "unit tests pass locally; I am running the integration suite "
                      "next."),
        ("user", "Ship it when green, then open a PR and summarize the change."),
    ]
    for seq, (role, content) in enumerate(blobs, 1):
        lines.append(_json.dumps({"role": role, "content": content}, ensure_ascii=False))
    return "\n".join(lines) + "\n"


def cmd_check(args: argparse.Namespace) -> int:
    if args.demo:
        import tempfile

        with tempfile.NamedTemporaryFile(
            "w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as fh:
            fh.write(_demo_transcript())
            path = fh.name
        report = check_transcript(path, window=args.window)
        report.file_path = "<demo transcript>"
    else:
        if not args.file:
            print("error: --file is required (or use --demo)", file=sys.stderr)
            return 2
        report = check_transcript(args.file, window=args.window)

    if args.json:
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
        return 0
    print(render_markdown(report))
    if args.demo and path:
        import os

        os.unlink(path)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="agent-context-clinic",
        description="AI session context health check — how close to memory loss?",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="check a session transcript")
    check.add_argument("--file", help="path to a JSONL transcript")
    check.add_argument("--window", type=int, default=DEFAULT_WINDOW,
                       help="context window size in tokens (default %(default)s)")
    check.add_argument("--json", action="store_true", help="output JSON instead of markdown")
    check.add_argument("--demo", action="store_true", help="run the built-in demo transcript")
    check.set_defaults(func=cmd_check)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())