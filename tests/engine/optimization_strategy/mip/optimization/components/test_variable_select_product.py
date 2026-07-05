import pytest
from domain.product import Product
from domain.request import Request
from engine.optimization.mip.optimization.components.variable_select_product import VariableSelectProduct


@pytest.fixture
def banana() -> Product:
    return Product(name="banana", price_usd=0.5, weight_kg=0.12, calories=89)


@pytest.fixture
def chips() -> Product:
    return Product(name="chips", price_usd=1.0, weight_kg=0.2, calories=150)


def test__variable_select_product__creates_one_variable_per_product(banana, chips):
    # ARRANGE
    request = Request(max_weight_kg=5.0, max_budget_usd=10.0, products=[banana, chips])

    # ACT
    variables = VariableSelectProduct().build(request)

    # ASSERT
    assert len(variables) == 2
    names = {v.name for v in variables}
    assert names == {"banana", "chips"}


def test__variable_select_product__variables_are_integer_type(banana):
    # ARRANGE
    request = Request(max_weight_kg=5.0, max_budget_usd=10.0, products=[banana])

    # ACT
    variables = VariableSelectProduct().build(request)

    # ASSERT
    assert all(v.var_type == "integer" for v in variables)


def test__variable_select_product__lower_bound_is_zero(banana):
    # ARRANGE
    request = Request(max_weight_kg=5.0, max_budget_usd=10.0, products=[banana])

    # ACT
    variables = VariableSelectProduct().build(request)

    # ASSERT
    assert all(v.lower_bound == 0.0 for v in variables)


def test__variable_select_product__given_name_fn__applies_it_to_variable_names(banana, chips):
    # ARRANGE
    request = Request(max_weight_kg=5.0, max_budget_usd=10.0, products=[banana, chips])

    # ACT
    variables = VariableSelectProduct().build(request, name_fn=lambda name: f"quantity_{name}")

    # ASSERT
    names = {v.name for v in variables}
    assert names == {"quantity_banana", "quantity_chips"}
