"""Integration tests for the optimization Orchestrator."""

import pytest

from domain.product import Product
from domain.request import Request
from use_cases.solving.optimization.heuristic.greedy_calories import GreedyCalories
from use_cases.solving.optimization.mip.mip_strategy import MipStrategy
from use_cases.solving.optimization.mip.optimization.optimization import Optimization
from use_cases.solving.optimization.mip.optimization.solvers.highs_solver import HighsSolver
from use_cases.solving.orchestrator import Orchestrator
from use_cases.solving.postprocessing.postprocessing import PostProcess
from use_cases.solving.preprocessing.preprocessing import PreProcess


@pytest.fixture
def banana() -> Product:
    """A product for testing."""
    return Product(name="banana", price_usd=0.5, weight_kg=0.12, calories=89)


def _orchestrator() -> Orchestrator:
    return Orchestrator(
        preprocessing=PreProcess(),
        postprocessing=PostProcess(),
        mip_strategy=MipStrategy(optimization=Optimization(solver=HighsSolver())),
        heuristic_strategy=GreedyCalories(),
    )


def test__orchestrator__when_request_is_solvable__returns_recommendation(banana):
    """ARRANGE: Small request (≤50 products) → MIP solver."""
    request = Request(max_weight_kg=5.0, max_budget_usd=10.0, products=[banana])
    orchestrator = _orchestrator()

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
    orchestrator = _orchestrator()

    # ACT
    result = orchestrator.solve(request)

    # ASSERT — No product fits, so no recommendation exists
    assert result is None
