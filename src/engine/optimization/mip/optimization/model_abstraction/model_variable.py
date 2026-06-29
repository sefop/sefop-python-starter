"""Solver-agnostic representation of a decision variable.

Pure Python stdlib only — no solver dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class VarType(StrEnum):
    """Valid integrality types for a decision variable."""

    INTEGER = "integer"
    BINARY = "binary"
    CONTINUOUS = "continuous"


@dataclass
class ModelVariable:
    """A single decision variable in the optimization model.

    Attributes:
        name: Unique identifier used to reference the variable in expressions.
        var_type: Integrality type of the variable.
        lower_bound: Minimum allowed value (default 0.0).
        upper_bound: Maximum allowed value; ``None`` means unbounded.
    """

    name: str
    var_type: VarType
    lower_bound: float = 0.0
    upper_bound: float | None = None
