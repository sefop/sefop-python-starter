"""Calorie-maximisation objective for the knapsack MIP model.

Pure Python stdlib only — no solver dependency.
"""

from __future__ import annotations

from collections.abc import Callable

from engine.optimization.mip.optimization.model_abstraction.linear_expression import LinearExpression
from domain.request import Request

# Scaling factor for the calorie term in the objective function.
# At 1.0, calories are measured as raw kcal. Adjust to tune relative importance
# if additional objective terms are added in future.
CALORIES_WEIGHT = 1.0


class ObjectiveCalories:
    """Objective function that maximises total calories:

        α · ∑(i) calories_i · x_i

    Where x_i is the number of units of product i selected and
    α is CALORIES_WEIGHT (1.0).
    """

    def build_expression(self, request: Request, name_fn: Callable[[str], str] = lambda name: name) -> LinearExpression:
        """Build the calorie objective expression.

        Args:
            request: The knapsack request containing the product catalogue.
            name_fn: Transforms a product name into the matching decision
                variable's name. Defaults to the identity function; must match
                whatever name_fn was used to build the variables themselves,
                or the solver won't be able to find the referenced column.

        Returns:
            A LinearExpression to be maximised by the solver.
        """
        expr = LinearExpression()
        for p in request.products:
            expr.add(CALORIES_WEIGHT * p.calories, name_fn(p.name))
        return expr
