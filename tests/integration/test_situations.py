"""End-to-end integration tests for the knapsack optimizer.

Each test drives the real CLI (cli.main()) against one pre-built "situation"
folder under tests/resources/. Together the situations cover the range of
behaviors the optimization pipeline needs to get right: a clean feasible optimum,
total infeasibility, ties between optimal solutions, the MIP/heuristic strategy switch,
preprocessing's filtering of individually-infeasible products, quantities above 1,
and both constraints binding at once.
"""

import csv
from pathlib import Path

import pytest

import cli
from tests.helpers.lp_comparer import compare_lp

_RESOURCES_DIR = Path(__file__).parent.parent / "resources"


def _run_cli(
    situation: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> tuple[Path, int]:
    """Run cli.main() against a named situation folder.

    Points --data-folder straight at tests/resources (no chdir needed) and
    --output-folder at a fresh tmp_path, so situations never touch the real
    data/ or output/ folders.

    Args:
        situation: Name of the subfolder under tests/resources/ to solve;
            doubles as the request_id passed to the CLI.
        tmp_path: Pytest's per-test temporary directory, used as the output root.
        monkeypatch: Used to substitute sys.argv for the duration of the call.
        capsys: Used to capture the "Results written to <path>" line the CLI prints.

    Returns:
        The run folder cli.main() reported writing to, and its exit code.
    """
    monkeypatch.setattr(
        "sys.argv",
        ["cli", situation, "--data-folder", str(_RESOURCES_DIR), "--output-folder", str(tmp_path / "output")],
    )
    with pytest.raises(SystemExit) as exc_info:
        cli.main()
    printed = capsys.readouterr().out.strip()
    run_folder = Path(printed.removeprefix("Results written to ").strip())
    return run_folder, exc_info.value.code


def _read_totals(run_folder: Path) -> dict[str, float]:
    """Parse the TOTAL row of solution.csv into its four numeric columns."""
    with (run_folder / "solution.csv").open(newline="", encoding="utf-8") as f:
        *_, total_row = csv.reader(f)
    return {
        "quantity": float(total_row[4]),
        "cost": float(total_row[5]),
        "weight": float(total_row[6]),
        "calories": float(total_row[7]),
    }


def _assert_model_lp_matches_golden(situation: str, run_folder: Path) -> None:
    """Assert the model.lp just produced matches tests/resources/<situation>/model.lp.

    To regenerate a golden file after an intentional formulation change, run
    the CLI directly against the fixture and copy its model.lp over the golden:
        python -m cli <situation> --data-folder tests/resources --output-folder <tmp_dir>
        cp <tmp_dir>/<situation>/<timestamp>/model.lp tests/resources/<situation>/model.lp
    """
    golden = _RESOURCES_DIR / situation / "model.lp"
    diffs = compare_lp(golden, run_folder / "model.lp")
    assert diffs == [], diffs


@pytest.mark.integration
def test__cli_main__given_feasible_unique_optimum__returns_expected_optimal_calories(tmp_path, monkeypatch, capsys):
    # ARRANGE / ACT — 1 protein_bar + 2 chips (500 cal, using the full budget)
    # beats every other combination that fits in budget=10/weight=5.
    run_folder, exit_code = _run_cli("feasible_unique_optimum", tmp_path, monkeypatch, capsys)

    # ASSERT
    assert exit_code == 0
    assert "SUCCESS" in (run_folder / "status.txt").read_text(encoding="utf-8")
    assert _read_totals(run_folder)["calories"] == 500
    _assert_model_lp_matches_golden("feasible_unique_optimum", run_folder)


@pytest.mark.integration
def test__cli_main__given_infeasible__exits_nonzero_and_writes_no_solution(tmp_path, monkeypatch, capsys):
    # ARRANGE / ACT — the only product costs more than the entire budget, so
    # preprocessing filters it out and no recommendation exists.
    run_folder, exit_code = _run_cli("infeasible", tmp_path, monkeypatch, capsys)

    # ASSERT
    assert exit_code == 1
    assert "FAILURE" in (run_folder / "status.txt").read_text(encoding="utf-8")
    assert not (run_folder / "solution.csv").exists()


@pytest.mark.integration
def test__cli_main__given_multiple_optimal_solutions__returns_shared_optimal_calories(tmp_path, monkeypatch, capsys):
    # ARRANGE / ACT — cookie_a and cookie_b are interchangeable (same price,
    # weight, and calories), so either one alone is an optimal pick. Assert
    # only the shared optimal total, never which cookie the solver preferred.
    run_folder, exit_code = _run_cli("multiple_optimal_solutions", tmp_path, monkeypatch, capsys)

    # ASSERT
    assert exit_code == 0
    assert _read_totals(run_folder)["calories"] == 100
    _assert_model_lp_matches_golden("multiple_optimal_solutions", run_folder)


@pytest.mark.integration
def test__cli_main__given_large_instance__triggers_heuristic_and_returns_feasible_solution(
    tmp_path, monkeypatch, capsys
):
    # ARRANGE / ACT — 55 feasible products exceeds orchestrator.MAX_PRODUCTS_FOR_MIP
    # (50), routing this request to the greedy heuristic instead of exact MIP.
    # The heuristic isn't guaranteed optimal, so only feasibility is checked.
    run_folder, exit_code = _run_cli("large_instance_triggers_heuristic", tmp_path, monkeypatch, capsys)

    # ASSERT
    assert exit_code == 0
    totals = _read_totals(run_folder)
    assert totals["cost"] <= 20
    assert totals["weight"] <= 3.0
    assert totals["calories"] > 0
    # The heuristic path never builds a HiGHS model, so no LP dump exists.
    assert not (run_folder / "model.lp").exists()


@pytest.mark.integration
def test__cli_main__given_individually_infeasible_products__filters_them_and_solves_with_the_rest(
    tmp_path, monkeypatch, capsys
):
    # ARRANGE / ACT — luxury_item (too expensive) and heavy_item (too heavy)
    # are filtered out by preprocessing on their own, before the solver ever
    # sees them; only affordable_snack remains to build the recommendation.
    run_folder, exit_code = _run_cli("individually_infeasible_product_filtered", tmp_path, monkeypatch, capsys)

    # ASSERT
    assert exit_code == 0
    assert _read_totals(run_folder)["calories"] == 120
    _assert_model_lp_matches_golden("individually_infeasible_product_filtered", run_folder)


@pytest.mark.integration
def test__cli_main__given_quantity_greater_than_one__selects_multiple_units_of_same_product(
    tmp_path, monkeypatch, capsys
):
    # ARRANGE / ACT — a single cheap, light product means the optimum buys
    # 10 units of it, confirming the model isn't restricted to 0/1 per product.
    run_folder, exit_code = _run_cli("quantity_greater_than_one", tmp_path, monkeypatch, capsys)

    # ASSERT
    assert exit_code == 0
    totals = _read_totals(run_folder)
    assert totals["quantity"] == 10
    assert totals["calories"] == 500
    _assert_model_lp_matches_golden("quantity_greater_than_one", run_folder)


@pytest.mark.integration
def test__cli_main__given_both_constraints_binding__saturates_budget_and_weight_together(tmp_path, monkeypatch, capsys):
    # ARRANGE / ACT — 4 x_item + 1 y_item exactly exhausts both the budget
    # and the weight limit at the same time, unlike the other feasible cases
    # where only one constraint binds.
    run_folder, exit_code = _run_cli("both_constraints_binding", tmp_path, monkeypatch, capsys)

    # ASSERT
    assert exit_code == 0
    totals = _read_totals(run_folder)
    assert totals["cost"] == 9
    assert totals["weight"] == 6
    assert totals["calories"] == 145
    _assert_model_lp_matches_golden("both_constraints_binding", run_folder)
