# -*- coding: utf-8 -*-
"""agent-context-clinic — public surface."""

from .core import (
    DEFAULT_WINDOW,
    HealthReport,
    SessionMessage,
    check_transcript,
    estimate_tokens,
    load_transcript,
    render_markdown,
)
from .cli import main

__version__ = "0.1.0"

__all__ = [
    "HealthReport",
    "SessionMessage",
    "check_transcript",
    "estimate_tokens",
    "load_transcript",
    "render_markdown",
    "DEFAULT_WINDOW",
    "main",
    "__version__",
]