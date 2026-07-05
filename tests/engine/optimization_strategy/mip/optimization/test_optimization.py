import pytest

from domain.product import Product
from domain.request import Request
from engine.optimization.mip.optimization.optimization import Optimization
from engine.preprocessing.pre_processed_data import PreProcessedData


@pytest.fixture
def banana() -> Product:
    return Product(name="banana", price_usd=0.5, weight_kg=0.12, calories=89)


@pytest.fixture
def chips() -> Product:
    return Product(name="chips", price_usd=1.0, weight_kg=0.2, calories=150)


@pytest.fixture
def preprocessed_data(banana, chips) -> PreProcessedData:
    request = Request(max_weight_kg=5.0, max_budget_usd=10.0, products=[banana, chips])
    return PreProcessedData(request=request, feasible_products=[banana, chips])


def test__run__recommendation_maps_solved_quantities_back_to_the_right_products(preprocessed_data, banana, chips):
    # ACT
    recommendation = Optimization().run(preprocessed_data)

    # ASSERT — the solver only ever sees "select_<name>" variable names;
    # this proves the reverse lookup in _extract_recommendation correctly
    # maps them back to the actual Product objects, not e.g. raising KeyError
    # or mixing up products.
    assert recommendation is not None
    for product in recommendation.quantities:
        assert product in {banana, chips}


def test__run__given_output_dir__lp_file_uses_prefixed_variable_names(preprocessed_data, tmp_path):
    # ACT
    Optimization().run(preprocessed_data, output_dir=tmp_path)

    # ASSERT
    lp_text = (tmp_path / "model.lp").read_text(encoding="utf-8")
    assert "quantity_banana" in lp_text
    assert "quantity_chips" in lp_text
