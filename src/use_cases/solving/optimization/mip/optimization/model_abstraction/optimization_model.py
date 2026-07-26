"""Complete solver-agnostic representation of a MIP optimization problem.

Assembles variables, constraints, and objective into a single object that
``BaseTechnologySolver`` implementations consume.
Pure Python stdlib only — no solver dependency.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from use_cases.solving.optimization.mip.optimization.model_abstraction.linear_constraint import LinearConstraint
from use_cases.solving.optimization.mip.optimization.model_abstraction.linear_expression import LinearExpression
from use_cases.solving.optimization.mip.optimization.model_abstraction.model_variable import ModelVariable

# Variable and constraint names are written verbatim into solver-specific file
# formats (e.g. HiGHS's LP dump), where spaces, dots, and other special
# characters either break the file's syntax or collide with format-reserved
# symbols. Restricting names to letters, digits, and underscores keeps every
# name safe to write out, regardless of which solver ends up consuming it.
_SAFE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


class ObjectiveSense(StrEnum):
    """Valid optimization directions."""

    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


@dataclass
class OptimizationModel:
    """Complete MIP problem definition.

    This is the single point where a model is assembled from its parts, so it
    is also the single point where every variable and constraint name is
    validated: each must contain only letters, digits, and underscores (see
    ``_SAFE_NAME_PATTERN``). Construction raises ``ValueError`` immediately if
    any name violates this, rather than letting an unsafe name reach a solver
    and corrupt its output later.

    Attributes:
        variables: Decision variables that appear in constraints and objective.
        constraints: Linear constraints the solution must satisfy.
        objective_expression: Linear expression to optimize.
        objective_sense: Optimization direction.
    """

    variables: list[ModelVariable]
    constraints: list[LinearConstraint]
    objective_expression: LinearExpression
    objective_sense: ObjectiveSense

    def __post_init__(self) -> None:
        # Fail fast, once, here: every solver implementation downstream
        # (HighsSolver today, others later) can then pass names straight into
        # filenames or file-format syntax without re-validating them itself.
        for variable in self.variables:
            self._validate_name(variable.name, "Variable")
        for constraint in self.constraints:
            self._validate_name(constraint.name, "Constraint")

    @staticmethod
    def _validate_name(name: str, label: str) -> None:
        if not _SAFE_NAME_PATTERN.match(name):
            raise ValueError(
                f"{label} name '{name}' is invalid: only letters, digits, and underscores are "
                "allowed (no spaces, dots, or other special characters)."
            )
