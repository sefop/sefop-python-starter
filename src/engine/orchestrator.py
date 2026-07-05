"""Orchestrates the knapsack optimization pipeline.

The Orchestrator is the public face of the optimization package. Given a Request,
it orchestrates three explicit stages: preprocessing → strategy selection and
solving → postprocessing. Returns a Recommendation or None. Callers never need
to know which strategy was chosen or how preprocessing/postprocessing work.

Key design: strategy selection is based on problem size. Small problems (≤50
products) use the exact MIP solver; larger problems use the fast greedy
heuristic. This selection is hidden from callers.
"""

from __future__ import annotations

import logging
from pathlib import Path

from engine.optimization.optimization_strategy import OptimizationStrategy
from engine.preprocessing.pre_processed_data import PreProcessedData
from engine.preprocessing.preprocessing import PreProcess
from engine.postprocessing.postprocessing import PostProcess
from engine.optimization.heuristic.greedy_calories import GreedyCalories
from engine.optimization.mip.mip_strategy import MipStrategy
from domain.recommendation import Recommendation
from domain.request import Request

logger = logging.getLogger(__name__)

# Problems with at most this many products are solved with MIP (exact).
# Larger problems are routed to the greedy heuristic for speed.
MAX_PRODUCTS_FOR_MIP = 50


def _select_strategy(data: PreProcessedData) -> OptimizationStrategy:
    """Choose MIP or greedy based on the number of feasible products.

    Using feasible_products (not request.products) reflects the actual problem
    size after preprocessing: infeasible products were already removed and will
    not appear in the model.

    Args:
        data: The preprocessed data to evaluate.

    Returns:
        The strategy instance to use.
    """
    if len(data.feasible_products) <= MAX_PRODUCTS_FOR_MIP:
        return MipStrategy()
    return GreedyCalories()


class Orchestrator:
    """Selects and runs the appropriate optimization strategy for a Request.

    The Orchestrator is not itself a strategy, it coordinates the available
    strategies. Callers give the Orchestrator a request, and it silently picks
    the right solver based on problem size. The three stages (preprocessing,
    strategy selection, postprocessing) are coordinated here.
    """

    def __init__(self) -> None:
        self._preprocessing = PreProcess()
        self._postprocessing = PostProcess()

    def solve(self, request: Request, output_dir: Path | None = None) -> Recommendation | None:
        """Run the full optimization pipeline.

        Args:
            request: The knapsack request to solve.
            output_dir: Directory to write solver debugging artifacts into,
                or None to skip writing any. Forwarded to whichever strategy
                is selected; ignored by strategies that produce none.

        Returns:
            The best Recommendation found, or None if no feasible solution exists.
        """
        data = self._preprocessing.run(request)
        if not data.feasible_products:
            # Every product costs more than the budget or weighs more than the
            # capacity, so no valid selection exists.
            logger.warning("No feasible products after preprocessing; skipping solve")
            return None
        optimization_strategy: OptimizationStrategy = _select_strategy(data)
        result = optimization_strategy.solve(data, output_dir)
        if result is None:
            return None
        return self._postprocessing.run(result)
