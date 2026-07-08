"""Data container that carries request data into optimization strategies.

Defines the boundary between the preprocessing stage and the strategy stage.
Keeping them separate makes each independently extensible.
"""

from __future__ import annotations
from dataclasses import dataclass
from domain.product import Product
from domain.request import Request


@dataclass(frozen=True)
class PreProcessedData:
    """Preprocessed data ready for strategy execution.

    Attributes:
        request: The original knapsack request.
        feasible_products: Products where a single unit fits within both the
            weight and budget constraints, and whose calories exceed the
            minimum-calorie policy threshold (see MIN_CALORIES_ALLOWED in
            engine.preprocessing.preprocessing). Strategies should iterate
            this list instead of request.products to avoid wasting effort on
            products that can never be selected.
    """

    request: Request
    feasible_products: list[Product]
