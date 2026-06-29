"""Abstract interface that every solver implementation must satisfy.

The optimization orchestrator in ``optimization.py`` talks to solvers only
through this interface. That means you can swap HiGHS for any future solver
without changing the optimization logic â€” just provide a new subclass.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from engine.optimization_strategy.mip.optimization.model_abstraction.model_solution import ModelSolution
from engine.optimization_strategy.mip.optimization.model_abstraction.optimization_model import OptimizationModel


class BaseTechnologySolver(ABC):
    """Base class for solver technology implementations.

    Think of this as a *contract* (formally, an Abstract Base Class / ABC):
    it declares that every solver implementation **must** provide a
    ``solve(model)`` method, but it contains no solving logic itself. This
    lets the optimization code call ``solver.solve(model)`` without knowing
    or caring whether the underlying engine is HiGHS, Xpress, or something else.

    To add a new solver, subclass this class and implement ``solve``.
    """

    @abstractmethod
    def solve(self, model: OptimizationModel) -> ModelSolution:
        """Solve the given model and return a solution.

        Args:
            model: The solver-agnostic optimization model to solve.

        Returns:
            A ModelSolution with status and variable values (or None if infeasible).
        """
