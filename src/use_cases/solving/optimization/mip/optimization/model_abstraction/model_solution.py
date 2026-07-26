"""Solver output returned by BaseTechnologySolver.

Pure Python stdlib only — no solver dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SolutionStatus(StrEnum):
    """Canonical solver termination statuses."""

    OPTIMAL = "optimal"
    INFEASIBLE = "infeasible"
    UNBOUNDED = "unbounded"
    ERROR = "error"


@dataclass(frozen=True)
class ModelSolution:
    """Raw output from a solver run.

    Attributes:
        status: Solver termination status.
        variable_values: Map of variable name → solution value.
            ``None`` when the problem has no feasible solution.
    """

    status: SolutionStatus
    variable_values: dict[str, float] | None
