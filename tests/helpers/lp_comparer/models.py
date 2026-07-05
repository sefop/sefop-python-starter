"""Data models for LP file comparison results.

Defines the structured output produced by the comparer so that callers
can filter, format, or assert on specific difference categories without
parsing free-text messages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class LpDifference:
    """Represents a single semantic difference between two LP models.

    Attributes:
        category: Broad category of the difference. One of "model",
            "variable", "objective", or "constraint".
        diff_type: Nature of the difference. One of "missing", "extra",
            or "modified".
        name: Name of the entity that differs (variable, constraint, or
            objective name; empty string for model-level differences).
        detail: Human-readable description of the difference.
        expected: The expected value for a "modified" diff; ``None`` for
            "missing" / "extra" diffs.
        actual: The actual value for a "modified" diff; ``None`` for
            "missing" / "extra" diffs.
    """

    category: str
    diff_type: str
    name: str
    detail: str
    expected: Any = None
    actual: Any = None
