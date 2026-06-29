"""Preprocessing stage that prepares request data for optimization strategies.

All products are already validated by the domain layer (Request.__post_init__
ensures positive weight, price, and calories and no duplicates), so
preprocessing is a pass-through. This stage exists as an extension point:
override PreProcess.run() to add enrichment or custom filtering without
touching the optimizer.
"""

from __future__ import annotations

from engine.pre_processed_data import PreProcessedData
from domain.request import Request


class PreProcess:
    """Preprocessing step before strategy execution.

    Default implementation: wrap the request in PreProcessedData unchanged.
    Override to add data enrichment, filtering, or parameter tuning.
    """

    def run(self, request: Request) -> PreProcessedData:
        """Wrap the request for the optimization stage.

        Args:
            request: The validated knapsack request.

        Returns:
            PreProcessedData containing the request.
        """
        return PreProcessedData(request=request)
