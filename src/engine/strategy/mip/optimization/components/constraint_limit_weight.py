"""Weight capacity constraint for the knapsack MIP model.

Pure Python stdlib only — no solver dependency.
"""

from __future__ import annotations

from engine.strategy.mip.optimization.model_abstraction.linear_constraint import ConstraintSign, LinearConstraint
from engine.strategy.mip.optimization.model_abstraction.linear_expression import LinearExpression
from domain.request import Request


class ConstraintLimitWeight:
    """Total weight of selected products must not exceed the weight limit:

        ∑(i) weight_i · qty_i ≤ max_weight_kg

    Where qty_i is the number of units of product i selected.
    """

    def build(self, request: Request) -> LinearConstraint:
        """Build the weight constraint for the given request.

        Args:
            request: The knapsack request containing products and weight limit.

        Returns:
            A LinearConstraint representing the weight capacity bound.
        """
        lhs = LinearExpression()
        for p in request.products:
            lhs.add(p.weight_kg, p.name)
        return LinearConstraint(name="weight_limit", lhs=lhs, sign=ConstraintSign.LEQ, rhs=request.max_weight_kg)
