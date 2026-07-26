"""Decision variables for product quantity selection.

One non-negative integer variable per product: x_i ≥ 0, integer.
Pure Python stdlib only — no solver dependency.
"""

from __future__ import annotations

from collections.abc import Callable

from domain.request import Request
from use_cases.solving.optimization.mip.optimization.model_abstraction.model_variable import ModelVariable, VarType


class VariableSelectProduct:
    """Creates one integer variable per product in the request.

    The variable ``x[product.name]`` represents how many units of that
    product are selected. It is non-negative and integer — this formulates
    the unbounded knapsack problem.
    """

    def build(self, request: Request, name_fn: Callable[[str], str] = lambda name: name) -> list[ModelVariable]:
        """Return one ModelVariable per product, keyed by product name.

        Args:
            request: The knapsack request whose products define the variables.
            name_fn: Transforms a product name into the ModelVariable name.
                Defaults to the identity function. Callers that need the
                solver-facing name to differ from the raw product name (e.g.
                Optimization, which prefixes it) inject their own function
                here rather than this component hardcoding a convention.

        Returns:
            List of integer variables with lower_bound=0 and no upper bound.
        """
        return [
            ModelVariable(name=name_fn(p.name), var_type=VarType.INTEGER, lower_bound=0.0, upper_bound=None)
            for p in request.products
        ]
