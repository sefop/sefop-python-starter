"""Solver-agnostic representation of a linear constraint.

A LinearConstraint expresses: lhs sign rhs, e.g. ∑(w_i · x_i) ≤ W.
Pure Python stdlib only — no solver dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from use_cases.solving.optimization.mip.optimization.model_abstraction.linear_expression import LinearExpression


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
            Must contain only letters, digits, and underscores; this is
            enforced once, when the constraint is assembled into an
            ``OptimizationModel``, not here.
        lhs: Left-hand side linear expression.
        sign: Comparison operator.
        rhs: Right-hand side scalar value.
    """

    name: str
    lhs: LinearExpression
    sign: ConstraintSign
    rhs: float
