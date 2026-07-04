"""Core optimization orchestrator for the MIP knapsack model.

Assembles the OptimizationModel from components, delegates solving to
BaseTechnologySolver, and extracts a domain Recommendation from the solution.

Typical call chain:
    MipStrategy.solve() â†’ PreProcess â†’ **this module** â†’ PostProcess
"""

from __future__ import annotations

import logging

from engine.optimization.mip.optimization.components.constraint_limit_budget import ConstraintLimitBudget
from engine.optimization.mip.optimization.components.constraint_limit_weight import ConstraintLimitWeight
from engine.optimization.mip.optimization.components.objective_calories import ObjectiveCalories
from engine.optimization.mip.optimization.components.variable_select_product import VariableSelectProduct
from engine.optimization.mip.optimization.model_abstraction.optimization_model import ObjectiveSense, OptimizationModel
from engine.optimization.mip.optimization.solvers.base_technology_solver import BaseTechnologySolver
from engine.optimization.mip.optimization.solvers.highs_solver import HighsSolver
from engine.preprocessing.pre_processed_data import PreProcessedData
from domain.product import Product
from domain.recommendation import Recommendation
from domain.request import Request

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

        # Subphase 1: build solver-agnostic model over feasible products only.
        # Wrapping feasible_products in a temporary Request lets the model
        # components work unchanged — they only see products that can be selected.
        feasible_request = Request(
            max_weight_kg=request.max_weight_kg,
            max_budget_usd=request.max_budget_usd,
            products=preprocessed_data.feasible_products,
        )
        model = self._build_model(feasible_request)

        # Subphase 2: solve
        solution = self._solver.solve(model)
        logger.info("Solver status: %s", solution.status)
        if solution.variable_values is None:
            return None

        # Subphase 3: extract recommendation
        return self._extract_recommendation(request, solution.variable_values)

    def _build_model(self, request: Request) -> OptimizationModel:
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

    def _extract_recommendation(
        self, request: Request, variable_values: dict[str, float]
    ) -> Recommendation | None:
        """Convert solver variable values to a domain Recommendation."""
        product_map = {p.name: p for p in request.products}
        quantities: dict[Product, int] = {}
        for name, value in variable_values.items():
            # Round to nearest integer” MIP solvers use floating-point arithmetic
            qty = int(round(value))
            if qty >= 1:
                quantities[product_map[name]] = qty

        if not quantities:
            return None

        return Recommendation(request=request, quantities=quantities)
