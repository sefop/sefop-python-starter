"""Mixed-Integer Programming (MIP) solving strategy for the knapsack problem.

This module contains the exact-optimization solver. When the problem is small
enough for MIP to solve in a reasonable time, this strategy is preferred over
the greedy heuristic because it guarantees an optimal selection.

It plugs into the system as one of the strategies that Orchestrator can
choose between (the other being GreedyCalories).
"""

from __future__ import annotations

import logging
from pathlib import Path

from domain.recommendation import Recommendation
from use_cases.solving.optimization.mip.optimization.optimization import Optimization
from use_cases.solving.optimization.optimization_strategy import OptimizationStrategy
from use_cases.solving.preprocessing.pre_processed_data import PreProcessedData

logger = logging.getLogger(__name__)


class MipStrategy(OptimizationStrategy):
    """Mixed-Integer Programming Strategy.

    Solves the knapsack problem exactly. The Optimization instance that builds
    and solves the model is constructor-injected (Dependency Injection) rather
    than built here, so which solver technology it delegates to is a choice
    made once at the composition root (bootstrap.py), not by this class.
    """

    def __init__(self, optimization: Optimization) -> None:
        self._optimization = optimization

    def solve(self, data: PreProcessedData, output_dir: Path | None = None) -> Recommendation | None:
        """Run the MIP Strategy.

        Args:
            data: The preprocessed knapsack data.
            output_dir: Directory to write the HiGHS model's LP dump into, or
                None to skip writing it. Forwarded to Optimization.run().

        Returns:
            The optimal Recommendation, or None if no feasible solution exists.
        """
        recommendation = self._optimization.run(data, output_dir)
        if recommendation is None:
            logger.warning("MIP found no feasible solution")
            return None
        return recommendation
