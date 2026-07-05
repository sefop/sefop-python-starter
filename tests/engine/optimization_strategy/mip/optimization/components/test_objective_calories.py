import pytest
from domain.product import Product
from domain.request import Request
from engine.optimization.mip.optimization.components.objective_calories import ObjectiveCalories
from engine.optimization.mip.optimization.model_abstraction.linear_expression import LinearExpression
from engine.optimization.mip.optimization.optimization import Optimization


@pytest.fixture
def banana() -> Product:
    return Product(name="banana", price_usd=0.5, weight_kg=0.12, calories=89)


@pytest.fixture
def chips() -> Product:
    return Product(name="chips", price_usd=1.0, weight_kg=0.2, calories=150)


def test__objective_calories__matches_expected_expression(banana, chips):
    # ARRANGE
    request = Request(max_weight_kg=5.0, max_budget_usd=10.0, products=[banana, chips])
    expected = LinearExpression()
    expected.add(banana.calories, Optimization.variable_name(banana.name))
    expected.add(chips.calories, Optimization.variable_name(chips.name))

    # ACT
    expression = ObjectiveCalories().build_expression(request, name_fn=Optimization.variable_name)

    # ASSERT — pytest.approx handles the whole terms dict, avoiding
    # exact-== comparison on the underlying float coefficients.
    assert expression.terms == pytest.approx(expected.terms)
