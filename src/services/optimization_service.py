"""Orchestrates the full "solve a knapsack request" workflow.

This is the main entry point that calling code (e.g., a CLI command) uses to
run an optimization. It coordinates loading data, running the solver, and
returning a response, so callers don't need to manage those steps themselves.
"""

import logging

from services.base_data_loader import BaseDataLoader
from services.optimization_response import OptimizationResponse
from engine.orchestrator import Orchestrator

logger = logging.getLogger(__name__)


class OptimizationService:
    """Orchestrates the "load → optimize → respond" pipeline for one request.

    A use case: given a request ID, fetch the data, run the optimization via
    the Orchestrator, and return a response. The service creates the Orchestrator
    internally and coordinates data loading with solving.
    """

    def __init__(self, request_loader: BaseDataLoader) -> None:
        self._request_loader = request_loader
        self._orchestrator = Orchestrator()

    def solve(self, request_id: str) -> OptimizationResponse:
        """Load a request and run the optimization pipeline.

        Args:
            request_id: Identifier of the request to solve.

        Returns:
            An OptimizationResponse with the recommendation or an error message.
        """
        logger.info("Solving request: %s", request_id)

        request = self._request_loader.load(request_id)
        if request is None:
            logger.warning("Request not found: %s", request_id)
            return OptimizationResponse.failure(f"Request '{request_id}' not found")

        recommendation = self._orchestrator.solve(request)
        if recommendation is None:
            logger.warning("No feasible solution for request: %s", request_id)
            return OptimizationResponse.failure("No feasible solution found")

        logger.info("--------- Request %s solved successfully ---------", request_id)
        return OptimizationResponse.success(recommendation)
