import pytest
from domain.product import Product
from domain.request import Request
from engine.optimization.mip.optimization.components.constraint_limit_weight import ConstraintLimitWeight


@pytest.fixture
def banana() -> Product:
    return Product(name="banana", price_usd=0.5, weight_kg=0.12, calories=89)


@pytest.fixture
def chips() -> Product:
    return Product(name="chips", price_usd=1.0, weight_kg=0.2, calories=150)


def test__constraint_limit_weight__rhs_equals_max_weight(banana):
    # ARRANGE
    request = Request(max_weight_kg=3.5, max_budget_usd=10.0, products=[banana])

    # ACT
    constraint = ConstraintLimitWeight().build(request)

    # ASSERT
    assert constraint.rhs == 3.5
    assert constraint.sign == "<="


def test__constraint_limit_weight__each_product_contributes_its_weight(banana, chips):
    # ARRANGE
    request = Request(max_weight_kg=5.0, max_budget_usd=10.0, products=[banana, chips])

    # ACT
    constraint = ConstraintLimitWeight().build(request)

    # ASSERT
    assert constraint.lhs.terms["banana"] == pytest.approx(0.12)
    assert constraint.lhs.terms["chips"] == pytest.approx(0.2)
