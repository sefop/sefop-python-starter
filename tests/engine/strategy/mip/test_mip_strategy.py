import pytest
from domain.product import Product
from domain.request import Request
from engine.pre_processed_data import PreProcessedData
from engine.strategy.mip.mip_strategy import MipStrategy


@pytest.fixture
def banana() -> Product:
    return Product(name="banana", price_usd=0.5, weight_kg=0.12, calories=89)


@pytest.fixture
def chips() -> Product:
    return Product(name="chips", price_usd=1.0, weight_kg=0.2, calories=150)


@pytest.mark.integration
def test__mip_strategy__when_request_is_solvable__returns_recommendation(banana, chips):
    # ARRANGE
    request = Request(max_weight_kg=1.0, max_budget_usd=5.0, products=[banana, chips])
    strategy = MipStrategy()

    # ACT
    data = PreProcessedData(request=request)
    result = strategy.solve(data)

    # ASSERT
    assert result is not None
    assert result.total_calories > 0
    assert result.total_weight_kg <= request.max_weight_kg
    assert result.total_cost_usd <= request.max_budget_usd


@pytest.mark.integration
def test__mip_strategy__when_no_product_fits__returns_none():
    # ARRANGE — price too high to afford anything
    expensive = Product(name="expensive", price_usd=100.0, weight_kg=1.0, calories=100)
    request = Request(max_weight_kg=10.0, max_budget_usd=0.01, products=[expensive])
    strategy = MipStrategy()

    # ACT
    data = PreProcessedData(request=request)
    result = strategy.solve(data)

    # ASSERT
    assert result is None
