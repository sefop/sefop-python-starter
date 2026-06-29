"""Complete solver-agnostic representation of a MIP optimization problem.

Assembles variables, constraints, and objective into a single object that
``BaseTechnologySolver`` implementations consume.
Pure Python stdlib only â€” no solver dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from engine.optimization_strategy.mip.optimization.model_abstraction.linear_constraint import LinearConstraint
from engine.optimization_strategy.mip.optimization.model_abstraction.linear_expression import LinearExpression
from engine.optimization_strategy.mip.optimization.model_abstraction.model_variable import ModelVariable


class ObjectiveSense(StrEnum):
    """Valid optimization directions."""

    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


@dataclass
class OptimizationModel:
    """Complete MIP problem definition.

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
