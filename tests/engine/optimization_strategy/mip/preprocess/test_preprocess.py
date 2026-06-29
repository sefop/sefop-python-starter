import pytest
from domain.product import Product
from domain.request import Request
from engine.preprocessing import PreProcess


@pytest.fixture
def banana() -> Product:
    return Product(name="banana", price_usd=0.5, weight_kg=0.12, calories=89)


def test__preprocess__run__passes_request_through_unchanged(banana):
    # ARRANGE
    request = Request(max_weight_kg=5.0, max_budget_usd=10.0, products=[banana])

    # ACT
    result = PreProcess().run(request)

    # ASSERT
    assert result.request is request
