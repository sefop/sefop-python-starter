"""Preprocessing stage that prepares request data for optimization strategies.

Domain validation (Request.__post_init__) already guarantees that each product
has positive weight, price, and calories and that names are unique. Preprocessing
goes one step further: it removes products that can never appear in any solution,
for two distinct reasons:

1. *Individually infeasible* — a single unit of the product already exceeds
   either the weight capacity or the budget. No strategy — exact or heuristic —
   could ever select such a product.
2. *Policy-prohibited* — the product has 20 calories or less. This is a fixed
   business rule (low-calorie products add no nutritional value worth
   recommending), independent of whether the product would otherwise fit.

Filtering both kinds out here, before any strategy runs, shrinks the problem
and guarantees the rule applies uniformly regardless of which strategy
(MipStrategy or the GreedyCalories heuristic) ends up solving the request.
"""

from __future__ import annotations

from engine.preprocessing.pre_processed_data import PreProcessedData
from domain.request import Request

# Products with this many calories or fewer are prohibited from every
# recommendation, regardless of how attractive their price or weight is.
# This is a fixed business rule, not a user-configurable setting.
MIN_CALORIES_ALLOWED = 20


class PreProcess:
    """Preprocessing step before strategy execution.

    Filters out products that are individually infeasible or policy-prohibited,
    then wraps the remaining data in PreProcessedData for the strategy stage.
    """

    def run(self, request: Request) -> PreProcessedData:
        """Filter excluded products and prepare data for the strategy stage.

        A product is excluded when either:
        - it is infeasible: a single unit costs more than the total budget or
          weighs more than the total weight capacity, so it can never be
          included in any valid solution; or
        - it is policy-prohibited: it has MIN_CALORIES_ALLOWED calories or
          fewer, so it is never worth recommending regardless of fit.

        Args:
            request: The validated knapsack request.

        Returns:
            PreProcessedData with feasible_products containing only the
            products that both physically fit within the constraints and
            satisfy the minimum-calorie policy.
        """
        feasible_products = [
            p
            for p in request.products
            if p.price_usd <= request.max_budget_usd and p.weight_kg <= request.max_weight_kg
            # "20 calories or less" is prohibited, so the boundary is exclusive:
            # a product must have strictly more than MIN_CALORIES_ALLOWED to survive.
            and p.calories > MIN_CALORIES_ALLOWED
        ]
        return PreProcessedData(request=request, feasible_products=feasible_products)
