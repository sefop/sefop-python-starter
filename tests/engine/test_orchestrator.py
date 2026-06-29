"""Integration tests for the optimization Orchestrator."""

import pytest

from domain.product import Product
from domain.request import Request
from engine.orchestrator import Orchestrator


@pytest.fixture
def banana() -> Product:
    """A product for testing."""
    return Product(name="banana", price_usd=0.5, weight_kg=0.12, calories=89)


def test__orchestrator__when_request_is_solvable__returns_recommendation(banana):
    """ARRANGE: Small request (≤50 products) → MIP solver."""
    request = Request(max_weight_kg=5.0, max_budget_usd=10.0, products=[banana])
    orchestrator = Orchestrator()

    # ACT
    result = orchestrator.solve(request)

    # ASSERT — Recommendation should contain selected products and totals
    assert result is not None
    assert result.total_calories > 0
    assert result.total_weight_kg > 0
    assert result.total_cost_usd > 0


def test__orchestrator__when_no_product_fits__returns_none():
    """ARRANGE: Budget too tight to afford any product."""
    expensive = Product(name="expensive", price_usd=100.0, weight_kg=1.0, calories=100)
    request = Request(max_weight_kg=10.0, max_budget_usd=0.01, products=[expensive])
    orchestrator = Orchestrator()

    # ACT
    result = orchestrator.solve(request)

    # ASSERT — No product fits, so no recommendation exists
    assert result is None
