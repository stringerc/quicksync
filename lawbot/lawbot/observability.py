"""Structured, one-line JSON logs for LLM calls (Phase 1 observability)."""

from __future__ import annotations

import json
import logging
from typing import Any

_logger = logging.getLogger("lawbot.llm")


def configure_llm_logging() -> None:
    """
    Ensure ``lawbot.llm`` INFO events reach stderr. Uvicorn often sets the root logger to WARNING,
    which would otherwise drop these lines.
    """
    if _logger.handlers:
        _logger.setLevel(logging.INFO)
        return
    h = logging.StreamHandler()
    h.setLevel(logging.INFO)
    h.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(h)
    _logger.setLevel(logging.INFO)
    _logger.propagate = False


def log_llm_event(payload: dict[str, Any]) -> None:
    """Emit a single JSON object on the lawbot.llm logger (parseable by log aggregators)."""
    _logger.info("%s", json.dumps(payload, default=str))
