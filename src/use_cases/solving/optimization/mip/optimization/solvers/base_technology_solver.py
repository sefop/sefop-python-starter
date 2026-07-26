"""Abstract interface that every solver implementation must satisfy.

The optimization orchestrator in ``optimization.py`` talks to solvers only
through this interface. That means you can swap HiGHS for any future solver
without changing the optimization logic — just provide a new subclass.

This is an internal solving-strategy contract, not a public port: it lives
inside use_cases/solving/ because only Optimization ever calls it, and only
bootstrap.py's build_solver() ever picks a concrete implementation of it —
it is not something adapters/ implements the way use_cases/ports/ contracts
are.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from use_cases.solving.optimization.mip.optimization.model_abstraction.model_solution import ModelSolution
from use_cases.solving.optimization.mip.optimization.model_abstraction.optimization_model import OptimizationModel


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
    def solve(self, model: OptimizationModel, output_dir: Path | None = None) -> ModelSolution:
        """Solve the given model and return a solution.

        Args:
            model: The solver-agnostic optimization model to solve.
            output_dir: Directory to write solver debugging artifacts (e.g. an
                LP dump of the model) into, or None to skip writing any. Not
                every implementation produces artifacts; a solver that has
                nothing to write may simply ignore this argument.

        Returns:
            A ModelSolution with status and variable values (or None if infeasible).
        """
