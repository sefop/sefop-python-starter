"""Core optimization orchestrator for the MIP knapsack model.

Assembles the OptimizationModel from components, delegates solving to
BaseTechnologySolver, and extracts a domain Recommendation from the solution.

Typical call chain:
    MipStrategy.solve() â†’ PreProcess â†’ **this module** â†’ PostProcess
"""

from __future__ import annotations

import logging

from engine.optimization_strategy.mip.optimization.components.constraint_limit_budget import ConstraintLimitBudget
from engine.optimization_strategy.mip.optimization.components.constraint_limit_weight import ConstraintLimitWeight
from engine.optimization_strategy.mip.optimization.components.objective_calories import ObjectiveCalories
from engine.optimization_strategy.mip.optimization.components.variable_select_product import VariableSelectProduct
from engine.optimization_strategy.mip.optimization.model_abstraction.optimization_model import ObjectiveSense, OptimizationModel
from engine.optimization_strategy.mip.optimization.solvers.base_technology_solver import BaseTechnologySolver
from engine.optimization_strategy.mip.optimization.solvers.highs_solver import HighsSolver
from engine.pre_processed_data import PreProcessedData
from domain.recommendation import Recommendation

logger = logging.getLogger(__name__)

# Maps solver name strings to solver classes.
# To add a new solver: create a BaseTechnologySolver subclass and add it here.
_SOLVER_REGISTRY: dict[str, type[BaseTechnologySolver]] = {
    "highs": HighsSolver,
}


class Optimization:
    """Builds the optimization model, solves it, and extracts a Recommendation.

    Subphase 1: Build the model (variables, constraints, objective).
    Subphase 2: Solve with the chosen technology.
    Subphase 3: Extract the Recommendation from the solution.
    """

    def __init__(self, solver_name: str = "highs") -> None:
        if solver_name not in _SOLVER_REGISTRY:
            raise ValueError(
                f"Unknown solver '{solver_name}'. Available: {list(_SOLVER_REGISTRY.keys())}"
            )
        self._solver: BaseTechnologySolver = _SOLVER_REGISTRY[solver_name]()

    def run(self, preprocessed_data: PreProcessedData) -> Recommendation | None:
        """Build model, solve, and extract recommendation.

        Args:
            preprocessed_data: Output of the preprocessing stage.

        Returns:
            A Recommendation, or None if no feasible solution exists.
        """
        request = preprocessed_data.request

        # Subphase 1: build solver-agnostic model
        model = self._build_model(request)

        # Subphase 2: solve
        solution = self._solver.solve(model)
        logger.info("Solver status: %s", solution.status)
        if solution.variable_values is None:
            return None

        # Subphase 3: extract recommendation
        return self._extract_recommendation(request, solution.variable_values)

    def _build_model(self, request) -> OptimizationModel:
        variables = VariableSelectProduct().build(request)
        weight_c = ConstraintLimitWeight().build(request)
        budget_c = ConstraintLimitBudget().build(request)
        objective = ObjectiveCalories().build_expression(request)
        logger.info("Built model: %d products", len(variables))
        return OptimizationModel(
            variables=variables,
            constraints=[weight_c, budget_c],
            objective_expression=objective,
            objective_sense=ObjectiveSense.MAXIMIZE,
        )

    def _extract_recommendation(self, request, variable_values: dict[str, float]):
        """Convert solver variable values to a domain Recommendation."""
        product_map = {p.name: p for p in request.products}
        quantities = {}
        for name, value in variable_values.items():
            # Round to nearest integer â€” MIP solvers use floating-point arithmetic
            qty = int(round(value))
            if qty >= 1:
                quantities[product_map[name]] = qty

        if not quantities:
            return None

        return Recommendation(request=request, quantities=quantities)
