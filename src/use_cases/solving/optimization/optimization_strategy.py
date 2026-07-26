"""Contract that every optimization strategy must follow.

Strategies (MIP solver, greedy heuristic, etc.) are pluggable implementations
of this interface so Orchestrator can select and run any of them through a single
``solve()`` call without knowing which one it picked.

This is an internal solving-strategy contract, not a public port: it lives
inside use_cases/solving/ because only the solving pipeline's own collaborators
(Orchestrator, MipStrategy, GreedyCalories) ever implement or call it — it is
not something adapters/ or bootstrap.py wire in from the outside the way
use_cases/ports/ contracts are.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from domain.recommendation import Recommendation
from use_cases.solving.preprocessing.pre_processed_data import PreProcessedData


class OptimizationStrategy(ABC):
    """
    An abstract base class (ABC) is like a contract: it declares a set of
    methods that every solver **must** implement, but says nothing about
    *how*. Any class that inherits from ``BaseOptimizationStrategy`` is forced to provide
    a ``solve()`` method, so Orchestrator can call ``solve()`` without caring
    whether a MIP solver or a greedy heuristic is doing the work behind the
    scenes.
    """

    @abstractmethod
    def solve(self, data: PreProcessedData, output_dir: Path | None = None) -> Recommendation | None:
        """Solve the optimization problem for the given data.

        Args:
            data: The preprocessed knapsack request and related context.
            output_dir: Directory to write solver debugging artifacts into,
                or None to skip writing any. Strategies that produce no such
                artifacts (e.g. the greedy heuristic) simply ignore this.

        Returns:
            The best recommendation found, or None if no feasible solution exists.
        """
