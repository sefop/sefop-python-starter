import pytest
from domain.product import Product
from domain.request import Request
from engine.optimization.mip.optimization.components.constraint_limit_budget import ConstraintLimitBudget
from engine.optimization.mip.optimization.model_abstraction.linear_constraint import ConstraintSign


@pytest.fixture
def banana() -> Product:
    return Product(name="banana", price_usd=0.5, weight_kg=0.12, calories=89)


@pytest.fixture
def chips() -> Product:
    return Product(name="chips", price_usd=1.0, weight_kg=0.2, calories=150)


def test__constraint_limit_budget__rhs_equals_max_budget(banana):
    # ARRANGE
    request = Request(max_weight_kg=5.0, max_budget_usd=7.5, products=[banana])

    # ACT
    constraint = ConstraintLimitBudget().build(request)

    # ASSERT
    assert constraint.rhs == 7.5
    assert constraint.sign == ConstraintSign.LEQ


def test__constraint_limit_budget__each_product_contributes_its_price(banana, chips):
    # ARRANGE
    request = Request(max_weight_kg=5.0, max_budget_usd=10.0, products=[banana, chips])

    # ACT
    constraint = ConstraintLimitBudget().build(request)

    # ASSERT
    assert constraint.lhs.terms["banana"] == pytest.approx(0.5)
    assert constraint.lhs.terms["chips"] == pytest.approx(1.0)


def test__constraint_limit_budget__given_name_fn__applies_it_to_term_keys(banana):
    # ARRANGE
    request = Request(max_weight_kg=5.0, max_budget_usd=10.0, products=[banana])

    # ACT
    constraint = ConstraintLimitBudget().build(request, name_fn=lambda name: f"quantity_{name}")

    # ASSERT
    assert constraint.lhs.terms["quantity_banana"] == pytest.approx(0.5)
