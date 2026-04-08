"""Load Hermes golden fixtures from ``eval/goldens/cases/*.json``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
CASES_DIR = REPO_ROOT / "eval" / "goldens" / "cases"
GOLDENS_DIR = REPO_ROOT / "eval" / "goldens"
TAXONOMY_PATH = GOLDENS_DIR / "matrix_taxonomy.json"
RUNS_DIR = REPO_ROOT / "eval" / "runs"

__all__ = ["CASES_DIR", "GOLDENS_DIR", "REPO_ROOT", "RUNS_DIR", "TAXONOMY_PATH", "load_golden_cases"]


def load_golden_cases() -> list[dict[str, Any]]:
    """Return golden case dicts with ``_path`` set to the source file."""
    if not CASES_DIR.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for p in sorted(CASES_DIR.glob("*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            raise RuntimeError(f"golden load failed: {p}: {e}") from e
        if not isinstance(data, dict):
            raise RuntimeError(f"golden must be object: {p}")
        data["_path"] = str(p)
        out.append(data)
    return out
