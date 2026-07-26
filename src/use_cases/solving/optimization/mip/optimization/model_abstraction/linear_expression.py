"""Solver-agnostic representation of a linear expression.

A LinearExpression is a weighted sum of named variables: ∑(coefficient_i · variable_i).
It contains no solver dependency — pure Python stdlib only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# Absolute tolerance for treating an accumulated coefficient as zero.
# math.isclose()'s default abs_tol is 0.0, so isclose(x, 0.0) only matches an
# exact zero unless abs_tol is set explicitly (its relative tolerance scales
# with the compared values, which collapses to zero once one side is 0.0).
# This constant fills that gap so a coefficient that cancels out via
# floating-point addition (e.g. 0.1 + 0.2 - 0.3) is still recognized as zero.
_ZERO_TOLERANCE = 1e-9


@dataclass
class LinearExpression:
    """Weighted sum of named decision variables.

    Build incrementally with ``add()``. The ``terms`` property returns a
    snapshot that is safe to iterate without risk of external mutation.
    """

    _terms: dict[str, float] = field(default_factory=dict, init=False, repr=False)

    def add(self, coefficient: float, variable_name: str) -> None:
        """Add a term to the expression, accumulating if the variable already exists.

        If the accumulated coefficient becomes (approximately) zero the term
        is removed, keeping the expression minimal.

        Args:
            coefficient: Scalar weight for the variable.
            variable_name: Name of the decision variable.
        """
        new_value = self._terms.get(variable_name, 0.0) + coefficient
        if math.isclose(new_value, 0.0, abs_tol=_ZERO_TOLERANCE):
            self._terms.pop(variable_name, None)
        else:
            self._terms[variable_name] = new_value

    @property
    def terms(self) -> dict[str, float]:
        """Return a copy of the variable → coefficient mapping."""
        return dict(self._terms)
