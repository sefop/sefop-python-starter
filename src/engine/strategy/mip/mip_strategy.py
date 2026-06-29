"""Mixed-Integer Programming (MIP) solver for the knapsack problem.

This module contains the exact-optimisation solver. When the problem is small
enough for MIP to solve in a reasonable time, this solver is preferred over
the greedy heuristic because it guarantees an optimal (calorie-maximising)
selection.

It plugs into the system as one of the solver strategies that Orchestrator can
choose between (the other being GreedyCalories).
"""

from __future__ import annotations

import logging

from engine.strategy.base_strategy import BaseOptimizationStrategy
from engine.pre_processed_data import PreProcessedData
from engine.strategy.mip.optimization.optimization import Optimization
from domain.recommendation import Recommendation

logger = logging.getLogger(__name__)


class MipStrategy(BaseOptimizationStrategy):
    """Mixed-Integer Programming Strategy.

    Solves the knapsack problem exactly via linear programming. Accepts
    preprocessed data and returns a recommendation.
    """

    def __init__(self, solver_name: str = "highs") -> None:
        self._optimization = Optimization(solver_name=solver_name)

    def solve(self, data: PreProcessedData) -> Recommendation | None:
        """Run the MIP Strategy.

        Args:
            data: The preprocessed knapsack data.

        Returns:
            The optimal Recommendation, or None if no feasible solution exists.
        """
        recommendation = self._optimization.run(data)
        if recommendation is None:
            logger.warning("MIP found no feasible solution")
            return None
        return recommendation
