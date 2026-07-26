"""Core optimization orchestrator for the MIP knapsack model.

Assembles the OptimizationModel from components, delegates solving to
BaseTechnologySolver, and extracts a domain Recommendation from the solution.

Typical call chain:
    MipStrategy.solve() → PreProcess → **this module** → PostProcess
"""

from __future__ import annotations

import logging
from pathlib import Path

from domain.product import Product
from domain.recommendation import Recommendation
from domain.request import Request
from use_cases.solving.optimization.mip.optimization.components.constraint_limit_budget import ConstraintLimitBudget
from use_cases.solving.optimization.mip.optimization.components.constraint_limit_weight import ConstraintLimitWeight
from use_cases.solving.optimization.mip.optimization.components.objective_calories import ObjectiveCalories
from use_cases.solving.optimization.mip.optimization.components.variable_select_product import (
    VariableSelectProduct,
)
from use_cases.solving.optimization.mip.optimization.model_abstraction.optimization_model import (
    ObjectiveSense,
    OptimizationModel,
)
from use_cases.solving.optimization.mip.optimization.solvers.base_technology_solver import BaseTechnologySolver
from use_cases.solving.preprocessing.pre_processed_data import PreProcessedData

logger = logging.getLogger(__name__)


class Optimization:
    """Builds the optimization model, solves it, and extracts a Recommendation.

    Subphase 1: Build the model (variables, constraints, objective).
    Subphase 2: Solve with the chosen technology.
    Subphase 3: Extract the Recommendation from the solution.

    The solver is constructor-injected (Dependency Injection) rather than
    selected here from a name string: resolving a solver name (e.g. "highs")
    to a concrete BaseTechnologySolver happens once, at the composition root
    (bootstrap.py), not inside this class.
    """

    def __init__(self, solver: BaseTechnologySolver) -> None:
        self._solver = solver

    def run(self, preprocessed_data: PreProcessedData, output_dir: Path | None = None) -> Recommendation | None:
        """Build model, solve, and extract recommendation.

        Args:
            preprocessed_data: Output of the preprocessing stage.
            output_dir: Directory to write the built model's LP dump into, or
                None to skip writing it. Forwarded to the solver unchanged.

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
        solution = self._solver.solve(model, output_dir)
        logger.info("Solver status: %s", solution.status)
        if solution.variable_values is None:
            return None

        # Subphase 3: extract recommendation
        return self._extract_recommendation(request, solution.variable_values)

    def _build_model(self, request: Request) -> OptimizationModel:
        # Every component is handed self.variable_name so the whole model
        # (variables, constraints, objective) agrees on one naming convention.
        # The components can't apply this convention themselves: they're
        # imported by this module, so importing Optimization back into them
        # would be a circular import. Passing the function in as an argument
        # sidesteps that entirely.
        variables = VariableSelectProduct().build(request, name_fn=self.variable_name)
        weight_c = ConstraintLimitWeight().build(request, name_fn=self.variable_name)
        budget_c = ConstraintLimitBudget().build(request, name_fn=self.variable_name)
        objective = ObjectiveCalories().build_expression(request, name_fn=self.variable_name)
        logger.info("Built model: %d products", len(variables))
        return OptimizationModel(
            variables=variables,
            constraints=[weight_c, budget_c],
            objective_expression=objective,
            objective_sense=ObjectiveSense.MAXIMIZE,
        )

    @staticmethod
    def variable_name(product_name: str) -> str:
        """Return the solver-facing variable name for a product's decision variable.

        Prefixing with "quantity_" makes model.lp self-explanatory: a reader
        immediately sees "quantity_banana" as the number of units of banana
        bought, rather than a bare "banana" that could be confused with some
        other variable kind referencing the same product if the model grows
        later. The variable is a general (unbounded) integer, not binary — it
        counts units, it isn't a yes/no decision.
        """
        return f"quantity_{product_name}"

    def _extract_recommendation(self, request: Request, variable_values: dict[str, float]) -> Recommendation | None:
        """Convert solver variable values to a domain Recommendation."""
        # Keyed with the same variable_name() used to build the model, so a
        # solved variable name maps straight back to its Product with no
        # separate "strip the prefix" logic to keep in sync.
        product_map = {self.variable_name(p.name): p for p in request.products}
        quantities: dict[Product, int] = {}
        for name, value in variable_values.items():
            # Round to nearest integer” MIP solvers use floating-point arithmetic
            qty = int(round(value))
            if qty >= 1:
                quantities[product_map[name]] = qty

        if not quantities:
            return None

        return Recommendation(request=request, quantities=quantities)
