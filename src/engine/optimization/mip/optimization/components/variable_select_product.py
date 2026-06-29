"""Decision variables for product quantity selection.

One non-negative integer variable per product: qty_i â‰¥ 0, integer.
Pure Python stdlib only â€” no solver dependency.
"""

from __future__ import annotations

from engine.optimization.mip.optimization.model_abstraction.model_variable import ModelVariable, VarType
from domain.request import Request


class VariableSelectProduct:
    """Creates one integer variable per product in the request.

    The variable ``qty[product.name]`` represents how many units of that
    product are selected. It is non-negative and integer â€” this formulates
    the unbounded knapsack problem.
    """

    def build(self, request: Request) -> list[ModelVariable]:
        """Return one ModelVariable per product, keyed by product name.

        Args:
            request: The knapsack request whose products define the variables.

        Returns:
            List of integer variables with lower_bound=0 and no upper bound.
        """
        return [
            ModelVariable(name=p.name, var_type=VarType.INTEGER, lower_bound=0.0, upper_bound=None)
            for p in request.products
        ]
