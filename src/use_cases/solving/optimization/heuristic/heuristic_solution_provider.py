"""Greedy heuristic that maximizes calories for a knapsack request.

Products are ranked by calorie density (calories per kg). The algorithm
works through the ranked list and takes as many units of each product as
the remaining weight and budget allow.
"""

from __future__ import annotations

from math import floor
from pathlib import Path

from domain.recommendation import Recommendation
from use_cases.solving.optimization.solution_provider import SolutionProvider
from use_cases.solving.preprocessing.pre_processed_data import PreProcessedData


class HeuristicSolutionProvider(SolutionProvider):
    """Greedy knapsack solver that prioritizes calorie-dense products.

    This is a *heuristic* — it does not guarantee the mathematically
    optimal solution, but it runs in linear time and produces good results
    in practice for the calorie-maximization objective.
    """

    def solve(self, data: PreProcessedData, output_dir: Path | None = None) -> Recommendation | None:
        """Greedily select products ranked by calories per kg.

        Args:
            data: The preprocessed knapsack data with products and constraints.
            output_dir: Unused. This heuristic builds no solver model, so it
                has no debugging artifact to write; the parameter exists only
                to satisfy the shared SolutionProvider interface.

        Returns:
            The single Recommendation found, or None if no product fits
            within the weight and budget constraints.
        """
        request = data.request
        sorted_products = sorted(
            data.feasible_products,
            key=lambda p: p.calories / p.weight_kg,
            reverse=True,
        )

        remaining_weight = request.max_weight_kg
        remaining_budget = request.max_budget_usd
        quantities: dict = {}

        for product in sorted_products:
            max_by_weight = floor(remaining_weight / product.weight_kg)
            max_by_budget = floor(remaining_budget / product.price_usd)
            qty = min(max_by_weight, max_by_budget)
            if qty >= 1:
                quantities[product] = qty
                remaining_weight -= qty * product.weight_kg
                remaining_budget -= qty * product.price_usd

        if not quantities:
            return None

        return Recommendation(request=request, quantities=quantities)
