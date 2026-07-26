"""HiGHS solver implementation that delegates to the optimizer via highspy.

HiGHS is an open-source, high-performance solver for LP and MIP problems.
This class translates an OptimizationModel into the highspy Python API
directly — no Pyomo dependency. It is the only file in this project that
imports highspy.
"""

from __future__ import annotations

import logging
from pathlib import Path

import highspy
import numpy as np

from use_cases.solving.optimization.mip.optimization.model_abstraction.linear_constraint import ConstraintSign
from use_cases.solving.optimization.mip.optimization.model_abstraction.model_solution import (
    ModelSolution,
    SolutionStatus,
)
from use_cases.solving.optimization.mip.optimization.model_abstraction.model_variable import VarType
from use_cases.solving.optimization.mip.optimization.model_abstraction.optimization_model import (
    ObjectiveSense,
    OptimizationModel,
)
from use_cases.solving.optimization.mip.optimization.solvers.base_technology_solver import BaseTechnologySolver

logger = logging.getLogger(__name__)

# Floating-point values returned by MIP solvers for binary/integer variables
# are not always exact (e.g. 0.9999 instead of 1). Values are rounded to the
# nearest integer when extracting the solution.
_FEASIBLE_STATUSES = {
    highspy.HighsModelStatus.kOptimal,
    highspy.HighsModelStatus.kObjectiveBound,
    highspy.HighsModelStatus.kObjectiveTarget,
    highspy.HighsModelStatus.kSolutionLimit,
}


class HighsSolver(BaseTechnologySolver):
    """HiGHS solver implementation using the highspy Python bindings.

    Translates the solver-agnostic ``OptimizationModel`` into HiGHS calls:
    variables -> ``addVar`` / ``changeColIntegrality``,
    constraints -> ``addRow``,
    objective -> ``changeColCost`` / ``changeObjectiveSense``.
    """

    def solve(self, model: OptimizationModel, output_dir: Path | None = None) -> ModelSolution:
        """Translate and solve the model with HiGHS.

        Args:
            model: The solver-agnostic optimization model.
            output_dir: If given, the built model is dumped as "model.lp" in
                this directory before solving starts. This lets a data
                scientist inspect the exact formulation HiGHS received —
                useful when a solution looks wrong and the bug could be in
                variable/constraint construction rather than in the solver
                itself. Pass None (the default) to skip writing it.

        Returns:
            ModelSolution with status and variable values, or None values
            if no feasible solution was found.
        """
        highs_model = highspy.Highs()

        # Uncomment this if you don't want logs into the console.
        # highs_model.silent()

        # Create the model in Highs
        col_index = self._add_variables(model, highs_model)
        self._set_objective(model, col_index, highs_model)
        self._add_constraints(model, col_index, highs_model)

        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            # highspy infers the output format (LP vs MPS) from the file
            # extension, so ".lp" is what selects the human-readable LP format.
            highs_model.writeModel(str(output_dir / "model.lp"))

        # Solve the model
        highs_model.run()
        status = highs_model.getModelStatus()
        logger.info("HiGHS terminated with status: %s", status)

        return self._build_solution(model, status, highs_model)

    def _add_variables(self, model: OptimizationModel, highs_model: highspy.Highs) -> dict[str, int]:
        """Add decision variables to the HiGHS model.

        Args:
            model: The solver-agnostic optimization model.
            highs_model: The HiGHS model instance being built for this solve() call.

        Returns:
            Mapping from variable name to HiGHS column index, used to
            reference variables when building constraints and the objective.
        """
        col_index: dict[str, int] = {}
        for i, var in enumerate(model.variables):
            ub = var.upper_bound if var.upper_bound is not None else highspy.kHighsInf
            highs_model.addVar(var.lower_bound, ub)
            # Without this, HiGHS defaults to generic labels ("c0", "c1", ...)
            # for every column, which makes the model.lp dump unreadable.
            highs_model.passColName(i, var.name)
            if var.var_type in {VarType.INTEGER, VarType.BINARY}:
                highs_model.changeColIntegrality(i, highspy.HighsVarType.kInteger)
            col_index[var.name] = i
        return col_index

    def _set_objective(self, model: OptimizationModel, col_index: dict[str, int], highs_model: highspy.Highs) -> None:
        """Set the objective function coefficients and optimization direction.

        Args:
            model: The solver-agnostic optimization model.
            col_index: Mapping from variable name to HiGHS column index.
            highs_model: The HiGHS model instance being built for this solve() call.
        """
        for var_name, coeff in model.objective_expression.terms.items():
            highs_model.changeColCost(col_index[var_name], coeff)

        sense = (
            highspy.ObjSense.kMaximize
            if model.objective_sense == ObjectiveSense.MAXIMIZE
            else highspy.ObjSense.kMinimize
        )
        highs_model.changeObjectiveSense(sense)

    def _add_constraints(self, model: OptimizationModel, col_index: dict[str, int], highs_model: highspy.Highs) -> None:
        """Add linear constraints to the HiGHS model.

        Args:
            model: The solver-agnostic optimization model.
            col_index: Mapping from variable name to HiGHS column index.
            highs_model: The HiGHS model instance being built for this solve() call.
        """
        for row_index, constraint in enumerate(model.constraints):
            indices = [col_index[name] for name in constraint.lhs.terms]
            coeffs = list(constraint.lhs.terms.values())
            row_lb, row_ub = self._get_row_bounds(constraint.sign, constraint.rhs)
            highs_model.addRow(
                row_lb, row_ub, len(indices), np.array(indices, dtype=np.int32), np.array(coeffs, dtype=np.float64)
            )
            # Without this, HiGHS defaults to generic labels ("r0", "r1", ...)
            # for every row, which makes the model.lp dump unreadable.
            highs_model.passRowName(row_index, constraint.name)

    def _build_solution(
        self, model: OptimizationModel, status: highspy.HighsModelStatus, highs_model: highspy.Highs
    ) -> ModelSolution:
        """Map the HiGHS result to a domain ModelSolution.

        Args:
            model: The solver-agnostic optimization model.
            status: The model status returned by HiGHS.
            highs_model: The HiGHS model instance that was solved.

        Returns:
            ModelSolution with the appropriate status and variable values.
        """
        if status not in _FEASIBLE_STATUSES:
            return ModelSolution(status=self._map_status(status), variable_values=None)

        sol = highs_model.getSolution()
        values = {var.name: sol.col_value[i] for i, var in enumerate(model.variables)}
        return ModelSolution(status=SolutionStatus.OPTIMAL, variable_values=values)

    @staticmethod
    def _get_row_bounds(sign: ConstraintSign, rhs: float) -> tuple[float, float]:
        """Translate a constraint sign into the (row_lb, row_ub) pair HiGHS expects.

        HiGHS represents all constraints as range rows: lb ≤ expr ≤ ub.
        One-sided constraints use ±infinity as the inactive bound.

        Args:
            sign: The constraint comparison operator.
            rhs: The right-hand side scalar.

        Returns:
            A (lower_bound, upper_bound) pair for the HiGHS addRow call.
        """
        if sign == ConstraintSign.LEQ:
            return -highspy.kHighsInf, rhs
        if sign == ConstraintSign.GEQ:
            return rhs, highspy.kHighsInf
        # ConstraintSign.EQ: both bounds equal rhs forces equality
        return rhs, rhs

    @staticmethod
    def _map_status(highs_status: highspy.HighsModelStatus) -> SolutionStatus:
        """Translate a HiGHS model status to a domain SolutionStatus.

        Only called for non-feasible statuses; feasible cases are handled
        by the caller before reaching this method.

        Args:
            highs_status: The status returned by HiGHS after solving.

        Returns:
            The corresponding SolutionStatus for the domain layer.
        """
        if highs_status == highspy.HighsModelStatus.kInfeasible:
            return SolutionStatus.INFEASIBLE
        if highs_status in {highspy.HighsModelStatus.kUnbounded, highspy.HighsModelStatus.kUnboundedOrInfeasible}:
            return SolutionStatus.UNBOUNDED
        return SolutionStatus.ERROR
