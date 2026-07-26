import pytest
from domain.product import Product
from domain.request import Request
from use_cases.solving.optimization.mip.optimization.components.variable_select_product import VariableSelectProduct
from use_cases.solving.optimization.mip.optimization.model_abstraction.model_variable import ModelVariable, VarType
from use_cases.solving.optimization.mip.optimization.optimization import Optimization


@pytest.fixture
def banana() -> Product:
    return Product(name="banana", price_usd=0.5, weight_kg=0.12, calories=89)


@pytest.fixture
def chips() -> Product:
    return Product(name="chips", price_usd=1.0, weight_kg=0.2, calories=150)


def test__variable_select_product__matches_expected_variables(banana, chips):
    # ARRANGE
    request = Request(max_weight_kg=5.0, max_budget_usd=10.0, products=[banana, chips])
    expected = [
        ModelVariable(
            name=Optimization.variable_name(banana.name), var_type=VarType.INTEGER, lower_bound=0.0, upper_bound=None
        ),
        ModelVariable(
            name=Optimization.variable_name(chips.name), var_type=VarType.INTEGER, lower_bound=0.0, upper_bound=None
        ),
    ]

    # ACT
    variables = VariableSelectProduct().build(request, name_fn=Optimization.variable_name)

    # ASSERT — compared field-by-field (not with `==` on ModelVariable
    # directly) so the float bound fields go through pytest.approx.
    assert len(variables) == len(expected)
    for actual, exp in zip(variables, expected):
        assert actual.name == exp.name
        assert actual.var_type == exp.var_type
        assert actual.lower_bound == pytest.approx(exp.lower_bound)
        assert actual.upper_bound == exp.upper_bound
