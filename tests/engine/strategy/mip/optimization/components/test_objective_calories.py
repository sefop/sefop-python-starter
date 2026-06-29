import pytest
from domain.product import Product
from domain.request import Request
from engine.strategy.mip.optimization.components.objective_calories import ObjectiveCalories


@pytest.fixture
def banana() -> Product:
    return Product(name="banana", price_usd=0.5, weight_kg=0.12, calories=89)


@pytest.fixture
def chips() -> Product:
    return Product(name="chips", price_usd=1.0, weight_kg=0.2, calories=150)


def test__objective_calories__each_product_contributes_its_calories(banana, chips):
    # ARRANGE
    request = Request(max_weight_kg=5.0, max_budget_usd=10.0, products=[banana, chips])

    # ACT
    expression = ObjectiveCalories().build_expression(request)

    # ASSERT
    assert expression.terms["banana"] == pytest.approx(89.0)
    assert expression.terms["chips"] == pytest.approx(150.0)
