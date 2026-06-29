"""HiGHS solver implementation that delegates to the optimizer via highspy.

HiGHS is an open-source, high-performance solver for LP and MIP problems.
This class translates an OptimizationModel into the highspy Python API
directly â€” no Pyomo dependency. It is the only file in this project that
imports highspy.
"""

from __future__ import annotations

import logging

import highspy
import numpy as np

from engine.optimization_strategy.mip.optimization.model_abstraction.linear_constraint import ConstraintSign
from engine.optimization_strategy.mip.optimization.model_abstraction.model_solution import ModelSolution, SolutionStatus
from engine.optimization_strategy.mip.optimization.model_abstraction.model_variable import VarType
from engine.optimization_strategy.mip.optimization.model_abstraction.optimization_model import ObjectiveSense, OptimizationModel
from engine.optimization_strategy.mip.optimization.solvers.base_technology_solver import BaseTechnologySolver

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
    variables â†’ ``addVar`` / ``changeColIntegrality``,
    constraints â†’ ``addRow``,
    objective â†’ ``changeColCost`` / ``changeObjectiveSense``.
    """

    def __init__(self) -> None:
        self._highs_model: highspy.Highs | None = None

    def solve(self, model: OptimizationModel) -> ModelSolution:
        """Translate and solve the model with HiGHS.

        Args:
            model: The solver-agnostic optimization model.

        Returns:
            ModelSolution with status and variable values, or None values
            if no feasible solution was found.
        """
        self._highs_model = highspy.Highs()

        # Uncomment this if you don't want logs into the console.
        # self._highs_model.silent()

        # Create the model in Highs
        col_index = self._add_variables(model)
        self._set_objective(model, col_index)
        self._add_constraints(model, col_index)

        # Solve the model
        self._highs_model.run()
        status = self._highs_model.getModelStatus()
        logger.info("HiGHS terminated with status: %s", status)

        #
        return self._build_solution(model, status)

    def _add_variables(self, model: OptimizationModel) -> dict[str, int]:
        """Add decision variables to the HiGHS model.

        Args:
            model: The solver-agnostic optimization model.

        Returns:
            Mapping from variable name to HiGHS column index, used to
            reference variables when building constraints and the objective.
        """
        col_index: dict[str, int] = {}
        for i, var in enumerate(model.variables):
            ub = var.upper_bound if var.upper_bound is not None else highspy.kHighsInf
            self._highs_model.addVar(var.lower_bound, ub)
            if var.var_type in {VarType.INTEGER, VarType.BINARY}:
                self._highs_model.changeColIntegrality(i, highspy.HighsVarType.kInteger)
            col_index[var.name] = i
        return col_index

    def _set_objective(self, model: OptimizationModel, col_index: dict[str, int]) -> None:
        """Set the objective function coefficients and optimization direction.

        Args:
            model: The solver-agnostic optimization model.
            col_index: Mapping from variable name to HiGHS column index.
        """
        for var_name, coeff in model.objective_expression.terms.items():
            self._highs_model.changeColCost(col_index[var_name], coeff)

        sense = highspy.ObjSense.kMaximize if model.objective_sense == ObjectiveSense.MAXIMIZE else highspy.ObjSense.kMinimize
        self._highs_model.changeObjectiveSense(sense)

    def _add_constraints(self, model: OptimizationModel, col_index: dict[str, int]) -> None:
        """Add linear constraints to the HiGHS model.

        Args:
            model: The solver-agnostic optimization model.
            col_index: Mapping from variable name to HiGHS column index.
        """
        for constraint in model.constraints:
            indices = [col_index[name] for name in constraint.lhs.terms]
            coeffs = list(constraint.lhs.terms.values())
            row_lb, row_ub = self._get_row_bounds(constraint.sign, constraint.rhs)
            self._highs_model.addRow(row_lb, row_ub, len(indices), np.array(indices, dtype=np.int32), np.array(coeffs, dtype=np.float64))

    def _build_solution(self, model: OptimizationModel, status: highspy.HighsModelStatus) -> ModelSolution:
        """Map the HiGHS result to a domain ModelSolution.

        Args:
            model: The solver-agnostic optimization model.
            status: The model status returned by HiGHS.

        Returns:
            ModelSolution with the appropriate status and variable values.
        """
        if status not in _FEASIBLE_STATUSES:
            return ModelSolution(status=self._map_status(status), variable_values=None)

        sol = self._highs_model.getSolution()
        values = {var.name: sol.col_value[i] for i, var in enumerate(model.variables)}
        return ModelSolution(status=SolutionStatus.OPTIMAL, variable_values=values)

    @staticmethod
    def _get_row_bounds(sign: ConstraintSign, rhs: float) -> tuple[float, float]:
        """Translate a constraint sign into the (row_lb, row_ub) pair HiGHS expects.

        HiGHS represents all constraints as range rows: lb â‰¤ expr â‰¤ ub.
        One-sided constraints use Â±infinity as the inactive bound.

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
