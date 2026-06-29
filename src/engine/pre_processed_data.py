"""Data container that carries request data into optimization strategies.

Defines the boundary between the preprocessing stage and the strategy stage.
Keeping them separate makes each independently extensible.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.request import Request


@dataclass(frozen=True)
class PreProcessedData:
    """Preprocessed data ready for strategy execution.

    Attributes:
        request: The original knapsack request.
    """

    request: Request
