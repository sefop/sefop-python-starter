"""Calorie-maximisation objective for the knapsack MIP model.

Pure Python stdlib only — no solver dependency.
"""

from __future__ import annotations

from engine.strategy.mip.optimization.model_abstraction.linear_expression import LinearExpression
from domain.request import Request

# Scaling factor for the calorie term in the objective function.
# At 1.0, calories are measured as raw kcal. Adjust to tune relative importance
# if additional objective terms are added in future.
CALORIES_WEIGHT = 1.0


class ObjectiveCalories:
    """Objective function that maximises total calories:

        α · ∑(i) calories_i · qty_i

    Where qty_i is the number of units of product i selected and
    α is CALORIES_WEIGHT (1.0).
    """

    def build_expression(self, request: Request) -> LinearExpression:
        """Build the calorie objective expression.

        Args:
            request: The knapsack request containing the product catalogue.

        Returns:
            A LinearExpression to be maximised by the solver.
        """
        expr = LinearExpression()
        for p in request.products:
            expr.add(CALORIES_WEIGHT * p.calories, p.name)
        return expr
