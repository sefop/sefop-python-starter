"""Budget capacity constraint for the knapsack MIP model.

Pure Python stdlib only â€” no solver dependency.
"""

from __future__ import annotations

from engine.optimization.mip.optimization.model_abstraction.linear_constraint import ConstraintSign, LinearConstraint
from engine.optimization.mip.optimization.model_abstraction.linear_expression import LinearExpression
from domain.request import Request


class ConstraintLimitBudget:
    """Total cost of selected products must not exceed the budget:

        âˆ‘(i) price_i Â· qty_i â‰¤ max_budget_usd

    Where qty_i is the number of units of product i selected.
    """

    def build(self, request: Request) -> LinearConstraint:
        """Build the budget constraint for the given request.

        Args:
            request: The knapsack request containing products and budget limit.

        Returns:
            A LinearConstraint representing the budget capacity bound.
        """
        lhs = LinearExpression()
        for p in request.products:
            lhs.add(p.price_usd, p.name)
        return LinearConstraint(name="budget_limit", lhs=lhs, sign=ConstraintSign.LEQ, rhs=request.max_budget_usd)
