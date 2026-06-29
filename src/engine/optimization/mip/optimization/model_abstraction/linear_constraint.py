"""Solver-agnostic representation of a linear constraint.

A LinearConstraint expresses: lhs sign rhs, e.g. âˆ‘(w_i Â· qty_i) â‰¤ W.
Pure Python stdlib only â€” no solver dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from engine.optimization.mip.optimization.model_abstraction.linear_expression import LinearExpression


class ConstraintSign(StrEnum):
    """Valid comparison operators for a linear constraint."""

    LEQ = "<="
    GEQ = ">="
    EQ = "="


@dataclass
class LinearConstraint:
    """Named constraint: lhs sign rhs.

    Attributes:
        name: Unique identifier for the constraint (used in solver output).
        lhs: Left-hand side linear expression.
        sign: Comparison operator.
        rhs: Right-hand side scalar value.
    """

    name: str
    lhs: LinearExpression
    sign: ConstraintSign
    rhs: float
