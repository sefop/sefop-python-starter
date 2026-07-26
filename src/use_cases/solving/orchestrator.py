"""Orchestrates the knapsack optimization pipeline.

The Orchestrator is the public face of the solve use cases' internal solving
pipeline (see the package docstring convention: this whole `solving/`
subpackage is an implementation detail of `SolveSingleRequest`, not a
top-level architecture layer). Given a Request, it runs three explicit
stages: preprocessing -> strategy selection and solving -> postprocessing.
Returns a Recommendation or None. Callers never need to know which strategy
was chosen or how preprocessing/postprocessing work.

Key design: strategy selection is based on problem size. Small problems (at
most max_products_for_mip products) use the exact MIP solver; larger
problems use the fast greedy heuristic. This selection is hidden from callers.
"""

from __future__ import annotations

import logging
from pathlib import Path

from domain.recommendation import Recommendation
from domain.request import Request
from use_cases.solving.optimization.heuristic.greedy_calories import GreedyCalories
from use_cases.solving.optimization.mip.mip_strategy import MipStrategy
from use_cases.solving.optimization.optimization_strategy import OptimizationStrategy
from use_cases.solving.postprocessing.postprocessing import PostProcess
from use_cases.solving.preprocessing.pre_processed_data import PreProcessedData
from use_cases.solving.preprocessing.preprocessing import PreProcess

logger = logging.getLogger(__name__)


class Orchestrator:
    """Selects and runs the appropriate optimization strategy for a Request.

    The Orchestrator is not itself a strategy, it coordinates the available
    strategies. Callers give the Orchestrator a request, and it silently
    picks the right solver based on problem size. Every collaborator
    (preprocessing, postprocessing, and both strategies) is
    constructor-injected (Dependency Injection) rather than built here, so a
    fork can swap any stage — or test this class with fakes — without
    editing this file.
    """

    def __init__(
        self,
        preprocessing: PreProcess,
        postprocessing: PostProcess,
        mip_strategy: MipStrategy,
        heuristic_strategy: GreedyCalories,
        max_products_for_mip: int = 50,
    ) -> None:
        self._preprocessing = preprocessing
        self._postprocessing = postprocessing
        self._mip_strategy = mip_strategy
        self._heuristic_strategy = heuristic_strategy
        # Problems with at most this many products are solved with MIP
        # (exact). Larger problems are routed to the greedy heuristic for
        # speed. A constructor default, not global Settings: this threshold
        # is an implementation detail of how the Orchestrator picks a
        # strategy, not something a data scientist configures per run.
        self._max_products_for_mip = max_products_for_mip

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
        optimization_strategy: OptimizationStrategy = self._select_strategy(data)
        result = optimization_strategy.solve(data, output_dir)
        if result is None:
            return None
        return self._postprocessing.run(result)

    def _select_strategy(self, data: PreProcessedData) -> OptimizationStrategy:
        """Choose MIP or greedy based on the number of feasible products.

        Using feasible_products (not request.products) reflects the actual
        problem size after preprocessing: infeasible products were already
        removed and will not appear in the model.

        Args:
            data: The preprocessed data to evaluate.

        Returns:
            The strategy instance to use.
        """
        if len(data.feasible_products) <= self._max_products_for_mip:
            return self._mip_strategy
        return self._heuristic_strategy
