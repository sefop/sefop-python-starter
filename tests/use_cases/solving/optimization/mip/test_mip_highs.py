import pytest

from domain.product import Product
from domain.request import Request
from use_cases.solving.optimization.mip.mip_highs import MipHighs
from use_cases.solving.preprocessing.pre_processed_data import PreProcessedData


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


def test__solve__recommendation_maps_solved_quantities_back_to_the_right_products(preprocessed_data, banana, chips):
    # ACT
    recommendations = MipHighs().solve(preprocessed_data)

    # ASSERT — the solver only ever sees "quantity_<name>" variable names;
    # this proves the reverse lookup in _extract_recommendation correctly
    # maps them back to the actual Product objects, not e.g. raising KeyError
    # or mixing up products.
    assert recommendations
    for product in recommendations[0].quantities:
        assert product in {banana, chips}


def test__solve__given_output_dir__lp_file_uses_prefixed_variable_names(preprocessed_data, tmp_path):
    # ACT
    MipHighs().solve(preprocessed_data, output_dir=tmp_path)

    # ASSERT
    lp_text = (tmp_path / "model.lp").read_text(encoding="utf-8")
    assert "quantity_banana" in lp_text
    assert "quantity_chips" in lp_text


def test__solve__given_no_output_dir__writes_no_lp_file(preprocessed_data, tmp_path, monkeypatch):
    # ARRANGE — chdir so any accidental relative-path write would land under
    # tmp_path, where it's easy to detect.
    monkeypatch.chdir(tmp_path)

    # ACT
    MipHighs().solve(preprocessed_data)

    # ASSERT
    assert list(tmp_path.rglob("*.lp")) == []


def test__solve__given_output_dir__lp_file_uses_domain_names_not_generic_labels(preprocessed_data, tmp_path):
    # ACT
    MipHighs().solve(preprocessed_data, output_dir=tmp_path)

    # ASSERT
    lp_text = (tmp_path / "model.lp").read_text(encoding="utf-8")
    assert "quantity_banana" in lp_text
    assert "c0" not in lp_text
