"""Contract that every optimization strategy must follow.

Strategies (MIP solver, greedy heuristic, etc.) are pluggable implementations
of this interface so Orchestrator can select and run any of them through a single
``solve()`` call without knowing which one it picked.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from domain.recommendation import Recommendation
from engine.pre_processed_data import PreProcessedData


class BaseOptimizationStrategy(ABC):
    """
    An abstract base class (ABC) is like a contract: it declares a set of
    methods that every solver **must** implement, but says nothing about
    *how*. Any class that inherits from ``BaseOptimizationStrategy`` is forced to provide
    a ``solve()`` method, so Orchestrator can call ``solve()`` without caring
    whether a MIP solver or a greedy heuristic is doing the work behind the
    scenes.
    """

    @abstractmethod
    def solve(self, data: PreProcessedData) -> Recommendation | None:
        """Solve the optimization problem for the given data.

        Args:
            data: The preprocessed knapsack request and related context.

        Returns:
            The best recommendation found, or None if no feasible solution exists.
        """
