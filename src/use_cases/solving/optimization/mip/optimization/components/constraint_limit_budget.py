"""Budget capacity constraint for the knapsack MIP model.

Pure Python stdlib only — no solver dependency.
"""

from __future__ import annotations

from collections.abc import Callable

from domain.request import Request
from use_cases.solving.optimization.mip.optimization.model_abstraction.linear_constraint import (
    ConstraintSign,
    LinearConstraint,
)
from use_cases.solving.optimization.mip.optimization.model_abstraction.linear_expression import LinearExpression


class ConstraintLimitBudget:
    """Total cost of selected products must not exceed the budget:

        ∑(i) price_i · x_i ≤ max_budget_usd

    Where x_i is the number of units of product i selected.
    """

    def build(self, request: Request, name_fn: Callable[[str], str] = lambda name: name) -> LinearConstraint:
        """Build the budget constraint for the given request.

        Args:
            request: The knapsack request containing products and budget limit.
            name_fn: Transforms a product name into the matching decision
                variable's name. Defaults to the identity function; must match
                whatever name_fn was used to build the variables themselves,
                or the solver won't be able to find the referenced column.

        Returns:
            A LinearConstraint representing the budget capacity bound.
        """
        lhs = LinearExpression()
        for p in request.products:
            lhs.add(p.price_usd, name_fn(p.name))
        return LinearConstraint(name="budget_limit", lhs=lhs, sign=ConstraintSign.LEQ, rhs=request.max_budget_usd)
