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

from engine.strategy.base_strategy import BaseOptimizationStrategy
from engine.preprocessing import PreProcess
from engine.postprocessing import PostProcess
from engine.strategy.heuristic.greedy_calories import GreedyCalories
from engine.strategy.mip.mip_strategy import MipStrategy
from domain.recommendation import Recommendation
from domain.request import Request

logger = logging.getLogger(__name__)

# Problems with at most this many products are solved with MIP (exact).
# Larger problems are routed to the greedy heuristic for speed.
MAX_PRODUCTS_FOR_MIP = 50


class Orchestrator:
    """Selects and runs the appropriate optimization strategy for a Request.

    The Orchestrator is not itself a strategy, it coordinates the available
    strategies. Callers give the Orchestrator a request, and it silently picks
    the right solver based on problem size. The three stages (preprocessing,
    strategy selection, postprocessing) are coordinated here.
    """

    def __init__(self, max_products_for_mip: int = MAX_PRODUCTS_FOR_MIP) -> None:
        """Initialize with both strategy implementations available.

        Args:
            max_products_for_mip: Threshold above which the greedy heuristic
                is used instead of the (slower) MIP solver. Exposed for testing.
        """
        self._preprocessing = PreProcess()
        self._postprocessing = PostProcess()
        self._heuristic = GreedyCalories()
        self._mip = MipStrategy()
        self._max_products_for_mip = max_products_for_mip

    def solve(self, request: Request) -> Recommendation | None:
        """Run the full optimization pipeline.

        Args:
            request: The knapsack request to solve.

        Returns:
            The best Recommendation found, or None if no feasible solution exists.
        """
        data = self._preprocessing.run(request)
        strategy = self._select_strategy(request)
        logger.info(
            "Selected %s for %d products",
            type(strategy).__name__,
            len(request.products),
        )
        result = strategy.solve(data)
        if result is None:
            return None
        return self._postprocessing.run(result)

    def _select_strategy(self, request: Request) -> BaseOptimizationStrategy:
        """Choose MIP or greedy based on problem size.

        Args:
            request: The request to evaluate.

        Returns:
            The strategy instance to use.
        """
        if len(request.products) <= self._max_products_for_mip:
            return self._mip
        return self._heuristic
